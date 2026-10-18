import allure

from src.message import Message
from src.allure_reporting import attach_message

__all__ = [
    "IExecutionReportContext"
]



class IExecutionReportContext:
    """Base for customizable execution-report contexts.

    Subclasses implement the state methods and may use ``_update`` to set
    fields. Call the context to retrieve the wrapped Message. Implement the
    ``fullfil`` and ``partial_fill`` aliases explicitly if they are needed.
    """

    def __init__(self, message: Message):
        """Wrap a Message; raise TypeError for other objects."""
        if not isinstance(message, Message):
            raise TypeError("message must be a Message")
        self.message = message

    def __call__(self) -> Message:
        """Return the wrapped Message."""
        with allure.step("Retrieve execution report message"):
            attach_message(self.message, "Execution report message")
            return self.message

    def _update(self, fields=None, **tags):
        """Apply a mapping of tag IDs or names and named keyword fields."""
        if fields is not None or tags:
            self.message.update(dict(fields) if fields is not None else None, **tags)


    def new(self, fields=None, **tags) -> Message:
        """Build a new-order execution report."""
        raise NotImplementedError

    def fulfill(self, fields=None, **tags) -> Message:
        """Build a filled execution report."""
        raise NotImplementedError

    fullfil = fulfill

    def partfill(self, fields=None, **tags) -> Message:
        """Build a partially filled execution report."""
        raise NotImplementedError

    partial_fill = partfill

    def cancel(self, fields=None, **tags) -> Message:
        """Build a canceled-order execution report."""
        raise NotImplementedError

    def reject(self, fields=None, **tags) -> Message:
        """Build a rejected-order execution report."""
        raise NotImplementedError

    def pending_new(self, fields=None, **tags) -> Message:
        """Build a pending-new execution report."""
        raise NotImplementedError

    def pending_cancel(self, fields=None, **tags) -> Message:
        """Build a pending-cancel execution report."""
        raise NotImplementedError

    def pending_replace(self, fields=None, **tags) -> Message:
        """Build a pending-replace execution report."""
        raise NotImplementedError
