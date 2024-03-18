import re


def valid_username(username: str) -> bool:
    """ Validates the username based on protocol spec. """
    return (3 <= len(username) <= 12) and re.fullmatch(r'[a-zA-Z0-9]+', username)


def valid_message(message: str) -> bool:
    """ Validates the message based on protocol spec. """
    return 1 <= len(message) <= 1000
