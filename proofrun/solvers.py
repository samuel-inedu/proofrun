"""Solvers produce an answer for a task.

oracle   returns the known correct answer. It proves that a task can be solved.
nop      returns nothing. It proves that a task does not pass without work.
command  sends the prompt to any program through standard input and reads the reply.
         Use it to connect a language model command line tool or your own script.
"""
import re
import subprocess
from pathlib import Path


class SolverError(RuntimeError):
    pass


def extract_patch(text):
    """Find a unified diff in a model reply. Return '' when no diff exists."""
    fenced = re.findall(r"```(?:diff|patch)?\s*\n(.*?)```", text, flags=re.S)
    for block in fenced:
        if "--- " in block and "+++ " in block:
            text = block
            break
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("diff --git ") or line.startswith("--- "):
            return "\n".join(lines[index:]).rstrip("\n") + "\n"
    return ""


def extract_answer(text):
    """Return the text after the last 'ANSWER:' marker. Return '' when no marker exists."""
    found = re.findall(r"^\s*ANSWER:\s*(.+?)\s*$", text, flags=re.M | re.I)
    return found[-1] if found else ""


def run_command(command, prompt, timeout=600):
    try:
        done = subprocess.run(
            command, shell=True, input=prompt, timeout=timeout,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace",
        )
    except subprocess.TimeoutExpired:
        raise SolverError("solver command timed out")
    if done.returncode != 0:
        raise SolverError(f"solver command failed ({done.returncode}): {done.stderr.strip()[:300]}")
    return done.stdout


def solve_bugfix(task, prompt, solver, command=None):
    """Return (patch_text, raw_reply)."""
    if solver == "oracle":
        gold = Path(task["dir"]) / "gold.patch"
        if not gold.exists():
            raise SolverError("oracle needs gold.patch")
        text = gold.read_text(encoding="utf-8")
        return text, text
    if solver == "nop":
        return "", ""
    if solver == "command":
        reply = run_command(command, prompt)
        return extract_patch(reply), reply
    raise SolverError(f"unknown solver: {solver}")


def solve_research(task, prompt, solver, command=None):
    """Return (answer_text, raw_reply)."""
    if solver == "oracle":
        reply = f"ANSWER: {task['answer']}"
        return str(task["answer"]), reply
    if solver == "nop":
        return "", ""
    if solver == "command":
        reply = run_command(command, prompt)
        return extract_answer(reply), reply
    raise SolverError(f"unknown solver: {solver}")
