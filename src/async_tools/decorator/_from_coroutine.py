"""Work derived from curio written by David Beazley.

Reference:
    https://github.com/dabeaz/curio/blob/3d610aea866178800b1e5dbf5cfef8210418fb58/curio/meta.py
See original licenses in:
    https://github.com/dabeaz/curio/blob/3452129f513df501b962f456ef68c4204c2ad4c2/LICENSE
"""

try:
    from sys import _getframe
except ImportError:
    print("This is only compatible with CPython at the moment")
    raise


# Internal
from inspect import CO_NESTED, CO_COROUTINE, CO_ASYNC_GENERATOR, CO_ITERABLE_COROUTINE

CO_FROM_COROUTINE = CO_COROUTINE | CO_ITERABLE_COROUTINE | CO_ASYNC_GENERATOR


def _from_coroutine(level: int = 2) -> bool:
    f_code = _getframe(level).f_code

    if f_code.co_flags & CO_FROM_COROUTINE:
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
        if f_code.co_flags & CO_NESTED and f_code.co_name[0] == "<":
            return _from_coroutine(level + 2)
        else:
            return False
