# Internal
import typing as T
from asyncio import Future, AbstractEventLoop
from collections import Counter

# External
from async_tools.context import asynccontextmanager

# Project
from ..loopable import Loopable
from ._protocol import LockProtocol


class AsyncLockStack(Loopable):
    """A small asyncio framework for constructing locks.

    This is a modified version of the following:
        link: https://github.com/michalc/fifolock/blob/ce7a2d72cc84c4114a68b3b79176367db1d866cd/fifolock.py
        author: Michal Charemza <https://github.com/michalc>
        license: MIT <https://github.com/michalc/fifolock/blob/ce7a2d72cc84c4114a68b3b79176367db1d866cd/LICENSE>

    """

    def __init__(self, *, loop: T.Optional[AbstractEventLoop] = None) -> None:
        super().__init__(loop=loop)

        self._vault: T.Counter[T.Type[LockProtocol]] = Counter()
        self._locks: T.List[T.Tuple["Future[None]", LockProtocol]] = []

    def _maybe_acquire(self) -> None:
        while self._locks:
            fut, lock = self._locks.pop()
            if fut.cancelled():
                continue

            if not lock.can_acquire(self._vault):
                self._locks.append((fut, lock))
                break

            self._vault[type(lock)] += 1
            fut.set_result(None)

    @asynccontextmanager
    async def __call__(self, lock_type: T.Type[LockProtocol]) -> T.AsyncGenerator[None, None]:
        fut = self._loop.create_future()
        lock = lock_type()
        self._locks.append((fut, lock))
        self._maybe_acquire()
        try:
            await fut
            yield
        finally:
            if fut.done() and not fut.cancelled():
                self._vault[type(lock)] -= 1
                self._maybe_acquire()
