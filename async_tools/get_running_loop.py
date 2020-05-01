try:
    from asyncio import get_running_loop
except ImportError:
    from asyncio import AbstractEventLoop

    try:
        from asyncio import _get_running_loop
    except ImportError:
        # Shim of get_running_loop for Python <= 3.6
        import typing as T

        from warnings import warn

        warn(
            "The provided shim of get_running_loop() causes side-effects due to internal use of "
            "get_event_loop(). This MAY cause bugs if your code changes the default python loop "
            "or police",
            ImportWarning,
        )

        # A basic shim of get_running_loop for python 3.6
        def get_running_loop() -> AbstractEventLoop:
            from asyncio import get_event_loop

            exc: T.Optional[Exception] = None

            try:
                loop = get_event_loop()

                if loop.is_running():
                    return loop
            except Exception as ex:
                exc = ex
                pass

            raise RuntimeError("no running event loop") from exc

    else:
        # Polyfill of get_running_loop for cPython 3.6
        def get_running_loop() -> AbstractEventLoop:
            loop = _get_running_loop()
            if loop:
                return loop
            raise RuntimeError("no running event loop")


__all__ = ("get_running_loop",)
