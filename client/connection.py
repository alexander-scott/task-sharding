import json
import queue
import threading
import websocket
from typing import Optional
from time import sleep

from logger import Logger

INITIAL_CONN_TIMEOUT = 5


class Connection:
    def __init__(self, server_url: str, logger: Logger):
        self._logger = logger
        self._received_messages = queue.Queue()
        self._websocket = self._init_connection(server_url)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._websocket:
            self._websocket.close()

    def _init_connection(self, server_url: str) -> websocket.WebSocketApp:
        self._logger.print("Initialising connection...")
        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(
            server_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        wst = threading.Thread(target=ws.run_forever)
        wst.daemon = True
        wst.start()

        connection_timeout = INITIAL_CONN_TIMEOUT
        if ws.sock:
            while not ws.sock.connected and connection_timeout > 0:
                connection_timeout -= 1
                sleep(1)

        if not ws.sock.connected:
            raise Exception("Failed to connect")

        return ws

    # WS Thread
    def _on_message(self, ws: websocket.WebSocketApp, message: dict):
        self._received_messages.put(message)

    # WS Thread
    def _on_error(self, ws: websocket.WebSocketApp, error):
        self._logger.print("ERROR: " + str(error))

    # WS Thread
    def _on_close(self, ws: websocket.WebSocketApp, close_status_code, close_msg):
        self._logger.print("### closed ###")

    # Main Thread
    def _on_open(self, ws: websocket.WebSocketApp):
        self._logger.print("Opened connection")

    # Main Thread
    def send_message(self, message: dict):
        self._websocket.send(json.dumps(message))

    # Main Thread
    def get_latest_message(self, timeout: float) -> Optional[dict]:
        return self._received_messages.get(block=True, timeout=timeout)
