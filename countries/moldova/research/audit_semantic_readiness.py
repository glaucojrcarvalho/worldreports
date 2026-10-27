"""Static Moldova release-inventory gate against the executable common spine.

Classifies real rendered canonical slots as observed or explicitly pending.
An absent optional lens is not a gap; missing canonical slots and
unsupported synthetic fills are release blockers. Does not download data,
modify the registry, render graphics or publish.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

from core import spine

COUNTRY = Path(__file__).resolve().parents[1]
TOPICS = (
    "economy", "fiscal", "spending", "trade", "markets", "credit",
    "people", "world", "demography", "security", "mortality", "migration",
)
PENDING = frozenset({
    "spending.public_investment", "markets.bond_10y", "markets.equities",
    "credit.household_debt", "credit.lending_rate",
    "mortality.excess_deaths", "mortality.covid",
    "migration.flows", "migration.foreign_born",
})
ABSENT_OPTIONAL_LENSES = frozenset({
    "trade.lens", "people.lens", "security.lens",
})
DRAW_CALLS = frozenset({
    ("ctx", "line"), ("ctx", "bars"),
    ("ax", "stackplot"), ("ax", "scatter"),
})


def _call(node: ast.AST) -> tuple[str, str] | None:
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)):
        return node.func.value.id, node.func.attr
    return None


def inventory(code: str) -> dict:
    parsed = ast.parse(code, filename="countries/moldova/plates.py")
    found = {}
    for node in parsed.body:
        if not isinstance(node, ast.FunctionDef) or not node.name.startswith("plate_"):
            continue
        topic = node.name.removeprefix("plate_")
        if topic not in TOPICS:
            continue
        boundaries = []
        for index, statement in enumerate(node.body):
            if not isinstance(statement, ast.Assign):
                continue
            slot = statement.value
            if _call(slot) != ("ig", "slot"):
                continue
            if (len(statement.targets) != 1 or
                    not isinstance(statement.targets[0], ast.Name) or
                    statement.targets[0].id != "ax" or
                    not slot.args or not isinstance(slot.args[0], ast.Constant)
                    or not isinstance(slot.args[0].value, str)):
                raise AssertionError(f"{topic}: dynamic/unattributed slot")
            boundaries.append((index, slot.args[0].value))
        slots = {}
        for i, (start, key) in enumerate(boundaries):
            if key in slots or not key.startswith(topic + "."):
                raise AssertionError(f"{topic}: duplicate/foreign slot {key}")
            end = boundaries[i + 1][0] if i + 1 < len(boundaries) else len(node.body)
            calls = [call for statement in node.body[start:end]
                     for call in ast.walk(statement) if isinstance(call, ast.Call)]
            pending = [c for c in calls if isinstance(c.func, ast.Name)
                       and c.func.id == "_pending"]
            drawn = any(_call(c) in DRAW_CALLS for c in calls)
            if len(pending) > 1 or (pending and drawn) or (not pending and not drawn):
                raise AssertionError(
                    f"{key}: ambiguous missing/observed state "
                    f"(pending={len(pending)}, drawn={drawn})")
            explanation = None
            if pending:
                pieces = [arg.value for arg in pending[0].args[3:]
                          if isinstance(arg, ast.Constant) and isinstance(arg.value, str)]
                explanation = " ".join(pieces).strip()
                if len(explanation) < 28:
                    raise AssertionError(f"{key}: pending slot lacks a reason")
            slots[key] = {
                "kind": spine.SLOTS[key].kind,
                "status": "pending" if pending else "observed",
                "pending_reason": explanation,
            }
        found[topic] = slots
    if set(found) != set(TOPICS):
        raise AssertionError(f"Missing topic builder: {set(TOPICS)-set(found)}")

    expected = {key for topic in TOPICS for key in
                (s.key for s in spine.SPINE[topic]) if s.canonical}
    actual = set().union(*(set(group) for group in found.values()))
    if not expected <= actual:
        raise AssertionError(f"Canonical slots missing: {sorted(expected-actual)}")
    known = {s.key for topic in TOPICS for s in spine.SPINE[topic]}
    if not actual <= known:
        raise AssertionError(f"Unknown spine slot(s): {sorted(actual-known)}")
    omitted = known - actual
    if omitted != ABSENT_OPTIONAL_LENSES:
        raise AssertionError(f"Unexpected omitted lens slot(s): {sorted(omitted)}")
    observed_pending = {
        k for slots in found.values() for k, value in slots.items()
        if value["status"] == "pending"}
    if observed_pending != PENDING:
        raise AssertionError(
            "Unexpected pending/filled canonical slots; source-review required: "
            f"{sorted(observed_pending ^ PENDING)}")
    if any(not spine.SLOTS[k].canonical for k in observed_pending):
        raise AssertionError("Lenses must not be mistaken for canonical gaps")
    counts = {"claimed": len(actual), "canonical": len(expected),
              "observed": len(actual) - len(observed_pending),
              "pending": len(observed_pending),
              "optional_unclaimed_lenses": len(omitted)}
    if counts != {"claimed":45,"canonical":42,"observed":36,
                  "pending":9,"optional_unclaimed_lenses":3}:
        raise AssertionError(f"Unexpected release inventory totals: {counts}")
    return {
        "release_status": "research_only_pending_canonical_indicators",
        "counts": counts,
        "pending_canonical": sorted(PENDING),
        "unclaimed_optional_lenses": sorted(omitted),
        "topics": {topic: found[topic] for topic in TOPICS},
    }


def main() -> None:
    report = inventory((COUNTRY / "plates.py").read_text(encoding="utf-8"))
    path = Path("/tmp/moldova-semantic-readiness.json")
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n",
                    encoding="utf-8")
    print("Moldova semantic-readiness PASS:", report["counts"])
    print("Release remains blocked on independently sourced canonical gaps")


if __name__ == "__main__":
    main()
