"""Run the sample tasks with each solver. These tests need git, python3 and node on the machine."""
import sys
import unittest
from pathlib import Path

from proofrun.bugfix import run_bugfix
from proofrun.research import run_research
from proofrun.tasks import load_tasks

ROOT = Path(__file__).resolve().parent.parent
FAKE = ROOT / "tests" / "fake_models"
TASKS = {task["id"]: task for task in load_tasks(ROOT / "tasks")}


def fake(name):
    return f'"{sys.executable}" "{FAKE / name}"'


class TestBugfix(unittest.TestCase):
    def test_oracle_resolves_both_languages(self):
        for task_id in ("py-slugkit-001", "js-rangekit-001"):
            self.assertEqual(run_bugfix(TASKS[task_id], "oracle")["outcome"], "resolved", task_id)

    def test_nop_gives_empty_patch(self):
        self.assertEqual(run_bugfix(TASKS["py-slugkit-001"], "nop")["outcome"], "empty_patch")

    def test_command_solver_with_correct_patch(self):
        record = run_bugfix(TASKS["py-slugkit-001"], "command", command=fake("good.py"))
        self.assertEqual(record["outcome"], "resolved", record["detail"])

    def test_patch_that_breaks_a_passing_test(self):
        record = run_bugfix(TASKS["py-slugkit-001"], "command", command=fake("wrong.py"))
        self.assertEqual(record["outcome"], "broke_passing_tests", record["detail"])

    def test_patch_that_does_not_apply(self):
        record = run_bugfix(TASKS["py-slugkit-001"], "command", command=fake("garbage.py"))
        self.assertEqual(record["outcome"], "patch_did_not_apply", record["detail"])

    def test_solver_command_that_fails(self):
        record = run_bugfix(TASKS["py-slugkit-001"], "command", command=f'"{sys.executable}" -c "raise SystemExit(3)"')
        self.assertEqual(record["outcome"], "solver_error")

    def test_task_whose_tests_pass_before_the_fix_is_invalid(self):
        task = dict(TASKS["py-slugkit-001"], fail_to_pass=["python3 -m unittest tests.test_slug"])
        self.assertEqual(run_bugfix(task, "oracle")["outcome"], "invalid_task")

    def test_timeout(self):
        task = dict(TASKS["py-slugkit-001"], pass_to_pass=[f'"{sys.executable}" -c "import time; time.sleep(5)"'])
        self.assertEqual(run_bugfix(task, "oracle", timeout=1)["outcome"], "timeout")


class TestResearch(unittest.TestCase):
    def test_outcomes(self):
        command = fake("answers.py")
        self.assertEqual(run_research(TASKS["sample-number-001"], "command", command)["outcome"], "correct")
        self.assertEqual(run_research(TASKS["sample-date-001"], "command", command)["outcome"], "incorrect")
        self.assertEqual(run_research(TASKS["sample-text-001"], "command", command)["outcome"], "no_answer")


if __name__ == "__main__":
    unittest.main()
