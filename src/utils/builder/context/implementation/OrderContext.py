import allure

from ..interface import IOrderContext
from src.allure_reporting import attach_message
from src.message import Message

__all__ = [
    "OrderContext"
]

class OrderContext(IOrderContext):
    """Build outgoing new-order and cancel requests around a Message.

    Methods accept an optional mapping of tag IDs or names and keyword fields,
    mutate the wrapped message, and return this context. Call the context to
    obtain the message. Supply all fields required by the FIX counterparty.
    """

    def _request(self, msg_type, fields=None, **tags):
        with allure.step(f"Build {'new order' if msg_type == 'D' else 'cancel'} request"):
            self._update(fields, **tags)
            for tag in (39, 150):
                if self.message.get(tag) is not None:
                    self.message.pop(tag)
            self.message.update({35: msg_type})
            attach_message(self.message, "Built order request")
            return self

    def new(self, fields=None, **tags):
        """Build a NewOrderSingle request (MsgType D)."""
        return self._request("D", fields, **tags)

    def cancel(self, fields=None, **tags):
        """Build an OrderCancelRequest (MsgType F)."""
        return self._request("F", fields, **tags)
