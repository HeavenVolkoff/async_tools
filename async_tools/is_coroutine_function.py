"""Work derived from curio written by David Beazley.

Reference:
    https://github.com/dabeaz/curio/blob/3d610aea866178800b1e5dbf5cfef8210418fb58/curio/meta.py
See original licenses in:
    https://github.com/dabeaz/curio/blob/3d610aea866178800b1e5dbf5cfef8210418fb58/LICENSE
"""

# Internal
import typing as T
import inspect
from types import MethodType
from functools import partial


def is_coroutine_function(
    func: T.Union["partial[T.Any]", T.Callable[..., T.Any], MethodType]
) -> bool:
    """
    Modified test for a coroutine function with awareness of functools.partial
    """
    if isinstance(func, partial):
        return is_coroutine_function(func.func)
    if isinstance(func, MethodType):
        return is_coroutine_function(func.__func__)
    return inspect.iscoroutinefunction(func) or inspect.isasyncgenfunction(func)


__all__ = ("is_coroutine_function",)
