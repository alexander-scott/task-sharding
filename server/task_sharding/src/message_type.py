import enum


class MessageType(int, enum.Enum):
    INIT = 1
    BUILD_INSTRUCTION = 2
    TASK_COMPLETE = 3
    SCHEMA_COMPLETE = 4
    ABORT_TASK = 5
    WEBSOCKET_CLOSED = 6
