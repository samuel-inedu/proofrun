import unittest

from slugkit import slugify


class TestSlug(unittest.TestCase):
    def test_two_words(self):
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_custom_separator(self):
        self.assertEqual(slugify("Hello World", separator="_"), "hello_world")


if __name__ == "__main__":
    unittest.main()
