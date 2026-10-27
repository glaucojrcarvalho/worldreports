"""No stale Moldova image archives after source, locale or code edits."""
from pathlib import Path
import subprocess
import sys

import pytest
from countries.moldova.research.archive_branch_guard import SAFE, validate


NOTE = "countries/moldova/research/PHASE_B_HANDOFF.md"
ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "countries/moldova/research/archive_branch_guard.py"


def test_only_explicit_research_handoff_is_allowed():
    assert SAFE == {NOTE}
    validate([])
    validate([NOTE])


@pytest.mark.parametrize("path", [
    "countries/moldova/plates.py",
    "countries/moldova/SOURCES.yaml",
    "countries/moldova/i18n.json",
    "countries/moldova/research/country_candidate.yaml",
    "countries/moldova/data/macro/national_lfs.csv",
    "countries/moldova/output/01-economy.png",
    "countries/moldova/provenance.json",
    "countries/moldova/research/visual_review.py",
    "core/spine.py",
    ".github/workflows/moldova-research.yml",
    "countries/france/plates.py",
    "countries/moldova/DATA_NOTES.md",
    NOTE + "/fake", "../escape", "/tmp/outside",
])
def test_refuse_all_actual_data_or_render_input_changes(path):
    with pytest.raises(ValueError):
        validate([path])


def test_mixed_safe_and_unsafe_changes_fail():
    with pytest.raises(ValueError, match="national_lfs.csv"):
        validate([NOTE, "countries/moldova/data/macro/national_lfs.csv"])


def test_cli_returns_failure_for_actual_source_diff():
    a = subprocess.run([sys.executable, str(SCRIPT)], input=NOTE + "\n",
                       text=True, capture_output=True)
    b = subprocess.run([sys.executable, str(SCRIPT)],
                       input=NOTE + "\ncountries/moldova/plates.py\n",
                       text=True, capture_output=True)
    assert a.returncode == 0
    assert b.returncode == 1


def test_archive_workflow_gates_ancestor_paths_and_nonforced_push():
    import yaml
    spec = yaml.safe_load((ROOT / ".github/workflows/moldova-research.yml").read_text())
    step = next(s for s in spec["jobs"]["archive-validated-research-assets"]["steps"]
                if s.get("name", "").startswith("Commit only isolated"))
    script = step["run"]
    phrases = ["git fetch origin research/moldova-source-audit",
               'git merge-base --is-ancestor "$GITHUB_SHA" "$newest"',
               "python countries/moldova/research/archive_branch_guard.py",
               'git rebase "$newest"',
               "git push origin HEAD:refs/heads/research/moldova-source-audit"]
    positions = [script.index(p) for p in phrases]
    assert positions == sorted(positions)
    assert "git push --force" not in script and "if ! git push" not in script
