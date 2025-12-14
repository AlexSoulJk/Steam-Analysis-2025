from enum import Enum


class MessageType(Enum):
    TASK = "task"
    RESULT = "result"
    STATUS = "status"
    REGISTER = "register"
    PING = "ping"
    ERROR = "error"