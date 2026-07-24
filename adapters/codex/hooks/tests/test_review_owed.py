"""Tests for hooks/review-owed.py - the review-owed Stop gate.

Contract: mark-code-change.py arms /tmp/.codex-changed-review-<sid> on
every real project edit (its mtime tracks the last edit). At Stop, the debt is
settled iff a findings-<lens>.md under a .forge run dir postdates that marker -
the mechanism- and session_id-agnostic evidence a wave ran after the change.
An armed marker with no fresh findings means the change was never reviewed:
block once per debt - the cap keeps both markers so a later wave can still
settle it; further Stops on the same unsettled debt stay silent, and the
settle check runs ahead of the stop_hook_active short-circuit so findings
written inside a blocked continuation refund the retry at that same Stop.
Settling clears both markers, re-arming the gate for the next unreviewed
change. An unsettled stop_hook_active short-circuit keeps both markers too -
clearing the retry there was half of the old re-fire bug. Degenerate case:
while a debt sits unsettled, later changes fold into it silently - if no
review ever runs, per-debt degrades to per-session, by design. Always exit 0;
every non-block branch prints nothing.
"""

import json
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

REVIEW_OWED_PY = Path(__file__).resolve().parents[1] / "review-owed.py"


def _review_marker(session_id):
    return Path(f"/tmp/.codex-changed-review-{session_id}")


def _retry_marker(session_id):
    return Path(f"/tmp/.codex-review-owed-{session_id}")


def _run_hook(payload, *, raw_stdin=None):
    stdin_text = raw_stdin if raw_stdin is not None else json.dumps(payload)
    return subprocess.run(
        ["python3", str(REVIEW_OWED_PY)],
        input=stdin_text,
        capture_output=True,
        text=True,
    )


def _cleanup(*paths):
    for p in paths:
        p.unlink(missing_ok=True)


def test_armed_marker_blocks_with_review_pointer():
    session_id = str(uuid.uuid4())
    review, retry = _review_marker(session_id), _retry_marker(session_id)
    cwd = tempfile.mkdtemp()  # isolated: no .forge, so no findings can settle
    try:
        review.write_text("1")
        result = _run_hook(
            {"session_id": session_id, "cwd": cwd, "stop_hook_active": False}
        )
        assert result.returncode == 0, f"got {result.returncode}: {result.stderr!r}"
        parsed = json.loads(result.stdout)
        assert parsed.get("decision") == "block", f"got {result.stdout!r}"
        assert "crossfire" in parsed.get("reason", ""), (
            f"the block reason must point at the review wave; got {parsed!r}"
        )
        assert review.exists(), "a block must leave the review debt armed"
        assert retry.exists(), "a block must burn the single retry"
    finally:
        shutil.rmtree(cwd, ignore_errors=True)
        _cleanup(review, retry)


def test_fresh_findings_settle_the_debt():
    """A findings file newer than the marker (a wave ran after the change)
    clears the debt at Stop - no matter how or by whom it was written."""
    session_id = str(uuid.uuid4())
    review, retry = _review_marker(session_id), _retry_marker(session_id)
    cwd = tempfile.mkdtemp()
    try:
        review.write_text("1")
        run_dir = Path(cwd) / ".forge" / "run"
        run_dir.mkdir(parents=True)
        findings = run_dir / "findings-correctness.md"
        findings.write_text("pass")
        marker_mtime = review.stat().st_mtime
        os.utime(findings, (marker_mtime + 10, marker_mtime + 10))
        result = _run_hook(
            {"session_id": session_id, "cwd": cwd, "stop_hook_active": False}
        )
        assert result.returncode == 0, f"got {result.returncode}: {result.stderr!r}"
        assert result.stdout.strip() == "", (
            f"fresh findings must settle the debt silently; got {result.stdout!r}"
        )
        assert not review.exists(), "settling must clear the review marker"
        assert not retry.exists(), "settling must clear the retry marker"
    finally:
        shutil.rmtree(cwd, ignore_errors=True)
        _cleanup(review, retry)


def test_stale_findings_do_not_settle_the_debt():
    """Findings older than the marker (code changed again after the wave) must
    NOT settle - the block must fire. This is the review-then-edit-again case."""
    session_id = str(uuid.uuid4())
    review, retry = _review_marker(session_id), _retry_marker(session_id)
    cwd = tempfile.mkdtemp()
    try:
        run_dir = Path(cwd) / ".forge" / "run"
        run_dir.mkdir(parents=True)
        findings = run_dir / "findings-correctness.md"
        findings.write_text("pass")
        review.write_text("1")
        findings_mtime = findings.stat().st_mtime
        os.utime(review, (findings_mtime + 10, findings_mtime + 10))
        result = _run_hook(
            {"session_id": session_id, "cwd": cwd, "stop_hook_active": False}
        )
        assert result.returncode == 0, f"got {result.returncode}: {result.stderr!r}"
        parsed = json.loads(result.stdout)
        assert parsed.get("decision") == "block", (
            f"findings older than the last change must not settle the debt; got {parsed!r}"
        )
        assert review.exists(), "a block must leave the review debt armed"
        assert retry.exists(), "a block must burn the single retry"
    finally:
        shutil.rmtree(cwd, ignore_errors=True)
        _cleanup(review, retry)


