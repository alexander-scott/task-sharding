from channels.routing import ChannelNameRouter, ProtocolTypeRouter, URLRouter
from task_sharding.routing import channel_name_patterns, websocket_urlpatterns
from task_sharding.src.message_type import MessageType


def create_application():
    return ProtocolTypeRouter(
        {
            "channel": ChannelNameRouter(channel_name_patterns),
            "websocket": URLRouter(websocket_urlpatterns),
        }
    )


def create_default_client_init_message(total_steps=1):
    return {
        "message_type": MessageType.INIT,
        "repo_state": {
            "org/repo_1": {
                "base_ref": "main",
                "patchset": "5bfb44678a27f9bc3b6a96ced8d0b464d7ea9b71",
            }
        },
        "complex_patchset": False,
        "cache_id": "1",
        "total_steps": total_steps,
        "schema_id": "1",
    }


def create_default_build_instruction_message(step_id="0"):
    return {
        "type": "send.message",
        "message_type": MessageType.BUILD_INSTRUCTION,
        "schema_id": "1",
        "step_id": step_id,
    }


def create_default_step_complete_message(step_id="0", step_success=True):
    return {
        "message_type": MessageType.STEP_COMPLETE,
        "schema_id": "1",
        "step_id": step_id,
        "step_success": step_success,
    }


def create_default_schema_complete_message():
    return {
        "type": "send.message",
        "message_type": MessageType.SCHEMA_COMPLETE,
        "schema_id": "1",
    }
