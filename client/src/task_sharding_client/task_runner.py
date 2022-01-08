import logging

logger = logging.getLogger(__name__)


class TaskRunner:
    def __init__(self, schema: dict, config: any):
        self._config = config
        self._schema = schema

    def run(self, step_id: str) -> bool:
        raise NotImplementedError()


class DefaultTask(TaskRunner):
    def run(self, step_id: str) -> bool:
        logger.info("Starting task")
        logger.info("Finished task")
        return True
