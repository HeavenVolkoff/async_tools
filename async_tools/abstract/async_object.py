"""Work derived from curio written by David Beazley.

Reference:
    https://github.com/dabeaz/curio/blob/3d610aea866178800b1e5dbf5cfef8210418fb58/curio/meta.py
Removed in:
    https://github.com/dabeaz/curio/commit/66c60fec61610ae386bc03717724e6438948a419
See original licenses in:
    https://github.com/dabeaz/curio/blob/3d610aea866178800b1e5dbf5cfef8210418fb58/LICENSE
"""

# Standard
import typing as T
import inspect

# Project
from .async_abc import AsyncABCMeta

# Generic types
K = T.TypeVar("K")


class AsyncObjectMeta(AsyncABCMeta):
    """
    Metaclass that allows for asynchronous instance initialization and the
    __init__() method to be defined as a coroutine.   Usage:
    class Spam(metaclass=AsyncInstanceType):
        async def __init__(self, x, y):
            self.x = x
            self.y = y
    async def main():
         s = await Spam(2, 3)
         ...
    """

    @staticmethod
    def __new__(
        mcs: T.Type["AsyncObjectMeta"],
        name: str,
        bases: T.Tuple[type, ...],
        namespace: T.Dict[str, T.Any],
    ) -> "AsyncObjectMeta":
        if "__init__" in namespace and not inspect.iscoroutinefunction(namespace["__init__"]):
            raise TypeError("__init__ must be a coroutine")
        return super().__new__(mcs, name, bases, namespace)  # type: ignore

    async def __call__(cls: T.Type[K], *args: T.Any, **kwargs: T.Any) -> K:
        self: K = cls.__new__(cls, *args, **kwargs)  # type: ignore
        await self.__init__(*args, **kwargs)  # type: ignore
        return self


class AsyncObject(metaclass=AsyncObjectMeta):
    pass


__all__ = ("AsyncObjectMeta", "AsyncObject")
