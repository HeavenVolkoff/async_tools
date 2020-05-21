# Standard
import typing as T

# External
import typing_extensions as Te


class LockProtocol(Te.Protocol):
    def can_acquire(self, __vault: T.Counter[T.Type["LockProtocol"]]) -> bool:
        ...
