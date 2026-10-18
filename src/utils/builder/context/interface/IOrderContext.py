import allure

from src.message import Message
from src.allure_reporting import attach_message

__all__ = [
    "IOrderContext"
]


class IOrderContext:
    """Base for customizable outgoing order-request contexts.

    Subclasses implement ``new`` and ``cancel`` and may use ``_update`` to
    apply tag mappings and keyword fields. Call the context to retrieve its
    wrapped Message. The built-in implementation returns itself from state
    methods, allowing calls such as ``context.new()()``.
    """

    def __init__(self, message: Message):
        """Wrap a Message; raise TypeError for other objects."""
        if not isinstance(message, Message):
            raise TypeError("message must be a Message")
        self.message = message

    def __call__(self) -> Message:
        """Return the wrapped Message."""
        with allure.step("Retrieve order request message"):
            attach_message(self.message, "Order request message")
            return self.message

    def _update(self, fields=None, **tags):
        """Apply a mapping of tag IDs or names and named keyword fields."""
        if fields is not None or tags:
            self.message.update(dict(fields) if fields is not None else None, **tags)

    def new(self, fields=None, **tags) -> Message:
        """Build a new-order request; implement in a subclass."""
        raise NotImplementedError

    def cancel(self, fields=None, **tags) -> Message:
        """Build a cancellation request; implement in a subclass."""
        raise NotImplementedError
