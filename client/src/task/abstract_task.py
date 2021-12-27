from src.logger import Logger


class AbstractTask:
    def set_logger(self, logger: Logger):
        self._logger = logger

    def set_cwd(self, cwd: str):
        self._cwd = cwd

    def load_schema(self, schema: dict, step_id: str):
        raise NotImplementedError()

    def run(self) -> bool:
        raise NotImplementedError()
