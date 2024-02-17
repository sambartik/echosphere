from abc import abstractmethod

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
        raise KeyError(f"Invalid command: {command}")


@register_command_handler("list")
class ListCommandHandler(CommandHandler):
    def handle_command(self, sender: str, message: str):
        response_message = f"Connected users: {self.server.connected_users}"
        self.server.send_message_to(None, sender, response_message)
