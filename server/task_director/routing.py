from django.conf.urls import url
from task_director.consumers import TaskDirectorConsumer

websocket_urlpatterns = [
    url(r"^ws/api/(?P<api_version>\w+)/$", TaskDirectorConsumer.as_asgi()),
]
