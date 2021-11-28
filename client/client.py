import websocket
import json
import threading
from time import sleep


class Connection:
    def __init__(self, server_url: str):
        self._websocket = self._init_connection(server_url)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._websocket:
            self._websocket.close()

    def _init_connection(self, server_url: str) -> websocket.WebSocketApp:
        websocket.enableTrace(True)
        ws = websocket.WebSocketApp(
            server_url, on_open=self.on_open, on_message=self.on_message, on_error=self.on_error, on_close=self.on_close
        )
        wst = threading.Thread(target=ws.run_forever)
        wst.daemon = True
        wst.start()

        connection_timeout = 5
        while not ws.sock.connected and connection_timeout > 0:
            connection_timeout -= 1
            sleep(1)

        if not ws.sock.connected:
            raise Exception("Failed to connect")

        return ws

    # WS Thread
    def on_message(self, ws: websocket.WebSocketApp, message: dict):
        print("Message received: " + message)

    # WS Thread
    def on_error(self, ws: websocket.WebSocketApp, error):
        print("ERROR: " + error)

    # WS Thread
    def on_close(self, ws: websocket.WebSocketApp, close_status_code, close_msg):
        print("### closed ###")

    # Main Thread
    def on_open(self, ws: websocket.WebSocketApp):
        print("Opened connection")

    # Main Thread
    def send_message(self, message: dict):
        self._websocket.send(json.dumps(message))


if __name__ == "__main__":
    with Connection("ws://localhost:8000/ws") as connection:
        print("Sending message")
        connection.send_message({"email": "alex@alex1", "username": "username", "message": "message"})
        sleep(2)
