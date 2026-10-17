__all__ = [
    "SocketConnectionError",
    "MessageNotFound"
]

class SocketConnectionError(Exception):
    pass

class MessageNotFound(Exception):
    pass