"""Work derived from curio written by David Beazley.

Reference:
    https://github.com/dabeaz/curio/blob/133c1528633e65045c469c596664e89e9dd2b8a0
See original licenses in:
    https://github.com/dabeaz/curio/blob/133c1528633e65045c469c596664e89e9dd2b8a0/LICENSE
"""

# Internal
import inspect

try:
    from sys import _getframe
except ImportError:
    print("This is only compatible with CPython at the moment")
    raise

_CO_NESTED = inspect.CO_NESTED
_CO_FROM_COROUTINE = (
    inspect.CO_COROUTINE | inspect.CO_ITERABLE_COROUTINE | inspect.CO_ASYNC_GENERATOR
)


def _from_coroutine(level: int = 2) -> bool:
    f_code = _getframe(level).f_code

    if f_code.co_flags & _CO_FROM_COROUTINE:
        return True
    else:
        # Comment:  It's possible that we could end up here if one calls a function
        # from the context of a list comprehension or a generator expression. For
        # example:
        #
        #   async def coro():
        #        ...
        #        a = [ func() for x in s ]
        #        ...
        #
        # Where func() is some function that we've wrapped with one of the decorator
        # below.  If so, the code object is nested and has a name such as <listcomp> or <genexpr>
        if f_code.co_flags & _CO_NESTED and f_code.co_name[0] == "<":
            return _from_coroutine(level + 2)
        else:
            return False
