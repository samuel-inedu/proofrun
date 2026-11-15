import unittest

from proofrun.grader import grade, normalize_text, parse_date, parse_number
from proofrun.solvers import extract_answer, extract_patch


class TestText(unittest.TestCase):
    def test_case_punctuation_articles_accents(self):
        self.assertEqual(normalize_text("The  São-Paulo!"), "sao paulo")

    def test_alias(self):
        task = {"answer": "Canberra", "aliases": ["Canberra, ACT"]}
        self.assertTrue(grade(task, "canberra, act")[0])
        self.assertFalse(grade(task, "Sydney")[0])

    def test_empty_answer(self):
        self.assertEqual(grade({"answer": "x"}, "  "), (False, "no_answer"))


class TestNumber(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_number("1,250 km"), 1250)
        self.assertEqual(parse_number("about 3.5 million people"), 3_500_000)
        self.assertIsNone(parse_number("none"))

    def test_tolerance(self):
        task = {"answer": "100", "answer_type": "number", "tolerance": 2}
        self.assertTrue(grade(task, "101.5")[0])
        self.assertFalse(grade(task, "103")[0])


class TestDate(unittest.TestCase):
    def test_formats(self):
        for text in ("1960-10-01", "1 October 1960", "October 1, 1960", "1st Oct 1960", "01/10/1960"):
            self.assertEqual(parse_date(text), "1960-10-01", text)
        self.assertEqual(parse_date("October 1960"), "1960-10")
        self.assertEqual(parse_date("1960"), "1960")

    def test_expected_year_accepts_full_date(self):
        task = {"answer": "1960", "answer_type": "date"}
        self.assertTrue(grade(task, "1 October 1960")[0])
        self.assertFalse(grade(task, "1 October 1961")[0])

    def test_expected_full_date_rejects_year_only(self):
        task = {"answer": "1960-10-01", "answer_type": "date"}
        self.assertFalse(grade(task, "1960")[0])


class TestExtract(unittest.TestCase):
    def test_last_answer_line(self):
        self.assertEqual(extract_answer("ANSWER: no\ntext\nanswer:  Yes "), "Yes")
        self.assertEqual(extract_answer("no marker"), "")

    def test_patch_in_code_block(self):
        reply = "Fix:\n```diff\n--- a/x\n+++ b/x\n@@ -1 +1 @@\n-a\n+b\n```\nDone."
        self.assertEqual(extract_patch(reply), "--- a/x\n+++ b/x\n@@ -1 +1 @@\n-a\n+b\n")

    def test_no_patch(self):
        self.assertEqual(extract_patch("I cannot fix this."), "")


class TestWindowsCommand(unittest.TestCase):
    def test_python3_is_replaced_on_windows_only(self):
        import sys
        from proofrun.sandbox import local_command
        self.assertEqual(local_command("python3 -m unittest x", windows=True), f'"{sys.executable}" -m unittest x')
        self.assertEqual(local_command("python3 -m unittest x", windows=False), "python3 -m unittest x")
        self.assertEqual(local_command("node --test a.js", windows=True), "node --test a.js")


if __name__ == "__main__":
    unittest.main()
