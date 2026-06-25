"""Tests for hooks/block-git-writes.sh - a PreToolUse(Bash) hook.

CONTRACT:
  - Reads {"tool_name":"Bash","tool_input":{"command":"<cmd>"}} on stdin.
  - ALLOW: exit 0 with NO '"decision":"block"' in stdout.
  - BLOCK: stdout contains a JSON object with '"decision":"block"' (exit 0).
  - A non-Bash tool_name exits 0 immediately (ALLOW).

These 70 cases assert POST-narrowing behavior. Against the current
(over-blocking) script, TC-01..TC-15 (ALLOW/boundary) are expected to FAIL -
that is the correct red state. The implementer makes them green by narrowing
the blocked_verbs regex so that safe git verbs (add, commit, push without
force/delete flags) and non-git commands are permitted.
"""

import json
import subprocess
from pathlib import Path

HOOK_PATH = Path(__file__).resolve().parent.parent / "block-git-writes.sh"


def run_guard(command=None, tool_name="Bash"):
    """Invoke the hook as a subprocess with the given tool_name and command.

    Builds the stdin JSON and returns the captured stdout string.
    For non-Bash tool_names, command may be omitted (None).
    """
    tool_input = {}
    if command is not None:
        tool_input["command"] = command
    payload = json.dumps({"tool_name": tool_name, "tool_input": tool_input})
    result = subprocess.run(
        ["bash", str(HOOK_PATH)],
        input=payload,
        capture_output=True,
        text=True,
    )
    return result.stdout


# ---------------------------------------------------------------------------
# Parametrized cases
# ---------------------------------------------------------------------------
# Each entry: (case_id, tool_name, command_or_None, expected_block_bool)
# expected_block_bool=True  -> '"decision":"block"' must appear in stdout (BLOCK)
# expected_block_bool=False -> '"decision":"block"' must NOT appear in stdout (ALLOW)

