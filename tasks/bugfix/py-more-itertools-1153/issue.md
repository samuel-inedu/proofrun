reversed() fails on an empty numeric_range

`list(reversed(numeric_range(0)))` raises `IndexError`.
The expected result is an empty list, the same result that `list(reversed(range(0)))` gives.

`reversed()` on an empty `numeric_range` must return an empty iterator.
