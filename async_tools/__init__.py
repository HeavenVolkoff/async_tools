"""Asynchronous Reactive eXtensions."""

# External
from importlib_metadata import version

# Project
from .expires import Expires as expires
from .loopable import Loopable
from .all_tasks import all_tasks
from .current_task import current_task
from .attempt_await import attempt_await
from .wait_with_care import ALL_COMPLETED, FIRST_COMPLETED, FIRST_EXCEPTION, wait_with_care
from .at_loop_shutdown import at_loop_shutdown
from .get_running_loop import get_running_loop
from .is_coroutine_function import is_coroutine_function

try:
    __version__: str = version(__name__)
except Exception:  # pragma: no cover
    import traceback
    from warnings import warn

    warn(f"Failed to set version due to:\n{traceback.format_exc()}", ImportWarning)
    __version__ = "0.0a0"

__all__ = (
    "__version__",
    "expires",
    "Loopable",
    "all_tasks",
    "current_task",
    "attempt_await",
    "ALL_COMPLETED",
    "FIRST_COMPLETED",
    "FIRST_EXCEPTION",
    "wait_with_care",
    "at_loop_shutdown",
    "get_running_loop",
    "is_coroutine_function",
)
