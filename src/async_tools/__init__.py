"""Asynchronous Reactive eXtensions."""

# External
import pkg_resources

# Project
from .expires import expires, auto_timeout
from .Loopable import Loopable
from .all_tasks import all_tasks
from .current_task import current_task
from .attempt_await import attempt_await
from .wait_with_care import ALL_COMPLETED, FIRST_COMPLETED, FIRST_EXCEPTION, wait_with_care
from .get_running_loop import get_running_loop

try:
    __version__ = str(pkg_resources.resource_string(__name__, "VERSION"), encoding="utf8")
except (pkg_resources.ResolutionError, FileNotFoundError):
    __version__ = "0.0a0"


__all__ = (
    "__version__",
    "expires",
    "auto_timeout",
    "Loopable",
    "all_tasks",
    "current_task",
    "attempt_await",
    "ALL_COMPLETED",
    "FIRST_COMPLETED",
    "FIRST_EXCEPTION",
    "wait_with_care",
    "get_running_loop",
)
