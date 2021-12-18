from django.apps import AppConfig

from game.controller import Controller


class GameConfig(AppConfig):
    name = "game"
    controller = None

    def ready(self):
        self.controller = Controller()
