import os
from abc import abstractmethod
import random

"""
    A helper mapping that helps to determine a class from a command. Mainly helps the function get_command_handler
    to return the appropriate command handler
"""
COMMAND_HANDLER_MAP = {}


def register_command_handler(command: str):
    """
        Use this decorator when defining a new CommandHandler class type.

        Internally, this dynamically sets a command as a key in COMMAND_HANDLER_MAP map to value of a respective
        command handler class
    """

    def decorator(cls):
        COMMAND_HANDLER_MAP[command] = cls
        return cls

    return decorator


class CommandHandler:
    def __init__(self, server):
        self.server = server

    @abstractmethod
    def handle_command(self, sender: str, message: str):
        pass


def get_command_handler(server, command: str) -> CommandHandler:
    """
        Returns a PacketHandler for the given packet.

        Raises:
            ValueError: If there is no packet handler registered for the given packet
    """
    try:
        handler_class = COMMAND_HANDLER_MAP[command]
        handler = handler_class(server)

        return handler
    except KeyError:
        raise ValueError(f"Invalid command: {command}")


@register_command_handler("list")
class ListCommandHandler(CommandHandler):
    def handle_command(self, sender: str, message: str):
        response_message = f"Connected users: {', '.join(self.server.connected_users.keys())}"
        self.server.send_message_to(None, sender, response_message)

@register_command_handler("ping")
class PingCommandHandler(CommandHandler):
    def get_pong_message(self) -> str:
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        pong_messages_path = os.path.join(current_script_dir, "pong_messages.txt")
        
        # Choosing a random line, using Reservoir sampling, check out: https://en.wikipedia.org/wiki/Reservoir_sampling
        # and/or the first 5 minutes of https://www.youtube.com/watch?v=Ybra0uGEkpM
        random_message = ""
        processed_lines = 0
        with open(pong_messages_path, "r") as f:
            for line in f:
                processed_lines += 1
                if random.randrange(processed_lines) == 0:
                    random_message = line
        return random_message.strip()
    
    def handle_command(self, sender: str, message: str):
        response_message = self.get_pong_message()
        self.server.send_message_to(None, sender, response_message)