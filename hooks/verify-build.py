#!/usr/bin/env python3
"""Stop hook: verify the project still builds / typechecks before allowing Claude to finish.

Activates whenever a build/typecheck tool resolves locally for the project.
Max 1 retry per session to prevent infinite loops.

Conservative by construction: the build/typecheck runs ONLY when its tool is
locally present (no npx-on-miss downloads/hangs). A timeout is treated as a
non-blocking pass-through. For rust/go this checks the compile-error class
(cargo check / go build -o /dev/null) - it does not assert artifact parity.

Stdlib only. Always exits 0 (Claude hook contract). A failing build is signalled
by a single JSON block on stdout; every pass/skip branch prints nothing. Building
the JSON via json.dumps makes the exit-code footgun and the jq-injection class
structurally impossible.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def silent_pass(marker):
    """Clear the marker (gate re-arms) and exit 0 with no stdout."""
    if marker is not None:
        marker.unlink(missing_ok=True)
    sys.exit(0)


def read_marker_count(marker):
    """Read the marker as an int retry counter; junk/missing reads as 0 (fresh)."""
    try:
        return int(marker.read_text().strip())
    except (ValueError, OSError):
        return 0


def main():
    # Completion gate (fail-open bias): unparseable payload -> let Claude finish.
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    session_id = payload.get("session_id") or ""
    cwd = payload.get("cwd") or ""
    stop_hook_active = payload.get("stop_hook_active")

    # Anchor in the working directory (cwd from hook payload, fall back to getcwd).
    project_root = cwd or os.getcwd()
    if not os.path.isdir(project_root):
        sys.exit(0)
    root = Path(project_root)

    # Retry tracking: session-keyed marker so "max 1 retry" survives across
    # invocations in the same Claude session. Fall back to per-invocation when
    # session_id is unavailable.
    if session_id:
        marker = Path(f"/tmp/.claude-build-verify-{session_id}")
    else:
        marker = Path(f"/tmp/.claude-build-verify-fallback-{os.getpid()}")

    # Avoid re-blocking inside an already-blocked Stop loop.
    if stop_hook_active is True or stop_hook_active == "true":
        silent_pass(marker)

    # Already retried once - let Claude finish, the correctness-reviewer catches it.
    if read_marker_count(marker) >= 1:
        silent_pass(marker)

    # Detect a build/typecheck command. First match wins; the tool must resolve
    # locally or the row is skipped, never an npx-on-miss download.
    build_cmd = None
    pkg = root / "package.json"
    if pkg.is_file():
        try:
            scripts = json.loads(pkg.read_text()).get("scripts") or {}
        except (json.JSONDecodeError, OSError):
            scripts = {}
        if scripts.get("build"):
            if (root / "pnpm-lock.yaml").is_file():
                pm = "pnpm"
            elif (root / "yarn.lock").is_file():
                pm = "yarn"
            else:
                pm = "npm"
            build_cmd = [pm, "run", "build"]

    if build_cmd is None and (root / "tsconfig.json").is_file():
        local_tsc = root / "node_modules" / ".bin" / "tsc"
        if os.access(local_tsc, os.X_OK):
            build_cmd = [str(local_tsc), "--noEmit"]
        elif shutil.which("npx"):
            # --no-install: never download; a 127 (tool absent) is a skip below.
            build_cmd = ["npx", "--no-install", "tsc", "--noEmit"]

    if build_cmd is None and (root / "Cargo.toml").is_file() and shutil.which("cargo"):
        build_cmd = ["cargo", "check"]

    if build_cmd is None and (root / "go.mod").is_file() and shutil.which("go"):
        build_cmd = ["go", "build", "-o", "/dev/null", "./..."]

    if build_cmd is None and mypy_configured(root) and shutil.which("mypy"):
        build_cmd = ["mypy", "."]

    # No build command found / tool absent - don't block.
    if build_cmd is None:
        silent_pass(marker)

    # Run the build/typecheck. capture_output keeps child output off the hook's
    # own stdout (STDOUT PURITY); a non-failing branch must print nothing.
    try:
        completed = subprocess.run(
            build_cmd,
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=150,
        )
        rc = completed.returncode
        out = completed.stdout or ""
    except subprocess.TimeoutExpired:
        rc, out = 124, ""
    except FileNotFoundError:
        rc, out = 127, ""

    # 127 = tool not resolvable, 124 = timeout - treat as a skip, never block.
    if rc in (124, 127):
        silent_pass(marker)

    if rc != 0:
        marker.write_text(str(read_marker_count(marker) + 1))
        last30 = "\n".join(out.splitlines()[-30:])
        reason = (
            "Build is failing. Fix it before completing.\n\n```\n" + last30 + "\n```"
        )
        print(json.dumps({"decision": "block", "reason": reason}))
        sys.exit(0)

    # Build passed - clean up.
    silent_pass(marker)


def mypy_configured(root):
    """True when mypy config is present: [tool.mypy] in pyproject, mypy.ini, or [mypy] in setup.cfg."""
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        try:
            if "[tool.mypy]" in pyproject.read_text():
                return True
        except OSError:
            pass
    if (root / "mypy.ini").is_file():
        return True
    setup_cfg = root / "setup.cfg"
    if setup_cfg.is_file():
        try:
            if "[mypy]" in setup_cfg.read_text():
                return True
        except OSError:
            pass
    return False


if __name__ == "__main__":
    main()