def test_unreadable_findings_file_does_not_crash_or_settle():
    """A findings entry whose stat() raises (here a dangling symlink) is skipped,
    not fatal: the hook stays fail-toward-block rather than crashing."""
    session_id = str(uuid.uuid4())
    review, retry = _review_marker(session_id), _retry_marker(session_id)
    cwd = tempfile.mkdtemp()
    try:
        review.write_text("1")
        run_dir = Path(cwd) / ".forge" / "run"
        run_dir.mkdir(parents=True)
        (run_dir / "findings-correctness.md").symlink_to(Path(cwd) / "gone.md")
        result = _run_hook(
            {"session_id": session_id, "cwd": cwd, "stop_hook_active": False}
        )
        assert result.returncode == 0, f"got {result.returncode}: {result.stderr!r}"
        parsed = json.loads(result.stdout)
        assert parsed.get("decision") == "block", (
            f"an unreadable findings file must not settle the debt; got {parsed!r}"
        )
    finally:
        shutil.rmtree(cwd, ignore_errors=True)
        _cleanup(review, retry)


def test_no_marker_is_silent_pass():
    session_id = str(uuid.uuid4())
    result = _run_hook({"session_id": session_id, "stop_hook_active": False})
    assert result.returncode == 0, f"got {result.returncode}: {result.stderr!r}"
    assert result.stdout.strip() == "", f"got {result.stdout!r}"
    assert not _retry_marker(session_id).exists()


def test_second_stop_on_same_debt_stays_silent_and_keeps_both_markers():
    """The cap: a second Stop on the same unsettled debt stays silent but
    keeps both markers, so the debt stays settleable by a later review wave
    instead of being silently forgiven (fail-toward-block survives the cap)."""
    session_id = str(uuid.uuid4())
    review, retry = _review_marker(session_id), _retry_marker(session_id)
    cwd = tempfile.mkdtemp()  # isolated: the cap must not depend on findings
    try:
        review.write_text("1")
        retry.write_text("1")
        result = _run_hook(
            {"session_id": session_id, "cwd": cwd, "stop_hook_active": False}
        )
        assert result.returncode == 0, f"got {result.returncode}: {result.stderr!r}"
        assert result.stdout.strip() == "", f"got {result.stdout!r}"
        assert retry.exists(), (
            "the cap must keep the retry marker - clearing it here let the "
            "next edit re-arm the gate with a fresh retry (half of the "
            "re-fire bug)"
        )
        assert review.exists(), (
            "the cap must keep the review debt armed until a review actually "
            "settles it, not clear it just because the cap was hit"
        )
    finally:
        shutil.rmtree(cwd, ignore_errors=True)
        _cleanup(review, retry)


def test_stop_hook_active_short_circuits_and_keeps_review_marker():
    """An unsettled stop_hook_active Stop must keep BOTH markers - clearing
    the retry here (the old behavior) was the other half of the re-fire bug:
    it let the very next Stop treat the debt as fresh and re-block."""
    session_id = str(uuid.uuid4())
    review, retry = _review_marker(session_id), _retry_marker(session_id)
    cwd = tempfile.mkdtemp()  # isolated: no findings, so the settle check stays inert
    try:
        review.write_text("1")
        retry.write_text("1")
        result = _run_hook(
            {"session_id": session_id, "cwd": cwd, "stop_hook_active": True}
        )
        assert result.returncode == 0, f"got {result.returncode}: {result.stderr!r}"
        assert result.stdout.strip() == "", f"got {result.stdout!r}"
        assert review.exists(), (
            "the stop_hook_active short-circuit must keep the review debt "
            "armed for the next turn"
        )
        assert retry.exists(), (
            "the short-circuit must keep the retry marker too when nothing "
            "settled the debt"
        )
    finally:
        shutil.rmtree(cwd, ignore_errors=True)
        _cleanup(review, retry)


def test_block_then_edit_then_stop_stays_silent():
    """The observed triple-fire, acceptance 4: block once per debt, not once
    per edit. block -> edit -> stop must stay silent; a further edit -> stop
    on the SAME still-unreviewed debt must also stay silent, not re-block -
    this is exactly the loop that fired three times in one session."""
    session_id = str(uuid.uuid4())
    review, retry = _review_marker(session_id), _retry_marker(session_id)
    cwd = tempfile.mkdtemp()  # isolated: no .forge, so no findings can settle
    try:
        review.write_text("1")
        first = _run_hook(
            {"session_id": session_id, "cwd": cwd, "stop_hook_active": False}
        )
        assert first.returncode == 0, f"got {first.returncode}: {first.stderr!r}"
        first_parsed = json.loads(first.stdout)
        assert first_parsed.get("decision") == "block", f"got {first.stdout!r}"

        # mark-code-change.py rewrites the review marker on every edit - a
        # fresh mtime is the faithful simulation of "the agent edited again".
        review.write_text("1")

        second = _run_hook(
            {"session_id": session_id, "cwd": cwd, "stop_hook_active": False}
        )
        assert second.returncode == 0, f"got {second.returncode}: {second.stderr!r}"
        assert second.stdout.strip() == "", (
            f"a second Stop on the same unsettled debt must stay silent, "
            f"not re-block; got {second.stdout!r}"
        )

        # A further edit on the still-unreviewed debt must not re-arm the
        # gate either - this third Stop is what the old per-edit-burst cap
        # got wrong (it cleared both markers at the cap, so this edit looked
        # like a fresh, never-blocked debt and re-blocked).
        review.write_text("1")

        third = _run_hook(
            {"session_id": session_id, "cwd": cwd, "stop_hook_active": False}
        )
        assert third.returncode == 0, f"got {third.returncode}: {third.stderr!r}"
        assert third.stdout.strip() == "", (
            f"a third Stop on the same unsettled debt must also stay silent - "
            f"per-debt, not per-edit; got {third.stdout!r}"
        )
    finally:
        shutil.rmtree(cwd, ignore_errors=True)
        _cleanup(review, retry)


