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
    """
    This class needs to be subclassed to define handlers for different commands. These handler classes need to be
    registered with @register_command_handler class decorator. The only method that needs to be implemented by
    subclasses is handle_command method.
    """

    def __init__(self, server):
        self.server = server

    @abstractmethod
    def handle_command(self, sender: str, args: list[str]):
        """
        This method is called to handle the command sent by the user.

        Parameters:
            sender: The sender of the command
            args: The list of arguments that followed after the command, i.e. for message:
                  /command [arg1] [arg2] [arg3] ... [argN] the args list would have been [arg1, arg2, ..., argN]
        """
        pass


def get_command_handler(server, command: str) -> CommandHandler:
    """
    Returns a CommandHandler instance for the given command.

    Parameters:
        server: The instance of ServrApplication class
        command: The command to be handled

    Raises:
        ValueError: If there is no packet handler registered for the given command
    """
    try:
        handler_class = COMMAND_HANDLER_MAP[command]
        handler = handler_class(server)

        return handler
    except KeyError:
        raise ValueError(f"Invalid command: {command}")


@register_command_handler("list")
class ListCommandHandler(CommandHandler):
    """ Lists the currently logged-in users """
    def handle_command(self, sender: str, args: list[str]):
        response_message = f"Connected users: {', '.join(self.server.connected_users.keys())}"
        self.server.send_message_to(None, sender, response_message)


@register_command_handler("ping")
class PingCommandHandler(CommandHandler):
    """ Pings the server, and it pongs back, in a rather funny way. """
    @staticmethod
    def get_pong_message() -> str:
        """ Returns a random pong message """
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

    def handle_command(self, sender: str, args: list[str]):
        response_message = self.get_pong_message()
        self.server.send_message_to(None, sender, response_message)
