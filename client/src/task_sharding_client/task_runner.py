import logging

logger = logging.getLogger(__name__)


class TaskRunner:
    def __init__(self, schema: dict, config: any):
        self._config = config
        self._schema = schema

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.abort()

    def run(self, step_id: str) -> bool:
        raise NotImplementedError()

    def abort(self):
        raise NotImplementedError()


class DefaultTask(TaskRunner):
    def run(self, step_id: str) -> bool:
        logger.info("Starting task: " + step_id)
        logger.info("Finished task: " + step_id)
        return True

    def abort(self):
        pass