"""Write results.jsonl and summary.md."""
import json
from collections import Counter, defaultdict
from pathlib import Path

SUCCESS = {"resolved", "correct"}


def write_report(records, out_dir, title):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "results.jsonl", "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    summary = build_summary(records, title)
    (out / "summary.md").write_text(summary, encoding="utf-8")
    return summary


def build_summary(records, title):
    by_task = defaultdict(list)
    for record in records:
        by_task[record["id"]].append(record)
    lines = [f"# {title}", ""]
    for kind in ("bugfix", "research"):
        group = [r for r in records if r["kind"] == kind]
        if not group:
            continue
        good = sum(r["outcome"] in SUCCESS for r in group)
        lines += [f"## {kind}: {good}/{len(group)} runs succeeded ({100 * good / len(group):.0f}%)", ""]
        counts = Counter(r["outcome"] for r in group)
        lines += ["| outcome | runs |", "|---|---|"]
        lines += [f"| {name} | {count} |" for name, count in counts.most_common()]
        lines += ["", "| task | runs | succeeded | outcomes | detail of last run |", "|---|---|---|---|---|"]
        for task_id, runs in by_task.items():
            if runs[0]["kind"] != kind:
                continue
            ok = sum(r["outcome"] in SUCCESS for r in runs)
            outcomes = ", ".join(f"{n} x{c}" for n, c in Counter(r["outcome"] for r in runs).items())
            detail = runs[-1]["detail"].replace("|", "/").replace("\n", " ")[:90]
            lines.append(f"| {task_id} | {len(runs)} | {ok} | {outcomes} | {detail} |")
        lines.append("")
    return "\n".join(lines)
