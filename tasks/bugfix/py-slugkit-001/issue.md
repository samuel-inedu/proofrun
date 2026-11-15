slugify() writes repeated separators

`slugify("Hello,  World!")` returns `hello---world-`.
The expected result is `hello-world`.

Punctuation and repeated spaces must not add more separators.
The result must not start or end with a separator.
