from django.conf.urls import url
from game.consumers import TicTacToeConsumer

websocket_urlpatterns = [
    url(r"^ws/api/(?P<api_version>\w+)/$", TicTacToeConsumer.as_asgi()),
]
