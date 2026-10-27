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
                if s["name"].startswith("Exercise full atlas and browser JS"))
    producer = next(i for i, s in enumerate(steps)
                    if s["name"].startswith("Upload exact full-suite-validated"))
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
                    if s["name"].startswith("Download validated"))
    checked = next(i for i, s in enumerate(archive_steps)
                   if s["name"].startswith("Restore ONLY the exact fully tested"))
    commit = next(i for i, s in enumerate(archive_steps)
                  if s["name"].startswith("Commit only isolated"))
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
