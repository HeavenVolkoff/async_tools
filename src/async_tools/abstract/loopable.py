__all__ = ("AbstractLoopable", "Loopable")

# Internal
import typing as T
from asyncio import AbstractEventLoop, get_running_loop


class AbstractLoopable:
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
