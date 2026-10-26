"""Smoke-test the source-preserving, noncanonical Moldova fiscal preview."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "countries/moldova/research/render_fiscal_preview.py"
spec = importlib.util.spec_from_file_location("moldova_fiscal_preview", SCRIPT)
assert spec is not None and spec.loader is not None
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


def test_preview_reads_only_verified_national_budget_rows() -> None:
    rows = preview.data()
    assert [row["year"] for row in rows] == list(range(2016, 2026))
    assert rows[-2]["expenditure_mdl_mn"] == 122962.7
    assert rows[-1]["expenditure_mdl_mn"] == 139856.4
    assert len(preview.FUNCTIONS) == 10
    assert rows[-1]["social_protection_mdl_mn"] == 54056.0


def test_preview_renders_image_without_modifying_curated_input(tmp_path: Path) -> None:
    before = preview.CSV.read_bytes()
    output = tmp_path / "moldova-research-preview.png"
    assert preview.render(output) == output
    assert output.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert output.stat().st_size > 10_000
    assert preview.CSV.read_bytes() == before
