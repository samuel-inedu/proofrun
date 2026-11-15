"""Grade a research answer against the expected answer.

answer_type:
- text    compare after normalization; 'aliases' lists other accepted spellings
- number  compare numeric values; 'tolerance' sets the allowed difference (default 0)
- date    compare calendar dates; an expected year or year-month matches by prefix
"""
import re
import unicodedata
from datetime import datetime

ARTICLES = {"a", "an", "the"}
DATE_FORMATS = [
    "%Y-%m-%d", "%d %B %Y", "%B %d %Y", "%d %b %Y", "%b %d %Y",
    "%d/%m/%Y", "%Y/%m/%d", "%B %Y", "%b %Y", "%Y-%m", "%Y",
]
PRECISION = {"%B %Y": 7, "%b %Y": 7, "%Y-%m": 7, "%Y": 4}


def normalize_text(value):
    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^\w\s]", " ", value.casefold())
    words = [word for word in value.split() if word not in ARTICLES]
    return " ".join(words)


def parse_number(value):
    """Return the first number in the text, or None."""
    text = str(value).replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    number = float(match.group())
    tail = text[match.end():].strip().casefold()
    for word, factor in (("thousand", 1e3), ("million", 1e6), ("billion", 1e9)):
        if tail.startswith(word):
            number *= factor
    return number


def parse_date(value):
    """Return an ISO string: YYYY-MM-DD, YYYY-MM or YYYY. Return None when no format agrees."""
    text = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", str(value).strip(), flags=re.I)
    text = re.sub(r"\s+", " ", text.replace(",", " ")).strip()
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(text, fmt)
        except ValueError:
            continue
        return parsed.strftime("%Y-%m-%d")[: PRECISION.get(fmt, 10)]
    return None


def grade(task, answer):
    """Return (is_correct, reason)."""
    if not str(answer).strip():
        return False, "no_answer"
    kind = task.get("answer_type", "text")
    expected = task["answer"]
    if kind == "number":
        want, got = parse_number(expected), parse_number(answer)
        if got is None:
            return False, "answer has no number"
        if abs(want - got) <= float(task.get("tolerance", 0)):
            return True, "number agrees"
        return False, f"expected {want:g}, got {got:g}"
    if kind == "date":
        want, got = parse_date(expected), parse_date(answer)
        if got is None:
            return False, "answer is not a date"
        if got.startswith(want):
            return True, "date agrees"
        return False, f"expected {want}, got {got}"
    accepted = {normalize_text(expected)} | {normalize_text(a) for a in task.get("aliases", [])}
    got = normalize_text(answer)
    if got in accepted:
        return True, "text agrees"
    return False, f"expected one of {sorted(accepted)}, got '{got}'"
