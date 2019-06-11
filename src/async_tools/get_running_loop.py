# Internal
from asyncio import AbstractEventLoop

try:
    from asyncio import get_running_loop
except ImportError:
    import typing as T

    # A basic shim of get_running_loop for python 3.6
    def get_running_loop() -> T.Optional[AbstractEventLoop]:
        from asyncio import get_event_loop

        exc: T.Optional[Exception] = None

        try:
            loop = get_event_loop()

            if loop.is_running():
                return loop
        except Exception as exc:
            pass

        raise RuntimeError("no running event loop") from exc


__all__ = ("get_running_loop",)
