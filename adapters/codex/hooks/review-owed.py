#!/usr/bin/env python3
"""Stop gate: code changed this session, so a review wave is owed (codex port).

The one duty of the old deterministic router that no prose flow can replace:
knowing the session isn't done. mark-code-change.py arms the review marker on
every real project edit; the debt is settled here, at Stop, when a lens
findings file (`findings-<lens>.md` in a `.forge/` run dir) postdates that last
edit - both the forge review wave and standalone crossfire write those.

Settling is checked here, not at write time, on purpose. The findings files are
written by review *subagents*, usually via the shell tool and always under a
subagent session_id - so a PostToolUse clearer neither fires nor rendezvous
with the main session's marker. This Stop gate runs under the main session_id
and reads the files off disk, so it is agnostic to both how the findings were
written and by whom. The mtime comparison (findings newer than the marker) is
what keeps "review then edit again" honest: stale findings from before the
last change do not settle.

If no findings postdate the change, it was never reviewed: block once per debt
and say so. No command runs here - the block message IS the enforcement. After
a block, further Stops on the same unsettled debt stay silent; the spent retry
marker holds until a review settles the debt, and settling clears both markers
so the next unreviewed change earns a fresh block. The settle check runs even
when stop_hook_active is set, so findings from the blocked continuation settle
at that same Stop (RISK-5: codex may never send it; the retry cap is the
structural loop-breaker either way). While a debt sits unsettled, later changes
fold into it silently - if no review ever runs, per-debt degrades to
per-session, by design.

Stdlib only. Always exits 0 (a block is a decision, not a hook error). The
block is a single {"decision":"block"} JSON object on stdout - codex's
documented Stop block channel; every pass/skip branch prints nothing.
"""

import json
import sys
from pathlib import Path

from verify_shared import (
    REVIEW_CHANGE_PREFIX,
    read_marker_count,
    session_marker,
    silent_pass,
)

RETRY_PREFIX = "codex-review-owed"

BLOCK_REASON = (
    "Code changed this session but no review ran over it. Fire the review wave "
    "- crossfire over the change, or finish the forge run's review stage - "
    "before completing. If a review truly does not apply, tell the user why "
    "instead of stopping silently."
)


def review_ran_since(review_marker, cwd):
    """True when a lens findings file postdates the last code change.

    The review marker's mtime is the time of the last armed edit (mark-code-
    change.py rewrites it on every project edit). A `findings-<lens>.md` under a
    `.forge/` run dir with a newer mtime is the deterministic "a wave ran after
    the change" signal - written by the forge wave or standalone crossfire,
    regardless of tool or session_id.

    Scoping is by mtime ordering alone: the scan sweeps the whole `.forge/` tree
    (gitignored, so a branch checkout never resets these mtimes) and any findings
    newer than the marker counts. Honest for the normal case (a wave spans
    seconds after the edit) and for review-then-edit-again (a later edit re-arms
    the marker past the old findings). The one gap left open: an edit made *while
    a prior wave is still running* can be settled by that wave's just-later
    findings - acceptable, as it needs an interleaved edit-during-review and only
    skips one extra wave.

    Every failure path declines to settle so the gate stays fail-toward-block:
    a bad marker, a missing `.forge/`, or any error walking the tree or stat-ing
    a findings file (unreadable subdir, symlink loop, dangling link) all return
    False - block and ask for re-review rather than settle on shaky evidence.
    """
    try:
        # Stat before walk: a missing marker raises OSError right here, so the
        # chat-only fast path never touches .forge - this ordering IS the
        # guard; callers need no exists() check of their own.
        marker_mtime = review_marker.stat().st_mtime
        forge = (Path(cwd) if cwd else Path.cwd()) / ".forge"
        if not forge.is_dir():
            return False
        for findings in forge.rglob("findings-*.md"):
            if findings.stat().st_mtime > marker_mtime:
                return True
    except OSError:
        return False
    return False


def main():
    # Fail-open bias: unparseable payload -> let the agent finish.
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    sid = payload.get("session_id") or ""
    cwd = payload.get("cwd") or ""
    stop_hook_active = payload.get("stop_hook_active")

    retry_marker = session_marker(RETRY_PREFIX, sid)
    review_marker = session_marker(REVIEW_CHANGE_PREFIX, sid)

    # Settle first, even on a blocked continuation's Stop - findings written
    # inside that continuation refund the retry right here. The .forge walk
    # deliberately runs ahead of the stop_hook_active short-circuit: checking
    # after it made this branch unreachable exactly when the gate had just
    # demanded the wave. Keep this ordering - hoisting the short-circuit back
    # above it reintroduces that blind spot.
    if review_ran_since(review_marker, cwd):
        silent_pass(retry_marker, review_marker)

    # Unsettled blocked loop: stand down for this turn; both markers stay put
    # so the debt and its spent retry survive to the next real Stop. (Clearing
    # the retry here was one half of the re-fire bug.)
    if stop_hook_active is True or stop_hook_active == "true":
        sys.exit(0)

    if not review_marker.exists():
        sys.exit(0)

    # Already blocked for this debt - stay silent, keep both markers; the debt
    # stays settleable by a later wave, and only settling re-arms the gate.
    # (Clearing both here was the other half of the re-fire bug: the next edit
    # re-armed the change marker with the retry reset to zero.)
    if read_marker_count(retry_marker) >= 1:
        sys.exit(0)

    retry_marker.write_text("1")
    print(json.dumps({"decision": "block", "reason": BLOCK_REASON}))
    sys.exit(0)


if __name__ == "__main__":
    main()
