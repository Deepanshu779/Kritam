"""Shared microphone stream guard to prevent competing audio capture workers."""

import threading
from contextlib import contextmanager
from typing import Iterator


_MICROPHONE_LOCK = threading.Lock()


@contextmanager
def microphone_session(timeout_s: float = 2.0) -> Iterator[bool]:
    """Try to acquire exclusive microphone access for one listener session."""
    acquired = _MICROPHONE_LOCK.acquire(timeout=timeout_s)
    try:
        yield acquired
    finally:
        if acquired:
            _MICROPHONE_LOCK.release()
