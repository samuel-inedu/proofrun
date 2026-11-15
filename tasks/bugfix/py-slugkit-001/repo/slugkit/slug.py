import re


def slugify(text, separator="-"):
    """Change text into a lowercase slug for a web address."""
    words = re.sub(r"[^a-z0-9]", " ", text.lower()).split(" ")
    return separator.join(words)
