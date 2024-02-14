import asyncio
from collections import deque
from typing import Optional
from shared.errors import BaseProtocolError, ConnectionClosedError, NetworkError
from shared.packets import Packet, ResponsePacket, packet_factory
from shared.utils.event_emitter import EventEmitter


class ChatProtocol(asyncio.Protocol, EventEmitter):
    """
    An implementation of asyncio.Protocol along with additional helper methods.
    It inherits methods from shared.utils.EventEmitter and defines following events:
      - packet_received (protocol: ChatProtocol, packet: Packet): When a new packet was received from the server
      - connection_made (protocol: ChatProtocol): When a connection was made.
      - connection_lost (protocol: ChatProtocol, err: Exception | None): When a connection was lost or closed.

    For information how to subscribe to an event, please check shared.utils.EventEmitter.
    """

    def __init__(self):
        asyncio.Protocol.__init__(self)
        EventEmitter.__init__(self, events=["packet_received", "connection_made", "connection_lost"])

        self._closed_event = asyncio.Event()
        self._closed_event.set()
        self._error = None
        self._future_responses = deque()
        self.transport = None
        self.buffer = None

    ### asyncio.Protocol interface:
    def connection_made(self, transport: asyncio.BaseTransport):
        self.transport = transport
        self.buffer = bytearray()
        self._closed_event.clear()
        self.emit("connection_made", self)

    def data_received(self, data: bytes):
        self.buffer += data

        try:
            next_packet = packet_factory(self.buffer)
            while next_packet != (None, None):
                packet, length = next_packet

                if isinstance(packet, ResponsePacket):
                    self._resolve_next_response(None, packet)
                self.emit("packet_received", self, packet)

                self.buffer = self.buffer[length:]
                next_packet = packet_factory(self.buffer)
        except BaseProtocolError as e:
            self._error = e
            self.transport.close()

    def eof_received(self):
        return False  #  Closes the connection

    def connection_lost(self, err):
        self._closed_event.set()
        if self._error:
            self.emit("connection_lost", self, self._error)
            while self._future_responses:
                self._resolve_next_response(self._error)
        else:
            self.emit("connection_lost", self, err)
            while self._future_responses:
                if err is None:
                    self._resolve_next_response(ConnectionClosedError("The connection was closed."))
                else:
                    self._resolve_next_response(err)

    ### Custom interface:
    @property
    def is_closed(self):
        return self._closed_event.is_set()

    async def wait_until_closed(self):
        return await self._closed_event.wait()

    def close_connection(self):
        """
            Closes the connection, if it has been established. Otherwise, it will ignore the call.
        """
        if self.transport and not self.transport.is_closing():
            self.transport.close()

    def send_packet(self, packet: Packet):
        """
          Sends a packet to the other end without waiting.

          Raises:
            ConnectionClosedError: If the connection was already closed.
            NetworkError: If an error occurs during the packet transmission.
        """
        if self.is_closed:
            raise ConnectionClosedError("Cant send packet, the connection is closed, sorry.")
        try:
            self.transport.write(packet.serialize())
        except Exception as e:
            raise NetworkError("Something unexpected happened while sending a packet, sorry.") from e

    async def send_packet_and_wait(self, packet: Packet) -> ResponsePacket:
        """
          Sends a packet to the other end and waits for a next response packet.

          Raises:
            ConnectionClosedError: If the connection was already closed.
            NetworkError: If something unexpected happened during while waiting for response packet.
        """
        if self.is_closed:
            raise ConnectionClosedError("Cant send packet, the connection is closed, sorry.")

        future_response = asyncio.Future()
        self._future_responses.append(future_response)

        self.send_packet(packet)

        return await future_response

    def _resolve_next_response(self, err: Optional[BaseException], result=None):
        """
          Resolves the next response future from the queue with either an error or a result.

          Parameters:
            err: An exception to be set on the next response future.
            result: A result that the response future will be set to. Ignored when err parameter is not None.

          If the futures queue is empty, this call will ignore the call and won't raise any errors.
        """
        if not self._future_responses: return

        future = self._future_responses.popleft()
        if not future.cancelled():
            if err is not None:
                future.set_exception(err)
            else:
                future.set_result(result)
