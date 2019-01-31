# Internal
from asyncio import AbstractEventLoop

try:
    from asyncio import get_running_loop
except ImportError:
    from asyncio import get_event_loop

    def get_running_loop() -> AbstractEventLoop:
        loop = get_event_loop()

        if not loop.is_running():
            raise RuntimeError("no running event loop")

        return loop


__all__ = ("get_running_loop",)
