"""Work derived from curio written by David Beazley.

Reference:
    https://github.com/dabeaz/curio/blob/3d610aea866178800b1e5dbf5cfef8210418fb58/curio/meta.py
See original licenses in:
    https://github.com/dabeaz/curio/blob/3452129f513df501b962f456ef68c4204c2ad4c2/LICENSE
"""

# Internal
import typing as T
import inspect
from abc import ABCMeta

# Project
from ..is_coroutine_function import iscoroutinefunction


class AsyncABCMeta(ABCMeta):
    """
    Metaclass that gives all of the features of an abstract base class, but
    additionally enforces coroutine correctness on subclasses. If any method
    is defined as a coroutine in a parent, it must also be defined as a
    coroutine in any child.
    """

    def __init__(cls, name: str, bases: T.Tuple[type, ...], namespace: T.Dict[str, T.Any]):
        coros: T.Dict[str, T.Coroutine[T.Any, T.Any, T.Any]] = {}
        for base in reversed(cls.__mro__):
            coros.update(
                (name, val) for name, val in vars(base).items() if iscoroutinefunction(val)
            )

        for name, val in vars(cls).items():
            if name in coros and not iscoroutinefunction(val):
                raise TypeError("Must use async def %s%s" % (name, inspect.signature(val)))

        super().__init__(name, bases, namespace)


class AsyncABC(metaclass=AsyncABCMeta):
    pass


__all__ = ("AsyncABCMeta", "AsyncABC")
