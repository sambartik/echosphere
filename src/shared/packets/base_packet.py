import struct
from abc import ABC, abstractmethod
from typing import Tuple

from shared.errors import IncompleteHeaderError, InvalidPayloadError, BaseProtocolError, UnknownPacketError

from .types import PacketType


class Packet(ABC):
    """
    This class represents an arbitrary packet of EchoSphere Chat Protocol. Each packet must be a subclass of this class,
    define the MAX_PAYLOAD_LENGTH variable and PACKET_TYPE. The latter variable is automatically set after packet
    registration via a class decorator @register_packet.

    Subclasses need to implement the _from_payload class method.
    """
    # Defined by each packet type:
    PACKET_TYPE = None
    MAX_PAYLOAD_LENGTH = None

    # Shared across different packet types:
    HEADER_FORMAT = '>BBH'  # Format (BE): Protocol version (1 byte), PacketType (1 byte), Length (2 bytes)
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, payload: bytes = b''):
        """
        Creates a new instance of Packet based on the payload.
        
        Raises
            InvalidPayloadError: If payload exceeds max. payload size for the packet.
        """
        # TODO: Implement a more thorough validation that lets different packet types hook in for additional
        #  requirements.
        if len(payload) > self.MAX_PAYLOAD_LENGTH:
            raise InvalidPayloadError(
                f"Invalid payload for this packet, exceeds max length. Expected at most {self.MAX_PAYLOAD_LENGTH}B, got {len(payload)}B. Sorry.")

        self.payload = payload
        self.header = struct.pack(self.HEADER_FORMAT, 1, self.PACKET_TYPE, len(self.payload))

    def serialize(self) -> bytes:
        """
        Serializes the Packet instance into bytes
        
        Returns:
            bytes
        """
        return self.header + self.payload

    @classmethod
    def deserialize_header(cls, raw_data: bytes) -> Tuple[PacketType, int]:
        """
        Unpacks the first packet header from a sequence of bytes.
            
        Parameters:
            raw_data: Not necessarily entire packet, but a byte sequence that includes the packet header at the start
        Raises:
            IncompleteHeaderError: If raw_data does not contain a full header length of data
            UnknownPacketError: If protocol type in the header is unknown
        Returns:
            A tuple: packet type and its payload's length
        """
        if len(raw_data) < cls.HEADER_SIZE:
            raise IncompleteHeaderError(
                f"The data do not contain a header of a valid length. Expected at least {cls.HEADER_SIZE}B, got {len(raw_data)}B. Sorry.")

        version, packet_type, payload_length = struct.unpack(cls.HEADER_FORMAT, raw_data[:cls.HEADER_SIZE])
        try:
            packet_type = PacketType(packet_type)
        except ValueError:
            raise UnknownPacketError(f"The header contains an unknown packet type: {hex(packet_type)}")

        return packet_type, payload_length

    @classmethod
    @abstractmethod
    def _from_payload(cls, payload: bytes):
        """
        An (internal/protected) abstract method for constructing a packet instance from a given payload.
        This method must be implemented by all subclasses of Packet.
        
        If the payload cant be reconstructed from the given payload, raise an InvalidPayloadError exception.
        
        Note: this method is called by the public from_payload method. Payload max length
        is automatically enforced by that method and implementation of this method does the rest.
        
        Raises:
            InvalidPayloadError: If the payload is not valid and the packet can't be reconstructed from that.
        """
        pass

    @classmethod
    def from_payload(cls, payload: bytes):
        """
        Get a packet instance from provided payload.

        Verifies that the payload length is within the maximum limit and then 
        processes it using the subclass-specific '_from_payload' method.

        Parameters:
            payload: Payload data for the packet.

        Returns:
            Packet: Instance of a specific packet subclass.

        Raises:
            InvalidPayloadError: If packet cant be reconstructed from the payload or if it exceeds the max length.
            BaseProtocolError: A generic error has occurred during the packet reconstruction.
        """
        if len(payload) > cls.MAX_PAYLOAD_LENGTH:
            raise InvalidPayloadError(
                f"Invalid payload for this packet, exceeds max length. Expected at most {cls.MAX_PAYLOAD_LENGTH}B, got {len(payload)}B. Sorry.")
        try:
            return cls._from_payload(payload)
        except Exception as e:
            raise BaseProtocolError(
                f"Something went wrong during the packet reconstruction from payload, sorry.") from e
