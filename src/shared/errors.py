class BaseProtocolError(Exception):
    """ A general error raised for errors that occur while handling/parsing raw binary data. """
    pass


class UnknownPacketError(BaseProtocolError):
    """ Raised when received an unknown (invalid) packet type. """
    pass


class InvalidPayloadError(BaseProtocolError):
    """ Raised when passing an invalid payload that does not conform to the packet spec. """
    pass


class IncompleteHeaderError(BaseProtocolError):
    """ Raised when the packet header is incomplete """
    pass


class NetworkError(Exception):
    """ A general error raised for errors that occur during network communication """
    pass


class ConnectionClosedError(NetworkError):
    """ Raised when trying to access a closed connection or the connection was closed unexpectedly """
    pass
