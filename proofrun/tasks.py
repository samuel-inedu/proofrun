"""Load tasks from a folder.

Two task kinds exist:
- bugfix:   a folder that contains task.json (plus repo/, tests.patch, gold.patch, issue.md)
- research: one line in a .jsonl file (question, answer, answer_type, aliases, sources)
"""
import json
from pathlib import Path

BUGFIX_REQUIRED = ["id", "language", "fail_to_pass", "pass_to_pass"]
RESEARCH_REQUIRED = ["id", "question", "answer"]


class TaskError(ValueError):
    pass


def _check(task, required, origin):
    missing = [key for key in required if key not in task]
    if missing:
        raise TaskError(f"{origin}: missing fields {missing}")


def load_tasks(root):
    root = Path(root)
    if not root.exists():
        raise TaskError(f"task folder not found: {root}")
    tasks = []
    for path in sorted(root.rglob("task.json")):
        task = json.loads(path.read_text(encoding="utf-8"))
        task["kind"] = "bugfix"
        task["dir"] = str(path.parent.resolve())
        _check(task, BUGFIX_REQUIRED, str(path))
        if "repo_url" not in task and not (path.parent / "repo").is_dir():
            raise TaskError(f"{path}: add a repo/ folder or a repo_url field")
        tasks.append(task)
    for path in sorted(root.rglob("*.jsonl")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            task = json.loads(line)
            task["kind"] = "research"
            _check(task, RESEARCH_REQUIRED, f"{path}:{number}")
            tasks.append(task)
    ids = [task["id"] for task in tasks]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        raise TaskError(f"duplicate task ids: {duplicates}")
    return tasks
