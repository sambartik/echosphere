import asyncio
from datetime import datetime, timedelta

from shared.errors import ConnectionClosedError
from shared.chat_protocol import ChatProtocol
from shared.utils.event_emitter import EventEmitter
from shared.validators import valid_message, valid_username
from shared.packets.definitions import *


class Connection:
    """ Represents a client connection to the server and stores related metadata. """

    def __init__(self, protocol, username=None):
        self.protocol = protocol
        self.username = username
        self.connection_time = datetime.now()
        self.last_heartbeat = None

    def is_alive(self):
        if self.username is None:
            raise Exception("The user has not yet logged in to the server.")

        if self.last_heartbeat:
            delta = datetime.now() - self.last_heartbeat
        else:
            delta = datetime.now() - self.connection_time

        if delta <= timedelta(seconds=15):
            return True

        return False


class ServerNetworking(EventEmitter):
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
        print("SERVER: New packet: ", packet)

        if isinstance(packet, LoginPacket):
            if not valid_username(packet.username):
                return protocol.send_packet(ResponsePacket(ResponseCode.INVALID_USERNAME))
            if self.username_is_taken(packet.username):
                return protocol.send_packet(ResponsePacket(ResponseCode.TAKEN_USERNAME))
            if packet.server_password != self.server_password:
                return protocol.send_packet(ResponsePacket(ResponseCode.WRONG_PASSWORD))

            protocol.send_packet(ResponsePacket(ResponseCode.OK))
            self.connections[protocol].username = packet.username
            self.emit("user_joined", protocol, packet.username)
            return

        elif isinstance(packet, MessagePacket):
            # Get the sender's username based on their protocol instance. (each connection has its own)
            sender_username = self.connections[protocol].username
            if not valid_message(packet.message) or sender_username is None:
                return protocol.send_packet(ResponsePacket(ResponseCode.INVALID_MESSAGE))

            protocol.send_packet(ResponsePacket(ResponseCode.OK))
            return self.emit("message_received", sender_username, packet.message)

        elif isinstance(packet, HeartbeatPacket):
            self.connections[protocol].last_heartbeat = datetime.now()

        elif isinstance(packet, LogoutPacket):
            if self.connections[protocol].username is not None:
                self.emit("user_left", protocol, self.connections[protocol].username, None)
                """NOTE: By clearing the username field we mark the user as disconnected and the on_connection_close
                hook won't have to emit another user_left event. This way we can distinguish between normal logouts
                and unexpected connection drops."""
                self.connections[protocol].username = None
                protocol.close_connection()
        else:
            print("SERVER: Unknown packet received, closing the connection.")
            protocol.close_connection()

    def on_new_connection(self, protocol: ChatProtocol):
        self.connections[protocol] = Connection(protocol)
        print("SERVER: New connection!")

    def on_connection_close(self, protocol: ChatProtocol, err: Exception | None):
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
            pass

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
