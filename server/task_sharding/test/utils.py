import copy
import json

from channels.layers import get_channel_layer


async def send_message_between_communicators(
    websocket_communicator, application_communicator, message, channel_layer="controller"
):
    await websocket_communicator.send_to(text_data=json.dumps(message))
    await proxy_message_from_channel_to_communicator(channel_layer, application_communicator)


async def proxy_message_from_channel_to_communicator(channel_name: str, communicator: any):
    msg = await get_channel_layer().receive(channel_name)
    await communicator.send_input(copy.deepcopy(msg))


async def prompt_response_from_communicator(
    communicator: any,
    type: str,
    response_key: str = None,
    message: dict = {},
    channel_layer: str = "testing",
):
    message["type"] = type
    message["channel_name"] = channel_layer
    await communicator.send_input(message)
    instances_created_msg = await get_channel_layer().receive(channel_layer)

    if response_key:
        return instances_created_msg[response_key]
    return instances_created_msg
