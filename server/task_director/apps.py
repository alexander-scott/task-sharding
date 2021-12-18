from django.apps import AppConfig

from task_director.controller import Controller


class TaskDirectorConfig(AppConfig):
    name = "task_director"
    controller = None

    def ready(self):
        self.controller = Controller()
