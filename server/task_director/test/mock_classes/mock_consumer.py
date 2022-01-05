import queue

from task_director.src.controller import TaskDirectorController


class MockController(TaskDirectorController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
