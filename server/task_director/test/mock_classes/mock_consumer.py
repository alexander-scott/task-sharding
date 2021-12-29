import queue


class MockConsumer:
    def __init__(self, id):
        self.id = id
        self.sent_messages = queue.Queue()

    async def send(self, text_data: str):
        self.sent_messages.put(text_data)

    def get_sent_data(self, block=True, timeout=None):
        return self.sent_messages.get(block=block, timeout=timeout)
