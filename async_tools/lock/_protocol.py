# Internal
import typing as T


class LockProtocol(T.Protocol):
    def can_acquire(self, __vault: T.Counter[T.Type["LockProtocol"]]) -> bool:
        ...
