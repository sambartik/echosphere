from shared.errors import InvalidPayloadError
from .base_packet import Packet
from .types import PacketType, ResponseType
from .factory import register_packet


@register_packet(PacketType.LOGIN)
class LoginPacket(Packet):
    MAX_PAYLOAD_LENGTH = 256
    
    def __init__(self, username):
        super().__init__(username.encode('utf-8'))

    @property
    def username(self):
        return self.payload.decode('utf-8')

    @classmethod
    def _from_payload(cls, payload):
        username = payload.decode('utf-8')
        return cls(username)


@register_packet(PacketType.HEARTBEAT)
class HeartbeatPacket(Packet):
    MAX_PAYLOAD_LENGTH = 0
    
    def __init__(self):
        super().__init__(b'')

    @classmethod
    def _from_payload(cls, _):        
        return cls()
    
@register_packet(PacketType.RESPONSE)
class ResponsePacket(Packet):
    MAX_PAYLOAD_LENGTH = 1
    
    def __init__(self, response_type):
        super().__init__(bytes([response_type]))
    
    @property
    def response_type(self):
        return ResponseType(int.from_bytes(self.payload))

    @classmethod
    def _from_payload(cls, payload):                
        response_type = int(payload[0])
        return cls(response_type)
    
@register_packet(PacketType.MESSAGE)
class MessagePacket(Packet):
    MAX_PAYLOAD_LENGTH = 4096
    
    def __init__(self, username: str | None, message: str):
        if username is None:
            super().__init__(f"|{message}".encode('utf-8'))
        else:
            super().__init__(f"{username}|{message}".encode('utf-8'))

    @property
    def message(self) -> str:
        return self.payload.decode('utf-8').split("|")[1]

    @property
    def username(self) -> str | None:
        username = self.payload.decode('utf-8').split("|")[0]
        
        return username if username != "" else None

    @classmethod
    def _from_payload(cls, payload):
        try:
            username, message= payload.decode('utf-8').split("|")
        except ValueError:
            raise InvalidPayloadError("Could not unpack the username and message from the payload, sorry!")
        return cls(username, message)
