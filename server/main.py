import os
import sys

# Add the parent directory of the current script to sys.path
sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
###################

import asyncio

from shared.chat_protocol import ChatProtocol
from shared.packets.definitions import *

from server.ServerNetworking import ServerNetworking


class ServerApplication:
    def __init__(self, networking: ServerNetworking):
        self.networking = networking
        self.connected_users = {}

        networking.on("user_joined", self.user_joined)
        networking.on("user_left", self.user_left)
        networking.on("message_received", self.broadcast_message)

    def user_joined(self, protocol: ChatProtocol, username: str):
        self.broadcast_message(None, f"User {username} has joined!")
        self.connected_users[username] = protocol

    def user_left(self, protocol: ChatProtocol, username: str, err: Exception):
        del self.connected_users[username]
        self.broadcast_message(None, f"User {username} has left!")

    def broadcast_message(self, sender: str | None, message: str):
        print(f"Broadcasting a message from {sender}")
        for username, protocol in self.connected_users.items():
            if sender is not None and sender == username: continue

            protocol.send_packet(MessagePacket(sender, message))

    async def start(self, port: int, server_password: str | None):
        await self.networking.serve("localhost", port, server_password)


async def main():
    try:
        networking = ServerNetworking()
        app = ServerApplication(networking)

        await app.start(12300, "my_password")
    except asyncio.CancelledError:
        print("Main task was canceled")
    except BaseExceptionGroup as e:
        print("Base exception?", e.exceptions)

    print("Goodbye.")


if __name__ == '__main__':
    asyncio.run(main())
