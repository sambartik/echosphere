class ServerError(Exception):
    pass


class ServerAlreadyRunning(ServerError):
    pass


class UserNotLoggedIn(ServerError):
    pass
