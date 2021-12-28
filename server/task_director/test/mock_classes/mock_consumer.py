class MockConsumer:
    def __init__(self, id):
        self.id = id

    async def send(self, text_data: str):
        self.sent_data = text_data

    def get_sent_data(self):
        return self.sent_data
