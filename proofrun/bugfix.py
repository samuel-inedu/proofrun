"""Run one bug-fix task.

Steps:
1. Copy (or clone) the repository into a new work folder.
2. Apply tests.patch. It adds the tests that describe the bug.
3. Run the fail_to_pass commands. They must fail before the fix.
4. Ask the solver for a patch and apply it.
5. Run fail_to_pass and pass_to_pass. All commands must succeed.
"""
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import sandbox, solvers

MAX_CONTEXT_CHARS = 60_000
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "dist", "build"}

PROMPT = """You fix a bug in a {language} repository.

## Issue
{issue}

## Repository files
{files}

## Instructions
Write a patch that fixes the issue. Do not change the tests.
Reply with one unified diff in a ```diff code block. Use paths relative to the repository root.
"""


def _git(args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, text=True, errors="replace")


def prepare_workdir(task):
    work = Path(tempfile.mkdtemp(prefix=f"proofrun-{task['id']}-"))
    if "repo_url" in task:
        done = _git(["clone", "--quiet", task["repo_url"], str(work)], cwd=None)
        if done.returncode != 0:
            raise RuntimeError(f"git clone failed: {done.stdout[:300]}")
        if task.get("base_commit"):
            done = _git(["checkout", "--quiet", task["base_commit"]], cwd=work)
            if done.returncode != 0:
                raise RuntimeError(f"git checkout failed: {done.stdout[:300]}")
    else:
        shutil.copytree(Path(task["dir"]) / "repo", work, dirs_exist_ok=True)
        _git(["init", "--quiet"], cwd=work)
    return work


def apply_patch(patch_text, work):
    """Return (ok, message)."""
    patch_file = Path(work) / ".proofrun.patch"
    # Write bytes. Text mode on Windows changes the line ends, and then git rejects the patch.
    patch_file.write_bytes(patch_text.replace("\r\n", "\n").encode("utf-8"))
    try:
        done = _git(["apply", "--whitespace=nowarn", patch_file.name], cwd=work)
    finally:
        patch_file.unlink(missing_ok=True)
    return done.returncode == 0, done.stdout.strip()


def read_context(task, work):
    """Collect the source files that the prompt shows to the model."""
    wanted = task.get("context_files")
    paths = []
    if wanted:
        paths = [Path(work) / name for name in wanted]
    else:
        for path in sorted(Path(work).rglob("*")):
            if path.is_file() and not (set(path.relative_to(work).parts) & SKIP_DIRS):
                paths.append(path)
    parts, used = [], 0
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if used + len(text) > MAX_CONTEXT_CHARS:
            break
        used += len(text)
        parts.append(f"### {path.relative_to(work)}\n```\n{text}\n```")
    return "\n\n".join(parts)


def _run_all(commands, work, backend, image, timeout):
    """Run each command. Return (passed, failed, timed_out, logs)."""
    passed, failed, logs, timed_out = [], [], {}, False
    for command in commands:
        result = sandbox.run(command, str(work), backend=backend, image=image, timeout=timeout)
        logs[command] = result.output[-2000:]
        timed_out = timed_out or result.timed_out
        (passed if result.ok else failed).append(command)
    return passed, failed, timed_out, logs


def run_bugfix(task, solver, command=None, backend="local", timeout=300, keep=False):
    record = {"id": task["id"], "kind": "bugfix", "language": task["language"], "outcome": None, "detail": ""}
    image = task.get("image")
    work = None
    try:
        work = prepare_workdir(task)
        if task.get("install"):
            setup = sandbox.run(task["install"], str(work), backend=backend, image=image, timeout=timeout)
            if not setup.ok:
                record.update(outcome="invalid_task", detail="install command failed: " + setup.output[-300:])
                return record

        tests_patch = Path(task["dir"]) / "tests.patch"
        if tests_patch.exists():
            ok, message = apply_patch(tests_patch.read_text(encoding="utf-8"), work)
            if not ok:
                record.update(outcome="invalid_task", detail="tests.patch did not apply: " + message[:300])
                return record

        passed_before, _, _, _ = _run_all(task["fail_to_pass"], work, backend, image, timeout)
        if passed_before:
            record.update(outcome="invalid_task",
                          detail=f"these tests pass before a fix: {passed_before}")
            return record

        prompt = PROMPT.format(language=task["language"], issue=_issue(task), files=read_context(task, work))
        try:
            patch, reply = solvers.solve_bugfix(task, prompt, solver, command)
        except solvers.SolverError as error:
            record.update(outcome="solver_error", detail=str(error))
            return record
        record["patch"] = patch
        if not patch.strip():
            record.update(outcome="empty_patch", detail="the solver gave no patch")
            return record

        ok, message = apply_patch(patch, work)
        if not ok:
            record.update(outcome="patch_did_not_apply", detail=message[:300])
            return record

        _, f2p_failed, timeout_1, logs_1 = _run_all(task["fail_to_pass"], work, backend, image, timeout)
        _, p2p_failed, timeout_2, logs_2 = _run_all(task["pass_to_pass"], work, backend, image, timeout)
        record["logs"] = {**logs_1, **logs_2}
        if timeout_1 or timeout_2:
            record.update(outcome="timeout", detail="a test command did not finish in time")
        elif f2p_failed:
            record.update(outcome="tests_still_fail", detail=f"still fails: {f2p_failed}")
        elif p2p_failed:
            record.update(outcome="broke_passing_tests", detail=f"now fails: {p2p_failed}")
        else:
            record.update(outcome="resolved", detail="all tests pass")
        return record
    except Exception as error:  # report the error in the record and continue with the next task
        record.update(outcome="harness_error", detail=f"{type(error).__name__}: {error}")
        return record
    finally:
        if work is not None:
            if keep:
                record["workdir"] = str(work)
            else:
                shutil.rmtree(work, ignore_errors=True)


def _issue(task):
    path = Path(task["dir"]) / "issue.md"
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return task.get("issue", "(no issue text)")
