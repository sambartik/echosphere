import asyncio
import logging
import socket

from client.errors import InvalidUsernameError, DestinationUnreachable, LoginError, MessageError, UsernameTakenError, \
    WrongPasswordError
from shared.chat_protocol import ChatProtocol
from shared.errors import ConnectionClosedError, NetworkError
from shared.packets.definitions import LoginPacket, HeartbeatPacket, MessagePacket, LogoutPacket
from shared.packets.types import ResponseCode
from shared.utils.event_emitter import EventEmitter

logger = logging.getLogger(__name__)


class ClientNetworking(EventEmitter):
    """
    The class emits following events:
    - message_received (username: str | None, message: str): When a new message packet is received from the server
    - connection_lost (err: Exception | None): When a connection is closed *unexpectedly* because of an error or the other side closed its end.
    """

    def __init__(self):
        EventEmitter.__init__(self, events=["message_received", "connection_lost"])
        self.connection = None
        self.heartbeat_task = None
        self.username = None

    def on_new_packet(self, _, packet):
        logger.debug(f"Received a new packet: {packet}")
        if isinstance(packet, MessagePacket):
            self.emit("message_received", packet.username, packet.message)

    def on_connection_lost(self, _, err: Exception | None):
        if err:
            logger.error(f"Connection lost because an error occurred: {err}")
        else:
            logger.debug(f"Connection lost")
        # In case we did not call disconnect beforehand, the connection drop was unexpected.
        if self.connection:
            self.emit("connection_lost",
                      err or ConnectionClosedError("The connection was closed by the server unexpectedly."))
            self.disconnect()

    def disconnect(self):
        """
          Disconnects from the currently joined server. If there is no active connection, the call is silently ignored.

          Raises:
            NetworkError: If any error occurs during the disconnection.
        """
        if not self.connection:
            return None
        try:
            logger.info(f"Disconnecting from the server.")

            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                self.heartbeat_task = None

            # The connection was not closed prior calling disconnect, i.e. by the other end or because of an error.
            # Send logout packet.
            if not self.connection[0].is_closing():
                logger.debug("Sending a close packet...")
                self.connection[1].send_packet(LogoutPacket())
                logger.debug("Closing the connection...")
                self.connection[0].close()
            self.connection = None
            self.username = None
        except Exception as e:
            logger.error(f"Could not disconnect from the server, received an error: {e}")
            raise NetworkError("There was an error when disconnecting from the server, sorry.")

    async def join_server(self, host: str, port: int, username: str, server_password: str | None):
        """
          Connects to a server with the username provided. After the connection is made, it is non-blocking.

          Raises:
            Exception: If already connected to the server
            DestinationUnreachable: If the host can't be reached.
            InvalidUsernameError: If the username is already taken
            WrongPasswordError: If the login is rejected because of incorrect server password provided.
            LoginError: When the server rejects the login because of a different reason
        """

        if self.connection and not self.connection[1].is_closed:
            raise Exception("Already connected to a server.")

        try:
            logger.info(f"Joining a server {host}:{port} with the username {username}")
            self.connection = await asyncio.get_running_loop().create_connection(lambda: ChatProtocol(), host, port)

            # Set up event listeners
            protocol = self.connection[1]
            protocol.on("packet_received", self.on_new_packet)
            protocol.on("connection_lost", self.on_connection_lost)

            await self._login(username, server_password)
            self.heartbeat_task = asyncio.create_task(self._send_heartbeat_periodically(), name="Heartbeat")
        except asyncio.CancelledError:
            logger.debug("join_server task cancelled.")
            self.disconnect()
        except (OSError, socket.gaierror, ConnectionError) as e:
            logger.debug(f"Received a connection error while reaching the host: {e}")
            self.disconnect()
            raise DestinationUnreachable(f"The destination {host}:{port} is unreachable, sorry.")

    async def _login(self, username: str, server_password: str | None):
        """
          Initiates a login request with the currently connected server.

          Raises:
            ConnectionClosedError: If there is no active connection with a server
            InvalidUsernameError: If the username is already taken
            WrongPasswordError: If the server password is incorrect
            LoginError: When the server rejects the login because of a different reason
        """

        if not self.connection or self.connection[1].is_closed:
            raise ConnectionClosedError("Not connected to a server.")

        logger.debug("Sending a login packet to the server")
        response = await self.connection[1].send_packet_and_wait(LoginPacket(username, server_password))
        logger.debug(f"Received a response: {response}")
        if response.response_code == ResponseCode.INVALID_USERNAME:
            raise InvalidUsernameError("The username is invalid, try a different one, sorry!")
        elif response.response_code == ResponseCode.TAKEN_USERNAME:
            raise UsernameTakenError("The username you have specified is already taken, try another one, sorry!")
        elif response.response_code == ResponseCode.WRONG_PASSWORD:
            raise WrongPasswordError("The server password provided is incorrect, sorry!")
        elif response.response_code != ResponseCode.OK:
            raise LoginError("There was an issue logging in to the server, sorry!")

        self.username = username

    async def send_message(self, message: str):
        """
          Sends the message to the server to be broadcaster to everyone else.

          Raises:
            ConnectionClosedError: If there is no active connection with a server
            NetworkError: If message can't be sent because of a network error
            MessageError: If the message was rejected by the server
        """

        if not self.connection or self.connection[1].is_closed:
            raise ConnectionClosedError("Not connected to a server.")

        logger.debug("Sending a message packet...")
        response = await self.connection[1].send_packet_and_wait(MessagePacket(self.username, message))
        logger.debug(f"Received a response: {response}")
        if response.response_code != ResponseCode.OK:
            raise MessageError(f'The message was rejected by the server: "{message}"')

    async def _send_heartbeat_periodically(self, interval: int = 15):
        """
          Maintains the heartbeat with the server. The heartbeat is meant to start after a successful login.

          Raises:
            ConnectionClosedError: If there is no active connection with a server
        """
        if not self.connection or self.connection[1].is_closed:
            raise ConnectionClosedError("Not connected to a server.")

        heartbeat_packet = HeartbeatPacket()
        try:
            while not self.connection[1].is_closed:
                logger.debug("Sending a heartbeat packet")
                self.connection[1].send_packet(heartbeat_packet)
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.debug("Heartbeat task cancelled.")
            self.heartbeat_task = None
        except NetworkError as err:
            logger.error(f"An error occurred while sending a heartbeat: {err}")
            self.disconnect()
            self.emit("connection_lost", err)
