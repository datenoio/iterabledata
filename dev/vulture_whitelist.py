"""Vulture whitelist for protocol-required parameter names.

These names are part of Python protocols whose signatures must keep them:

- ``exc_val`` / ``exc_tb`` in ``__exit__`` / ``__aexit__`` methods
  (``iterable/base.py``, ``iterable/async_base.py``, ``iterable/codec_base.py``,
  ``iterable/db/base.py``, ``iterable/db/iterable.py``,
  ``iterable/ai/progress.py``, ``iterable/helpers/structured_logging.py``,
  and the ``FileLike`` protocol in ``iterable/types.py``) — the interpreter
  passes them positionally, so vulture cannot see the implicit call sites.
- ``whence`` in the ``Seekable.seek`` protocol (``iterable/types.py``) —
  part of the io-style ``seek(offset, whence)`` signature.

Vulture only parses this file (it is never executed); the attribute
references below mark the names as used.
"""

_.exc_val  # noqa: F821
_.exc_tb  # noqa: F821
_.whence  # noqa: F821
