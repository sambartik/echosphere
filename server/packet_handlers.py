from abc import abstractmethod
from datetime import datetime

from shared.packets import PacketType
from shared.packets import ResponsePacket, ResponseCode, MessagePacket, HeartbeatPacket, LogoutPacket
from shared.chat_protocol import ChatProtocol
from shared.packets import LoginPacket
from shared.packets import Packet
from shared.validators import valid_username, valid_message

"""
    A helper mapping that helps to determine a class from a PacketType. Mainly helps the function packet_factory
    to instantiate the correct class based on a raw packet header.
"""
PACKET_HANDLER_MAP = {}


def register_packet_handler(packet_type: PacketType):
    """
        Use this decorator when defining a new PacketHandler class type.

        Internally, this dynamically sets the PACKET_HANDLER_MAP to an instance of the PacketHandler class.
    """

    def decorator(cls):
        PACKET_HANDLER_MAP[packet_type] = cls
        return cls

    return decorator


class PacketHandler:
    def __init__(self, networking):
        self.networking = networking

    @abstractmethod
    def handle_packet(self, protocol: ChatProtocol, packet: Packet):
        pass


def get_packet_handler(networking, packet: Packet) -> PacketHandler:
    """
        Returns a PacketHandler for the given packet.

        Raises:
            ValueError: If there is no packet handler registered for the given packet
    """
    try:
        handler_class = PACKET_HANDLER_MAP[packet.PACKET_TYPE]
        handler = handler_class(networking)

        return handler
    except ValueError:
        raise ValueError(f"No handler for packet type: {packet.PACKET_TYPE}")


@register_packet_handler(PacketType.LOGIN)
class LoginPacketHandler(PacketHandler):
    def handle_packet(self, protocol: ChatProtocol, packet: LoginPacket):
        if not valid_username(packet.username):
            return protocol.send_packet(ResponsePacket(ResponseCode.INVALID_USERNAME))
        if self.networking.username_is_taken(packet.username):
            return protocol.send_packet(ResponsePacket(ResponseCode.TAKEN_USERNAME))
        if packet.server_password != self.networking.server_password:
            return protocol.send_packet(ResponsePacket(ResponseCode.WRONG_PASSWORD))

        protocol.send_packet(ResponsePacket(ResponseCode.OK))
        self.networking.connections[protocol].username = packet.username
        self.networking.emit("user_joined", protocol, packet.username)


@register_packet_handler(PacketType.MESSAGE)
class MessagePacketHandler(PacketHandler):
    def handle_packet(self, protocol: ChatProtocol, packet: MessagePacket):
        # Get the sender's username based on their protocol instance. (each connection has its own)
        sender_username = self.networking.connections[protocol].username
        if not valid_message(packet.message) or sender_username is None:
            return protocol.send_packet(ResponsePacket(ResponseCode.INVALID_MESSAGE))

        protocol.send_packet(ResponsePacket(ResponseCode.OK))
        return self.networking.emit("message_received", sender_username, packet.message)


@register_packet_handler(PacketType.HEARTBEAT)
class HeartbeatPacketHandler(PacketHandler):
    def handle_packet(self, protocol: ChatProtocol, packet: HeartbeatPacket):
        self.networking.connections[protocol].last_heartbeat = datetime.now()


@register_packet_handler(PacketType.LOGOUT)
class LogoutPacketHandler(PacketHandler):
    def handle_packet(self, protocol: ChatProtocol, packet: LogoutPacket):
        if self.networking.connections[protocol].username is not None:
            self.networking.emit("user_left", protocol, self.networking.connections[protocol].username, None)
            """NOTE: By clearing the username field we mark the user as disconnected and the on_connection_close
            hook won't have to emit another user_left event. This way we can distinguish between normal logouts
            and unexpected connection drops."""
            self.networking.connections[protocol].username = None
            protocol.close_connection()
