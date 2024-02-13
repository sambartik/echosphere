from shared.errors import NetworkError


class DestinationUnreachable(NetworkError):
  pass

class ApplicationError(Exception):
  pass

class LoginError(ApplicationError):
  pass

class InvalidUsernameError(LoginError):
  pass

class UsernameTakenError(LoginError):
  pass

class WrongPasswordError(LoginError):
  pass

class MessageError(ApplicationError):
  pass