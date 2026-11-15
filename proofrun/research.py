"""Run one research question and grade the answer."""
from . import grader, solvers

PROMPT = """Answer the question. Do the research that the question needs.
Give sources for the facts that you use.
Put the final answer on the last line in this form:
ANSWER: <answer>

Question: {question}
"""


def run_research(task, solver, command=None):
    record = {"id": task["id"], "kind": "research", "outcome": None, "detail": "",
              "expected": task["answer"]}
    try:
        answer, reply = solvers.solve_research(task, PROMPT.format(question=task["question"]), solver, command)
    except solvers.SolverError as error:
        record.update(outcome="solver_error", detail=str(error))
        return record
    record["answer"] = answer
    record["reply"] = reply[-4000:]
    correct, reason = grader.grade(task, answer)
    if correct:
        record.update(outcome="correct", detail=reason)
    elif reason == "no_answer":
        record.update(outcome="no_answer", detail="the reply has no 'ANSWER:' line")
    else:
        record.update(outcome="incorrect", detail=reason)
    return record
