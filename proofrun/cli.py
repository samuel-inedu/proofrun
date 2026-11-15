"""Command line for proofrun."""
import argparse
import sys

from . import sandbox
from .bugfix import run_bugfix
from .report import SUCCESS, write_report
from .research import run_research
from .tasks import TaskError, load_tasks


def _run(tasks, solver, args):
    records = []
    for task in tasks:
        for attempt in range(1, args.repeat + 1):
            if task["kind"] == "bugfix":
                record = run_bugfix(task, solver, command=args.command, backend=args.backend,
                                    timeout=args.timeout, keep=args.keep)
            else:
                record = run_research(task, solver, command=args.command)
            record["solver"] = solver
            record["attempt"] = attempt
            records.append(record)
            print(f"[{solver}] {task['id']} (run {attempt}): {record['outcome']}", flush=True)
    return records


def cmd_run(args):
    if args.solver == "command" and not args.command:
        print("error: --solver command needs --command", file=sys.stderr)
        return 2
    tasks = _select(load_tasks(args.tasks), args)
    records = _run(tasks, args.solver, args)
    print()
    print(write_report(records, args.out, f"proofrun: solver '{args.solver}'"))
    print(f"Files: {args.out}/results.jsonl and {args.out}/summary.md")
    return 0


def cmd_validate(args):
    """A correct task succeeds with the oracle solver and does not succeed with the nop solver."""
    tasks = _select(load_tasks(args.tasks), args)
    args.repeat, args.command = 1, None
    oracle = {r["id"]: r for r in _run(tasks, "oracle", args)}
    nop = {r["id"]: r for r in _run(tasks, "nop", args)}
    bad = []
    for task in tasks:
        tid = task["id"]
        if oracle[tid]["outcome"] not in SUCCESS:
            bad.append(f"{tid}: oracle gave '{oracle[tid]['outcome']}' ({oracle[tid]['detail']})")
        if nop[tid]["outcome"] in SUCCESS:
            bad.append(f"{tid}: the task succeeds with no work")
    print()
    if bad:
        print("INVALID TASKS:")
        for line in bad:
            print("  " + line)
        return 1
    print(f"All {len(tasks)} tasks are valid.")
    return 0


def _select(tasks, args):
    if args.kind:
        tasks = [t for t in tasks if t["kind"] == args.kind]
    if args.only:
        tasks = [t for t in tasks if t["id"] in args.only]
    if not tasks:
        raise TaskError("no tasks selected")
    if args.backend == "docker" and any(t["kind"] == "bugfix" for t in tasks):
        ok, message = sandbox.docker_ready()
        if not ok:
            raise TaskError(f"docker backend not available: {message}")
    return tasks


def main(argv=None):
    parser = argparse.ArgumentParser(prog="proofrun", description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)

    def common(p):
        p.add_argument("--tasks", default="tasks", help="folder that contains the tasks")
        p.add_argument("--kind", choices=["bugfix", "research"], help="run only one task kind")
        p.add_argument("--only", nargs="+", help="run only these task ids")
        p.add_argument("--backend", choices=["local", "docker"], default="local",
                       help="where the test commands run")
        p.add_argument("--timeout", type=int, default=300, help="seconds for each test command")
        p.add_argument("--keep", action="store_true", help="keep the work folders")

    run = sub.add_parser("run", help="run the tasks with one solver")
    common(run)
    run.add_argument("--solver", choices=["oracle", "nop", "command"], required=True)
    run.add_argument("--command", help="program that reads the prompt from standard input")
    run.add_argument("--repeat", type=int, default=1, help="number of runs for each task")
    run.add_argument("--out", default="runs/latest", help="folder for the result files")
    run.set_defaults(func=cmd_run)

    validate = sub.add_parser("validate", help="check each task with the oracle and nop solvers")
    common(validate)
    validate.set_defaults(func=cmd_validate)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except TaskError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
