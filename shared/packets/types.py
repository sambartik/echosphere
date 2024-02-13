from enum import IntEnum

# These enum types correspond to different types as defined in the protocol specification (look at protocol.md)
class PacketType(IntEnum):
    HEARTBEAT = 1
    LOGIN = 2
    MESSAGE = 3
    RESPONSE = 4
    LOGOUT = 5

class ResponseType(IntEnum):
    OK = 0
    INVALID_USERNAME = 1
    TAKEN_USERNAME = 2
    INVALID_MESSAGE = 3
    GENERIC_ERROR = 4