customAlphabet() and customRandom() give wrong IDs for a size that is not an integer

`customAlphabet('0123456789abcdef')(16.5)` must return an ID with 16 characters, and each call must return a different ID.
`customRandom('abcd', 4, random)(4.5)` must return the same ID as size 4.

The current result for a size such as 16.5 or 4.5 is not correct in the Node.js version and in the browser version.
