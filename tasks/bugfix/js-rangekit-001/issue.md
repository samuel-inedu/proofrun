range() returns an empty array for a negative step

`range(5, 0, -1)` returns `[]`.
The expected result is `[5, 4, 3, 2, 1]`.

A negative step must count down from start to end. The end value is not included.
