from time import sleep

import json
import logging
import queue
import threading
import websocket


INITIAL_CONN_TIMEOUT = 5

logger = logging.getLogger(__name__)


class Connection:
    def __init__(self, server_url: str):
        self._received_messages = queue.Queue()
        self._websocket = self._init_connection(server_url)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._websocket:
            self._websocket.close()

    def _init_connection(self, server_url: str) -> websocket.WebSocketApp:
        logger.info("Initialising connection...")
        websocket.enableTrace(False)
        web_socket = websocket.WebSocketApp(
            server_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        wst = threading.Thread(target=web_socket.run_forever)
        wst.daemon = True
        wst.start()

        sleep(1)

        connection_timeout = INITIAL_CONN_TIMEOUT
        if web_socket.sock:
            while not web_socket.sock.connected and connection_timeout > 0:
                connection_timeout -= 1
                sleep(1)

        if not web_socket.sock.connected:
            raise Exception("Failed to connect")

        return web_socket

    # WS Thread
    def _on_message(self, web_socket: websocket.WebSocketApp, message: dict):
        self._received_messages.put(message)

    # WS Thread
    def _on_error(self, web_socket: websocket.WebSocketApp, error):
        logger.error("ERROR: " + str(error))

    # WS Thread
    def _on_close(self, web_socket: websocket.WebSocketApp, close_status_code, close_msg):
        logger.info("### closed ###")

    # Main Thread
    def _on_open(self, web_socket: websocket.WebSocketApp):
        logger.info("Opened connection")

    # Main Thread
    def send_message(self, message: dict):
        self._websocket.send(json.dumps(message))

    # Main Thread
    def close_websocket(self):
        self._websocket.close()

    # Main Thread
    def get_latest_message(self, timeout: float) -> dict:
        return self._received_messages.get(block=False, timeout=timeout)
