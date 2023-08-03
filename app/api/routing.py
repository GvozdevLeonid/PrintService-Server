from django.urls import re_path

from api import consumers

websocket_urlpatterns = [
    re_path("api/socket/", consumers.ApiConsumer.as_asgi()),
]