def test_settling_after_a_block_re_arms_the_gate():
    """The gate recovers, acceptance 5: after a review settles a blocked
    debt, a later unreviewed change must earn a fresh block - a quieter gate
    must not become a blinder one."""
    session_id = str(uuid.uuid4())
    review, retry = _review_marker(session_id), _retry_marker(session_id)
    cwd = tempfile.mkdtemp()
    try:
        review.write_text("1")
        retry.write_text("1")
        run_dir = Path(cwd) / ".forge" / "run"
        run_dir.mkdir(parents=True)
        findings = run_dir / "findings-correctness.md"
        findings.write_text("pass")
        marker_mtime = review.stat().st_mtime
        os.utime(findings, (marker_mtime + 10, marker_mtime + 10))

        settle = _run_hook(
            {"session_id": session_id, "cwd": cwd, "stop_hook_active": False}
        )
        assert settle.returncode == 0, f"got {settle.returncode}: {settle.stderr!r}"
        assert settle.stdout.strip() == "", (
            f"a review that postdates the block must settle silently; "
            f"got {settle.stdout!r}"
        )
        assert not review.exists(), "settling must clear the review marker"
        assert not retry.exists(), "settling must clear the retry marker"

        # A later, unreviewed change re-arms the debt.
        findings_mtime = findings.stat().st_mtime
        review.write_text("1")
        os.utime(review, (findings_mtime + 10, findings_mtime + 10))

        second = _run_hook(
            {"session_id": session_id, "cwd": cwd, "stop_hook_active": False}
        )
        assert second.returncode == 0, f"got {second.returncode}: {second.stderr!r}"
        second_parsed = json.loads(second.stdout)
        assert second_parsed.get("decision") == "block", (
            f"a later unreviewed change must earn a fresh block after "
            f"settling, not stay silenced by the earlier debt; "
            f"got {second.stdout!r}"
        )
        assert retry.exists(), "the fresh block must write a new retry marker"
    finally:
        shutil.rmtree(cwd, ignore_errors=True)
        _cleanup(review, retry)


def test_settle_during_blocked_continuation_refunds_the_retry():
    """The blocker's regression, the live shape of acceptance 5: findings
    written inside the blocked continuation's own Stop (stop_hook_active=True,
    the payload shape the real blocked-then-reviewed turn produces) must still
    settle the debt at that same Stop - silent, both markers cleared - instead
    of the settle check being skipped by the short-circuit."""
    session_id = str(uuid.uuid4())
    review, retry = _review_marker(session_id), _retry_marker(session_id)
    cwd = tempfile.mkdtemp()
    try:
        review.write_text("1")
        retry.write_text("1")
        run_dir = Path(cwd) / ".forge" / "run"
        run_dir.mkdir(parents=True)
        findings = run_dir / "findings-correctness.md"
        findings.write_text("pass")
        marker_mtime = review.stat().st_mtime
        os.utime(findings, (marker_mtime + 10, marker_mtime + 10))

        result = _run_hook(
            {"session_id": session_id, "cwd": cwd, "stop_hook_active": True}
        )
        assert result.returncode == 0, f"got {result.returncode}: {result.stderr!r}"
        assert result.stdout.strip() == "", (
            f"findings settling inside the blocked continuation must stay "
            f"silent; got {result.stdout!r}"
        )
        assert not review.exists(), (
            "the settle check must run ahead of the stop_hook_active "
            "short-circuit so the blocked continuation's own Stop refunds "
            "the debt instead of leaving it armed"
        )
        assert not retry.exists(), (
            "the settle check must clear the retry marker even on a "
            "stop_hook_active Stop - this is the refund the blocked flow "
            "depends on"
        )
    finally:
        shutil.rmtree(cwd, ignore_errors=True)
        _cleanup(review, retry)


def test_unparseable_stdin_is_silent_pass():
    for raw in ("{not valid json", ""):
        result = _run_hook(None, raw_stdin=raw)
        assert result.returncode == 0, (
            f"raw={raw!r}: got {result.returncode}; stderr={result.stderr!r}"
        )
        assert result.stdout.strip() == "", f"raw={raw!r}: got {result.stdout!r}"
