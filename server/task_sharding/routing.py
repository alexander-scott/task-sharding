from django.conf.urls import url
from task_sharding.consumers import TaskShardingConsumer
from task_sharding.src.controller import Controller

websocket_urlpatterns = [
    url(r"^ws/api/(?P<api_version>\w+)/(?P<id>\w+)/$", TaskShardingConsumer.as_asgi()),
]
channel_name_patterns = {
    "controller": Controller.as_asgi(),
}
