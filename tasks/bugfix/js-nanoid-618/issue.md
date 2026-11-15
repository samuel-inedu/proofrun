The command line tool accepts sizes that are not positive integers

`nanoid --size 0.5`, `nanoid --size 1.5` and `nanoid --size Infinity` do not print an error.

The expected behaviour: for each of these values the tool stops with the message `Size must be positive integer`.
