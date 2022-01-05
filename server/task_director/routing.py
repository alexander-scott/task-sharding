from django.conf.urls import url
from task_director.consumers import TaskDirectorConsumer
from task_director.src.controller import Controller

websocket_urlpatterns = [
    url(r"^ws/api/(?P<api_version>\w+)/(?P<id>\w+)/$", TaskDirectorConsumer.as_asgi()),
]
channel_name_patterns = {
    "controller": Controller.as_asgi(),
}
