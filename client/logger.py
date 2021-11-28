import threading


class Logger:
    def __init__(self, log_prefix: str):
        self._log_prefix = log_prefix
        self._lock = threading.Lock()

    def print(self, message: any):
        with self._lock:
            print("[" + self._log_prefix + "] " + str(message))
