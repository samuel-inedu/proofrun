interleave_evenly() fails when there are no iterables

`list(interleave_evenly([]))` raises an error.
`list(interleave_evenly([], lengths=[]))` raises the same error.

The expected result for the 2 calls is an empty list.
