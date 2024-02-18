from shared.errors import NetworkError


class DestinationUnreachable(NetworkError):
    """ Raised when trying to communicate with an endpoint that is unreachable over the network """
    pass


class ApplicationError(Exception):
    """ Raised for general application errors """
    pass


class LoginError(ApplicationError):
    """ Raised for errors during login """
    pass


class InvalidUsernameError(LoginError):
    """ Raised for invalid username """
    pass


class UsernameTakenError(LoginError):
    """ Raised when trying to login with a username that has already been taken """
    pass


class WrongPasswordError(LoginError):
    """ Raised when trying to login with a wrong password to a protected server """
    pass


class MessageError(ApplicationError):
    """ Raised when there is a problem with the message trying to send to. Either because it is invalid or the server
    rejected it from a different reason"""
    pass
