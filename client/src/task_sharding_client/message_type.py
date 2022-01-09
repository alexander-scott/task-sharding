import enum


class MessageType(int, enum.Enum):
    INIT = 1
    BUILD_INSTRUCTION = 2
    STEP_COMPLETE = 3
    SCHEMA_COMPLETE = 4
    ABORT_STEP = 5
