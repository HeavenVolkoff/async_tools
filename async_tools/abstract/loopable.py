# Internal
import typing as T
from asyncio import AbstractEventLoop

# Project
from ..get_running_loop import get_running_loop


class Loopable:
    """Interface for easy access to asyncio loop."""

    __slots__ = ("_loop",)

    def __init__(self, **kwargs: T.Any) -> None:
        """Loopable constructor.

        Arguments:
            kwargs: Keyword parameters for super.
        """
        super().__init__(**kwargs)  # type: ignore

        self._loop: T.Optional[AbstractEventLoop] = None

    @property
    def loop(self) -> AbstractEventLoop:
        """Public access to loop."""
        if self._loop is None:
            raise ValueError("Loop is not available")

        return self._loop


__all__ = ("Loopable",)
