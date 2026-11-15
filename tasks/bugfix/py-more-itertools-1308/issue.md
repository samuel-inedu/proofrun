bucket() ignores a validator that is falsey

`bucket(iterable, key, validator=v)` replaces `v` with the default validator when `bool(v)` is False.
An example is a callable object that is also an empty container, such as a `set` subclass with `__call__`.

With such a validator that rejects all keys, `10 in D` returns True and `list(D[10])` returns items.
The expected behaviour: `bucket` uses the validator that the caller gives. Only `validator=None` selects the default.
