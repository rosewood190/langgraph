from __future__ import annotations

import itertools
import sys
import threading
import time
from contextlib import contextmanager
from typing import Iterator


@contextmanager
def progress_indicator(message: str = "Agent 正在思考") -> Iterator[None]:
    stop_event = threading.Event()

    def run() -> None:
        for symbol in itertools.cycle(["|", "/", "-", "\\"]):
            if stop_event.is_set():
                break
            sys.stdout.write(f"\r{message} {symbol}")
            sys.stdout.flush()
            time.sleep(0.12)
        sys.stdout.write("\r" + " " * (len(message) + 4) + "\r")
        sys.stdout.flush()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop_event.set()
        thread.join(timeout=1)