CASES = [
    # ALLOW cases (TC-01..TC-09): safe git verbs and non-git commands
    ("TC-01", "Bash", "git add -A", False),
    ("TC-02", "Bash", "git add src/foo.ts", False),
    ("TC-03", "Bash", 'git commit -m "msg"', False),
    ("TC-04", "Bash", "git commit --amend --no-edit", False),
    ("TC-05", "Bash", "git push", False),
    ("TC-06", "Bash", "git push -u origin feat/x", False),
    ("TC-07", "Bash", "git push origin HEAD", False),
    ("TC-08", "Bash", "ls", False),
    ("TC-09", "Bash", "cat README.md", False),
    # ALLOW cases: non-Bash tool_name (TC-10, TC-11) - no command
    ("TC-10", "Read", None, False),
    ("TC-11", "Write", None, False),
    # BOUNDARY: must NOT block (TC-12..TC-15)
    ("TC-12", "Bash", "git push origin local:remote", False),
    ("TC-13", "Bash", "git push origin main:main", False),
    ("TC-14", "Bash", "git push -u origin feat/x --tags", False),
    ("TC-15", "Bash", 'git push origin HEAD -m "fix: bump version to 1.2+3"', False),
    # BLOCK: force/delete push (TC-16..TC-25)
    ("TC-16", "Bash", "git push --force", True),
    ("TC-17", "Bash", "git push --force-with-lease", True),
    ("TC-18", "Bash", "git push -f origin main", True),
    ("TC-19", "Bash", "git push -fu origin main", True),
    ("TC-20", "Bash", "git push -uf origin main", True),
    ("TC-21", "Bash", "git push origin +HEAD:main", True),
    ("TC-22", "Bash", "git push origin +main", True),
    ("TC-23", "Bash", "git push --delete origin branch", True),
    ("TC-24", "Bash", "git push -d origin branch", True),
    ("TC-25", "Bash", "git push origin :branch", True),
    # BLOCK: still-blocked verbs (TC-26..TC-35)
    ("TC-26", "Bash", "git reset --hard", True),
    ("TC-27", "Bash", "git rebase -i HEAD~3", True),
    ("TC-28", "Bash", "git clean -fd", True),
    ("TC-29", "Bash", "git checkout -- file.txt", True),
    ("TC-30", "Bash", "git branch -D feature", True),
    ("TC-31", "Bash", "git cherry-pick abc", True),
    ("TC-32", "Bash", "git stash", True),
    ("TC-33", "Bash", "git merge origin/main", True),
    ("TC-34", "Bash", "git revert HEAD", True),
    ("TC-35", "Bash", "git pull", True),
    # BLOCK: --mirror, --prune, and equals form of --force-with-lease (TC-36..TC-39)
    ("TC-36", "Bash", "git push --mirror", True),
    ("TC-37", "Bash", "git push --mirror origin", True),
    ("TC-38", "Bash", "git push --prune origin refs/heads/*", True),
    ("TC-39", "Bash", "git push --force-with-lease=main origin main", True),
    # ALLOW: --force-if-includes (inert modifier) and chained commands (TC-40..TC-43)
    ("TC-40", "Bash", "git push --force-if-includes origin main", False),
    ("TC-41", "Bash", "git push origin main && grep -rf pat .", False),
    ("TC-42", "Bash", "git push origin main && cp -f a b", False),
    ("TC-43", "Bash", "git push origin main; ls -d dirs", False),
    # BLOCK: tag create and delete (TC-44..TC-45)
    ("TC-44", "Bash", "git tag v1.0.0", True),
    ("TC-45", "Bash", "git tag -d v1.0.0", True),
    # BLOCK: branch delete and rename (TC-46..TC-47)
    ("TC-46", "Bash", "git branch -d feature", True),
    ("TC-47", "Bash", "git branch -m old new", True),
    # BLOCK: global-option bypass cases (TC-48..TC-54)
    ("TC-48", "Bash", "git -C /repo push --force", True),
    ("TC-49", "Bash", "git -c x=y reset --hard", True),
    ("TC-50", "Bash", "git --no-pager push --force", True),
    ("TC-51", "Bash", "git -C /repo branch -D main", True),
    ("TC-52", "Bash", "git -C /repo push origin :main", True),
    ("TC-53", "Bash", "git -p push --force", True),
    ("TC-54", "Bash", "git -c a.b=c push --delete origin x", True),
    # ALLOW: global-option prefix with safe verbs (TC-55..TC-60)
    ("TC-55", "Bash", "git -C /repo status", False),
    ("TC-56", "Bash", "git -c x=y add -A", False),
    ("TC-57", "Bash", 'git -C /repo commit -m "x"', False),
    ("TC-58", "Bash", "git --no-pager log", False),
    ("TC-59", "Bash", "git -C /repo push origin feat/x", False),
    ("TC-60", "Bash", "git -C /repo push", False),
    # BLOCK: previously-unlisted global options must not bypass the guard (TC-61..TC-67)
    ("TC-61", "Bash", "git --exec-path=/x push --force", True),
    ("TC-62", "Bash", "git --config-env=X=Y push --force", True),
    ("TC-63", "Bash", "git --no-advice push --force", True),
    ("TC-64", "Bash", "git --super-prefix=x push --force", True),
    ("TC-65", "Bash", "git --attr-source=x reset --hard", True),
    ("TC-66", "Bash", "git -C /repo --exec-path=/x push --force", True),
    ("TC-67", "Bash", "git -c x=y --exec-path=/y push --force", True),
    # ALLOW: unlisted global options with safe verbs must not be over-blocked (TC-68..TC-70)
    ("TC-68", "Bash", "git --no-advice push origin feat/x", False),
    ("TC-69", "Bash", "git --exec-path=/x status", False),
    ("TC-70", "Bash", "git --no-advice add -A", False),
]


def _case_ids():
    return [entry[0] for entry in CASES]


import pytest


@pytest.mark.parametrize(
    "case_id,tool_name,command,expected_block", CASES, ids=_case_ids()
)
def test_block_git_writes(case_id, tool_name, command, expected_block):
    """Each case asserts ALLOW or BLOCK behavior of block-git-writes.sh."""
    out = run_guard(command=command, tool_name=tool_name)
    block_marker = '"decision":"block"'
    if expected_block:
        assert block_marker in out, (
            f"{case_id}: expected BLOCK for tool_name={tool_name!r} command={command!r}; "
            f"stdout did not contain {block_marker!r}; got stdout={out!r}"
        )
    else:
        assert block_marker not in out, (
            f"{case_id}: expected ALLOW for tool_name={tool_name!r} command={command!r}; "
            f"stdout must not contain {block_marker!r}; got stdout={out!r}"
        )
