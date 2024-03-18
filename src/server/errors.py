class ServerError(Exception):
    """ Raised for general server errors """
    pass


class ServerAlreadyRunning(ServerError):
    """ Raised when trying to start a server that is already running """
    pass


class UserNotLoggedIn(ServerError):
    """ Raised when performing an action, where login is required """
    pass
