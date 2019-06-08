"""Work derived from curio written by David Beazley.

Reference:
    https://github.com/dabeaz/curio/blob/3d610aea866178800b1e5dbf5cfef8210418fb58/curio/meta.py
See original licenses in:
    https://github.com/dabeaz/curio/blob/3452129f513df501b962f456ef68c4204c2ad4c2/LICENSE
"""

# Internal
import typing as T
import inspect

# External
import typing_extensions as Te

# Project
from .async_abc import AsyncABCMeta

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
        mcs: Te.Type["AsyncObjectMeta"],
        name: str,
        bases: T.Tuple[type, ...],
        namespace: T.Dict[str, T.Any],
    ) -> None:
        if "__init__" in namespace and not inspect.iscoroutinefunction(namespace["__init__"]):
            raise TypeError("__init__ must be a coroutine")
        return super().__new__(mcs, name, bases, namespace)  # type: ignore

    async def __call__(cls: K, *args: T.Any, **kwargs: T.Any) -> K:
        self: K = cls.__new__(cls, *args, **kwargs)  # type: ignore
        await self.__init__(*args, **kwargs)  # type: ignore
        return self


class AsyncObject(metaclass=AsyncObjectMeta):
    pass


__all__ = ("AsyncObjectMeta", "AsyncObject")
