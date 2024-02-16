from .base_packet import Packet
from .types import PacketType

"""
    A helper mapping that helps to determine a class from a PacketType. Mainly helps the function packet_factory
    to instantiate the correct class based on a raw packet header.
"""
PACKET_CLASS_MAP = {}


def register_packet(packet_type: PacketType):
    """
        Use this decorator when defining a new Packet class type.
    
        Internally, this dynamically sets the PACKET_TYPE class attribute and sets a mapping in
        PACKET_CLASS_MAP accordingly so the user does not have to. For more info check PACKET_CLASS_MAP. 
    """

    def decorator(cls):
        PACKET_CLASS_MAP[packet_type] = cls
        cls.PACKET_TYPE = packet_type
        return cls

    return decorator


def packet_factory(buffer: bytes):
    """
    Factory function to create and return a specific instance of Packet subclass and its length in bytes from a
    buffer of data. Only the first packet found in the buffer is returned. To get the rest of the packets,
    call it with a smaller buffer.
    
    Returns:
        If raw_data includes a valid Packet: (Packet, int) otherwise (None, None)
        
    Raises:
        UnknownPacketError: if the buffer does not contain a valid packet at the start.
        InvalidPayloadError: If packet cant be reconstructed from the payload or if it exceeds the max length.
        BaseProtocolError: A generic error has occurred during the packet reconstruction.
        
    Args:
        buffer: A buffer containing a raw packet data.
    """
    if len(buffer) >= Packet.HEADER_SIZE:
        packet_type, length = Packet.deserialize_header(buffer[:Packet.HEADER_SIZE])
        total_packet_size = Packet.HEADER_SIZE + length
        payload = buffer[Packet.HEADER_SIZE:total_packet_size]

        if len(payload) >= length:
            packet_class = PACKET_CLASS_MAP.get(packet_type, Packet)
            return packet_class.from_payload(payload), total_packet_size

    return None, None
