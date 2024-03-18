from shared.errors import InvalidPayloadError
from .base_packet import Packet
from .types import PacketType, ResponseCode
from .factory import register_packet


@register_packet(PacketType.HEARTBEAT)
class HeartbeatPacket(Packet):
    MAX_PAYLOAD_LENGTH = 0

    def __init__(self):
        super().__init__(b'')

    @classmethod
    def _from_payload(cls, _):
        return cls()


@register_packet(PacketType.LOGIN)
class LoginPacket(Packet):
    MAX_PAYLOAD_LENGTH = 256

    def __init__(self, username: str, server_password: str | None):
        super().__init__(f"{username}|{server_password or ''}".encode('utf-8'))
        self.username = username
        self.server_password = server_password

    @classmethod
    def _from_payload(cls, payload):
        try:
            username, server_password = payload.decode('utf-8').split("|")
            if server_password == "": server_password = None
        except ValueError:
            raise InvalidPayloadError("Could not unpack the username and the server password from the payload, sorry!")
        return cls(username, server_password)


@register_packet(PacketType.MESSAGE)
class MessagePacket(Packet):
    MAX_PAYLOAD_LENGTH = 4096

    def __init__(self, username: str | None, message: str):
        """
            User messages have a valid username, whereas system messages have the username empty, i.e. set to None.
        """
        super().__init__(f"{username or ''}|{message}".encode('utf-8'))
        self.username = username
        self.message = message

    @classmethod
    def _from_payload(cls, payload):
        try:
            username, message = payload.decode('utf-8').split("|")
            if username == "": username = None
        except ValueError:
            raise InvalidPayloadError("Could not unpack the username and message from the payload, sorry!")
        return cls(username, message)


@register_packet(PacketType.RESPONSE)
class ResponsePacket(Packet):
    MAX_PAYLOAD_LENGTH = 1

    def __init__(self, response_code: ResponseCode):
        super().__init__(bytes([response_code]))
        self.response_code = response_code

    @classmethod
    def _from_payload(cls, payload):
        try:
            response_code = ResponseCode(int.from_bytes(payload, byteorder="big"))
            return cls(response_code)
        except ValueError:
            raise InvalidPayloadError("The payload of Response packet contains an invalid response code, sorry!")


@register_packet(PacketType.LOGOUT)
class LogoutPacket(Packet):
    MAX_PAYLOAD_LENGTH = 0

    def __init__(self):
        super().__init__(b'')

    @classmethod
    def _from_payload(cls, _):
        return cls()
