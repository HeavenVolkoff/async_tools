# Standard
from asyncio import AbstractEventLoop
import typing as T

# Project
from .abstract import Loopable as AbstractLoopable
from .get_running_loop import get_running_loop


class Loopable(AbstractLoopable):
    """Interface for easy access to asyncio loop."""

    __slots__ = ("_loop",)

    def __init__(self, *, loop: T.Optional[AbstractEventLoop] = None, **kwargs: T.Any) -> None:
        """Loopable constructor.

        Arguments:
            loop: Existing asyncio loop to be used.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        self._loop: AbstractEventLoop = get_running_loop() if loop is None else loop

    @property
    def loop(self) -> AbstractEventLoop:
        """Public access to loop."""

        return self._loop


__all__ = ("Loopable",)
