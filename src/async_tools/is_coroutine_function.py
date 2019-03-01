"""Work derived from curio written by David Beazley.

Reference:
    https://github.com/dabeaz/curio/blob/3d610aea866178800b1e5dbf5cfef8210418fb58/curio/meta.py
See original licenses in:
    https://github.com/dabeaz/curio/blob/3452129f513df501b962f456ef68c4204c2ad4c2/LICENSE
"""

# Internal
import typing as T
import inspect
from types import MethodType
from functools import partial


def iscoroutinefunction(
    func: T.Union["partial[T.Any]", T.Callable[..., T.Any], MethodType]
) -> bool:
    """
    Modified test for a coroutine function with awareness of functools.partial
    """
    if isinstance(func, partial):
        return iscoroutinefunction(func.func)
    if isinstance(func, MethodType):
        return iscoroutinefunction(func.__func__)
    return inspect.iscoroutinefunction(func) or inspect.isasyncgenfunction(func)


__all__ = ("iscoroutinefunction",)
