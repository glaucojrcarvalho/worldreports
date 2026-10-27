"""Protect nine unavailable Moldova canonical spine slots from unsafe fill."""
from pathlib import Path

import pytest
from countries.moldova.research.audit_semantic_readiness import (
    COUNTRY, PENDING, ABSENT_OPTIONAL_LENSES, inventory,
)

PLATES = (COUNTRY / "plates.py").read_text(encoding="utf-8")


def test_atlas_canonical_pending_and_lens_inventory():
    result = inventory(PLATES)
    assert result["counts"] == {
        "claimed":45, "canonical":42, "observed":36,
        "pending":9, "optional_unclaimed_lenses":3}
    assert set(result["pending_canonical"]) == PENDING
    assert set(result["unclaimed_optional_lenses"]) == ABSENT_OPTIONAL_LENSES
    assert result["topics"]["migration"]["migration.foreign_born"]["status"] == "pending"
    assert result["topics"]["migration"]["migration.lens"]["status"] == "observed"
    assert result["topics"]["credit"]["credit.npl"]["status"] == "observed"


def test_no_unsupported_fill_into_unavailable_household_debt():
    changed = PLATES.replace(
        '_pending(ctx, ig, ax, "Borrower-defined household credit stock',
        'ctx.line(ax, [2025], [5], ctx.p.BLUE)\n    _pending(ctx, ig, ax, "Borrower-defined household credit stock',
        1)
    assert changed != PLATES
    with pytest.raises(AssertionError, match="ambiguous"):
        inventory(changed)


def test_no_missing_canonical_slot_or_unreviewed_pending_conversion():
    original = '    ax = ig.slot("markets.bond_10y", "10-year government bond yield (%)")'
    changed = PLATES.replace(original, '    # missing 10-year yield')
    assert changed != PLATES
    with pytest.raises(AssertionError, match="Canonical slots missing"):
        inventory(changed)

    changed = PLATES.replace(
        '_pending(ctx, ig, ax, "No verified annual-average 10-year secondary',
        'ctx.line(ax, [2025], [4], ctx.p.RED) # No verified annual-average 10-year secondary',
        1)
    assert changed != PLATES
    with pytest.raises(AssertionError, match="Unexpected pending/filled"):
        inventory(changed)


def test_pending_reason_cannot_be_empty():
    original = '"No verified annual-average 10-year secondary\\n"'
    changed = PLATES.replace(original, '"not audited"')
    assert changed != PLATES
    with pytest.raises(AssertionError, match="lacks a reason"):
        inventory(changed)
