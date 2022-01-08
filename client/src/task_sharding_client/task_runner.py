import logging

logger = logging.getLogger(__name__)


class TaskRunner:
    def __init__(self, schema: dict, config: any):
        self._config = config
        self._schema = schema

    def run(self, step_id: str, return_queue):
        raise NotImplementedError()


class DefaultTask(TaskRunner):
    def run(self, step_id: str, return_queue):
        logger.info("Starting task: " + step_id)
        logger.info("Finished task: " + step_id)
        return_queue.put(True)
