import logging
import os
import sys
import argparse

# Add the parent directory of the current script to sys.path
sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
###################

import asyncio

from shared.chat_protocol import ChatProtocol
from shared.packets.definitions import *

from server.server_networking import ServerNetworking
from server.command_handlers import get_command_handler


class ServerApplication:
    """
    Essentially implements the server application logic. It is responsible for handling messages sent to the server and
    notifies everyone when a user joins or leaves.
    """

    def __init__(self, networking: ServerNetworking):
        self.networking = networking
        self.connected_users = {}

        networking.on("user_joined", self.on_user_joined)
        networking.on("user_left", self.on_user_left)
        networking.on("message_received", self.on_message_received)

    def on_user_joined(self, protocol: ChatProtocol, username: str):
        """
        An event listener that gets triggered every time a user establishes a connection with the server
        AND successfully logs in.
        """
        logger.info(f"User joined: {username}")
        self.broadcast_message(None, f"User {username} has joined!")
        self.connected_users[username] = protocol

    def on_user_left(self, _protocol: ChatProtocol, username: str, err: Exception | None):
        """
        An event listener that gets triggered every time a user gets disconnected from the server,
        either because of an error, indicated by the err parameter or a regular logout.
        """
        del self.connected_users[username]
        if not err:
            logger.info("User {username} left the chat!")
            self.broadcast_message(None, f"User {username} has left!")
        else:
            logger.info("User {username} left the chat due to an error!")
            self.broadcast_message(None, f"User {username} has lost the connection to the server!")

    def on_message_received(self, _protocol: ChatProtocol, sender: str, message: str):
        """
        An event listener that gets triggered every time any user sends a new message.
        """
        if message.startswith("/"):
            parsed_command = message.strip().split(" ")
            command = parsed_command[0][1:]
            args = parsed_command[1:]

            logger.info(f"Received a command {command}!")

            try:
                command_handler = get_command_handler(self, command)
                logger.debug(f"Handling the new packet with {command_handler}")
                command_handler.handle_command(sender, args)
            except ValueError as e:
                self.send_message_to(None, sender, "Invalid command!")
        else:
            self.broadcast_message(sender, message)

    def broadcast_message(self, sender: str | None, message: str):
        """
        Broadcasts the message to connected users. When a sender is not None, it will broadcast the message as
        a regular user message, leaving out the sender of the message. However, when sender is none, the message
        is treated as a system message that will be sent to every user!

        Parameters:
            sender: The sender of the message, None in case of a system message.
            message: The message to broadcast
        """
        logger.info(f"Broadcasting a message from {sender}")
        for username, protocol in self.connected_users.items():
            if sender is not None and sender == username:
                continue
            protocol.send_packet(MessagePacket(sender, message))

    def send_message_to(self, sender: str | None, recipient: str, message: str):
        """
        Sends a direct message to a user with specified username. When a sender is not None, it will broadcast the
        message as a regular user message. However, when sender is none, the message is treated as a system message,
        that is only visible to the recipient.

        Parameters:
            sender: The sender of the message, None in case of a system
            recipient: The username of recipient of the message.
            message: The message to send
        """
        logger.info(f"Sending direct message from {sender} to {recipient}")
        protocol = self.connected_users[recipient]
        protocol.send_packet(MessagePacket(sender, message))

    async def start(self, port: int, server_password: str | None):
        """
        Starts the server to listen on localhost on specified port. The server will be protected by
        the password passed in the server_password argument. Pass None for no password.
        """
        try:
            await self.networking.serve("localhost", port, server_password)
        except Exception as e:
            logger.error(f"An error occurred in start: {e}")


def configure_server_logging():
    """ Configures server console logging based on environment variables """
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    log_level = log_level_map.get(os.getenv('LOG_LEVEL'), logging.INFO)

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%d-%m-%Y %H:%M:%S"

    logging.basicConfig(level=log_level, format=log_format, datefmt=date_format, handlers=[logging.StreamHandler()])


async def main():
    try:
        parser = argparse.ArgumentParser(description="An EchoSphere Chat Protocol server implementation.")
        parser.add_argument("--port", type=int, help="The port number to listen on.", default=12300, required=False)
        parser.add_argument("--password", type=str,
                            help="The server password that the clients will be required to put in while logging in.",
                            default=None, required=False)

        args = parser.parse_args()

        networking = ServerNetworking()
        app = ServerApplication(networking)

        await app.start(args.port, args.password)
    except asyncio.CancelledError:
        logger.debug("Main task was canceled")
    except BaseException as e:
        logger.error(f"Base exception in main {e}")

    logging.info("Goodbye.")


if __name__ == '__main__':
    configure_server_logging()
    logger = logging.getLogger(__name__)
    asyncio.run(main())
