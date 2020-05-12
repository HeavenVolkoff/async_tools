# Project
# Internal
import typing as T

from ._protocol import LockProtocol


class ReadLock(LockProtocol):
    def can_acquire(self, vault: T.Counter[T.Type["LockProtocol"]]) -> bool:
        return not vault[WriteLock]


class WriteLock(LockProtocol):
    def can_acquire(self, vault: T.Counter[T.Type["LockProtocol"]]) -> bool:
        return not vault[ReadLock] and not vault[WriteLock]
