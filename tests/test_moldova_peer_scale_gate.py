"""Global comparison-scale contract for Moldova before country registration.

Regression tests are cheap; the companion workflow performs the expensive
25-country *locale-complete* re-render and uploads human-review contact sheets.
"""
from pathlib import Path

from core.country import Country
from countries.moldova.research.peer_scale_gate import (
    AXES, ROOT, compare_png, peer_plates, verify_axes,
)

def test_shared_range_and_complete_peer_selection():
    verify_axes()
    assert set(AXES) == {"trade.balance", "world.gdp", "world.reserves"}
    assert not (ROOT / "countries/moldova/country.yaml").exists()
    peers = Country.all()
    assert len(peers) >= 25
    assert "moldova" not in {c.slug for c in peers}
    for country in peers:
        selected = peer_plates(country)
        assert {p.topic for p in selected} == {"trade", "world"}
        assert all((country.dir / "output" / p.filename).is_file()
                   for p in selected)

def test_pixel_comparison_is_not_fooled_by_file_metadata(tmp_path: Path):
    from PIL import Image
    a, b = tmp_path / "one.png", tmp_path / "two.png"
    Image.new("RGB", (16, 16), "white").save(a)
    Image.new("RGB", (16, 16), "white").save(b)
    exact = compare_png(a, b)
    assert exact["difference_bbox"] is None
    assert exact["pixel_change_percent"] == 0
    Image.new("RGB", (16, 16), "black").save(b)
    different = compare_png(a, b)
    assert different["difference_bbox"] == [0, 0, 16, 16]
    assert different["pixel_change_percent"] == 100

def test_one_pixel_font_metric_jitter_is_recorded_not_rejected(tmp_path: Path):
    from PIL import Image
    import pytest
    a, b = tmp_path / "base.png", tmp_path / "rebuild.png"
    Image.new("RGB", (32, 20), "white").save(a)
    Image.new("RGB", (32, 21), "white").save(b)
    small = compare_png(a, b)
    assert small["dimension_drift_px"] == [0, 1]
    assert small["difference_bbox"] is None
    Image.new("RGB", (32, 25), "white").save(b)
    with pytest.raises(ValueError, match="Material image dimension drift"):
        compare_png(a, b)
