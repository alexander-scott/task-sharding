class TaskRunner:
    def __init__(self, schema: dict, config: any):
        self._config = config
        self._schema = schema

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.abort()

    def run(self, task_id: str) -> int:
        raise NotImplementedError()

    def abort(self):
        raise NotImplementedError()
