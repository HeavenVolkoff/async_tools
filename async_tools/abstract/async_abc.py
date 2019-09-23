"""Work derived from curio written by David Beazley.

Reference:
    https://github.com/dabeaz/curio/blob/3d610aea866178800b1e5dbf5cfef8210418fb58/curio/meta.py
See original licenses in:
    https://github.com/dabeaz/curio/blob/3d610aea866178800b1e5dbf5cfef8210418fb58/LICENSE
"""

# Internal
import typing as T
import inspect

# External
import typing_extensions as Te

# Project
from ..is_coroutine_function import is_coroutine_function

try:
    # Allow easy interoperability between typing generics and AsyncABCMeta on Python <= 3.6
    from typing import GenericMeta as Meta
except ImportError:
    from abc import ABCMeta as Meta  # type: ignore


class AsyncABCMeta(Meta):
    """
    Metaclass that gives all of the features of an abstract base class, but
    additionally enforces coroutine correctness on subclasses. If any method
    is defined as a coroutine in a parent, it must also be defined as a
    coroutine in any child.
    """

    def __init__(
        cls, name: str, bases: T.Tuple[type, ...], namespace: T.Dict[str, T.Any], **kwargs: T.Any
    ) -> None:
        super().__init__(name, bases, namespace, **kwargs)  # type: ignore

        coros: T.Dict[str, T.Coroutine[T.Any, T.Any, T.Any]] = {}
        for base in reversed(cls.__mro__):
            coros.update(
                (name, val) for name, val in vars(base).items() if is_coroutine_function(val)
            )

        for name, val in vars(cls).items():
            if name in coros and not is_coroutine_function(val):
                raise TypeError(f"Must use async def {name}{inspect.signature(val)}")

        super().__init__(name, bases, namespace)


class AsyncABC(metaclass=AsyncABCMeta):
    pass


__all__ = ("AsyncABCMeta", "AsyncABC")
