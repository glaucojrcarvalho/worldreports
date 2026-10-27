"""Prevent the Moldova research archive from rerendering untested figures.

The runner that executes complete Python/JS, provenance, localization and
layout gates must be the only producer of the saved research outputs. A
separate archive job may only restore its same-run artifact, re-audit it,
and commit to the fork research branch; there is no production deployment.
"""
from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/moldova-research.yml"


def test_archiver_consumes_exact_successful_validation_artifact() -> None:
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    jobs = workflow["jobs"]
    validation = jobs["moldova-research"]
    archival = jobs["archive-validated-research-assets"]
    assert archival["needs"] == "moldova-research"
    assert "github.repository == 'glaucojrcarvalho/worldreports'" in archival["if"]
    assert "refs/heads/research/moldova-source-audit" in archival["if"]
    assert "github.event_name == 'push'" in archival["if"]
    steps = validation["steps"]
    gate = next(i for i, s in enumerate(steps)
                if s.get("name", "").startswith("Exercise full atlas and browser JS"))
    producer = next(i for i, s in enumerate(steps)
                    if s.get("name", "").startswith("Upload exact full-suite-validated"))
    assert gate < producer
    assert "node --test tests/js/*.test.js" in steps[gate]["run"]
    artifact = steps[producer]
    assert artifact["uses"] == "actions/upload-artifact@v4"
    assert artifact["with"]["name"] == "moldova-validated-assets"
    assert artifact["with"]["if-no-files-found"] == "error"
    assert "countries/moldova/provenance.json" in artifact["with"]["path"]
    assert "countries/moldova/output/" in artifact["with"]["path"]

    archive_steps = archival["steps"]
    consumer = next(i for i, s in enumerate(archive_steps)
                    if s.get("name", "").startswith("Download validated"))
    checked = next(i for i, s in enumerate(archive_steps)
                   if s.get("name", "").startswith("Restore ONLY the exact fully tested"))
    commit = next(i for i, s in enumerate(archive_steps)
                  if s.get("name", "").startswith("Commit only isolated"))
    assert consumer < checked < commit
    assert archive_steps[consumer]["uses"] == "actions/download-artifact@v4"
    assert archive_steps[consumer]["with"]["name"] == artifact["with"]["name"]
    audit_script = "countries/moldova/research/audit_candidate_assets.py"
    assert audit_script in archive_steps[checked]["run"]
    assert "len(files) == 108" in archive_steps[checked]["run"]
    assert "hashlib.sha256" in archive_steps[checked]["run"]
    assert "test ! -e countries/moldova/country.yaml" in archive_steps[checked]["run"]
    for step in archive_steps:
        command = step.get("run", "")
        assert "python -m core.render" not in command
        assert "python -m core.thumbs" not in command
        assert "python -m core.provenance" not in command
        assert "force-with-lease" not in command
    assert "git push origin HEAD:refs/heads/research/moldova-source-audit" in (
        archive_steps[commit]["run"]
    )


def test_full_atlas_runner_finishes_and_image_only_archive_does_not_retrigger():
    """Hourly commits must not repeatedly cancel the 30-minute global suite."""
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    group = workflow["concurrency"]
    assert group["group"] == "moldova-research-${{ github.ref }}"
    assert group["cancel-in-progress"] is False
    # PyYAML 1.1 reads YAML's 'on' key as the boolean True.
    events = workflow.get("on", workflow.get(True))
    assert events is not None
    push = events["push"]
    assert push["branches"] == ["research/moldova-source-audit"]
    assert set(push["paths-ignore"]) == {
        "countries/moldova/output/**",
        "countries/moldova/provenance.json",
    }
    assert "workflow_dispatch" in events
    jobs = workflow["jobs"]
    assert 40 <= jobs["moldova-research"]["timeout-minutes"] <= 90
    assert jobs["archive-validated-research-assets"]["timeout-minutes"] <= 30
    archive = jobs["archive-validated-research-assets"]
    assert archive["needs"] == "moldova-research"
    assert "github.event_name == 'push'" in archive["if"]
    assert "git push origin HEAD:refs/heads/research/moldova-source-audit" in (
        next(step["run"] for step in archive["steps"]
             if step.get("name", "").startswith("Commit only isolated"))
    )

def test_archive_rejected_push_fails_closed_instead_of_reporting_success():
    """The former archive returned zero even when its push was refused."""
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    job = workflow["jobs"]["archive-validated-research-assets"]
    write_step = next(step for step in job["steps"]
                      if step.get("name", "").startswith("Commit only isolated"))
    commands = write_step["run"]
    assert "git push origin HEAD:refs/heads/research/moldova-source-audit" in commands
    assert "if ! git push" not in commands
    assert "Skipped the stale image push" not in commands
    assert "force" not in commands
    assert "git diff --cached --quiet" in commands  # no-op if same bytes
