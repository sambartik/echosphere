import asyncio
from datetime import datetime, timedelta

from server.errors import UserNotLoggedIn
from packet_handlers import get_packet_handler
from shared.errors import ConnectionClosedError
from shared.chat_protocol import ChatProtocol
from shared.utils.event_emitter import EventEmitter
from shared.packets.definitions import *


class Connection:
    """ Represents a client connection to the server and stores related metadata. """

    def __init__(self, protocol, username=None):
        self.protocol = protocol
        self.username = username
        self.connection_time = datetime.now()
        self.last_heartbeat = None

    def is_alive(self) -> bool:
        """
            Checks if the logged-in user is still connected to the server.

            Raises:
                UserNotLoggedIn: If the user is not logged in
                ConnectionClosedError: If the connection is already closed
        """
        if self.username is None:
            raise UserNotLoggedIn("The user has not yet logged in to the server.")
        if not self.protocol.is_connected:
            raise ConnectionClosedError("The connection to the user has already been closed!")

        if self.last_heartbeat:
            delta = datetime.now() - self.last_heartbeat
        else:
            delta = datetime.now() - self.connection_time

        if delta <= timedelta(seconds=15):
            return True

        return False


class ServerNetworking(EventEmitter):
    """
        This class emits following events:
            - user_joined (protocol: ChatProtocol, username: str)
            - user_left (protocol: ChatProtocol, username: str)
            - message_received (protocol: ChatProtocol, username: str, message: str)
    """
    def __init__(self):
        EventEmitter.__init__(self, events=["user_joined", "user_left", "message_received"])
        self.server = None
        self.heartbeat_monitor_task = None
        self.server_password = None
        self.connections = {}

    def username_is_taken(self, username: str):
        """ Checks if the username is already taken by one of the connected clients. """
        for connection in self.connections.values():
            if connection.username == username:
                return True
        return False

    def on_new_packet(self, protocol: ChatProtocol, packet: Packet):
        """
            An event listener that is triggered every time a server receives a new packet from client
        """
        print("SERVER: New packet: ", packet)

        try:
            handler = get_packet_handler(self, packet)
            handler.handle_packet(protocol, packet)
        except ValueError:
            print("SERVER: Unknown packet received, closing the connection.")
            protocol.close_connection()
        except Exception as e:
            print("An unexpected error occurred while handling packet: ", e)
            protocol.close_connection()

    def on_new_connection(self, protocol: ChatProtocol):
        """
            An event listener that is triggered every time a connection is estabilished with the server
        """
        self.connections[protocol] = Connection(protocol)
        print("SERVER: New connection!")

    def on_connection_close(self, protocol: ChatProtocol, err: Exception | None):
        """
            An event listener that is triggered every time a connection is closed or lost due to an error
        """
        if self.connections[protocol].username:
            err = err or ConnectionClosedError("The connection was closed unexpectedly!")
            self.emit("user_left", protocol, self.connections[protocol].username, err)
        del self.connections[protocol]
        print(f"SERVER: Connection closed (err: {err})")

    def accept_connection(self) -> ChatProtocol:
        protocol = ChatProtocol()
        protocol.on("connection_made", self.on_new_connection)
        protocol.on("packet_received", self.on_new_packet)
        protocol.on("connection_lost", self.on_connection_close)
        return protocol

    async def monitor_heartbeats(self, interval: int = 15):
        """ Periodically checks the heartbeats of all the connected users and finds the dead ones among them. """
        try:
            while True:
                for connection in self.connections.values():
                    if connection.username and not connection.is_alive():
                        print(f"SERVER: The connection of user {connection.username} is dead, cleaning up...")
                        self.emit("user_left", connection.protocol, connection.username,
                                  ConnectionClosedError("The connection to the client was lost!"))
                        connection.username = None
                        connection.protocol.close_connection()
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            self.heartbeat_monitor_task = None

    async def serve(self, host: str, port: int, server_password: str | None):
        """ Starts the server and listens for incoming connections. """
        if self.server:
            raise Exception("Server is already running!")

        try:
            self.server_password = server_password
            self.server = await asyncio.get_event_loop().create_server(self.accept_connection, host, port)
            print(f"Server started listening on {host}:{port}.")
            self.heartbeat_monitor_task = asyncio.create_task(self.monitor_heartbeats())
            await self.server.serve_forever()
        except Exception as e:
            print(f"An error occurred while serving: {e}")
        finally:
            self.stop_server()

    def stop_server(self):
        """ Stops the server and cleans up. """
        if self.server:
            self.server.close()
            self.server = None
            self.connections = {}
        if self.heartbeat_monitor_task:
            self.heartbeat_monitor_task.cancel()
            self.heartbeat_monitor_task = None
