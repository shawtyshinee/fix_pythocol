import allure

from src.message import Message
from src.allure_reporting import attach_message

__all__ = [
    "build_default_fix_message"
]


def build_default_fix_message(symbol_name: str, quantity: int, 
                              lot_size: int, price: float) -> Message:
    """Create a message with common limit-order fields.

    Args:
        symbol_name: Instrument symbol for tag 55.
        quantity: Number of lots to order.
        lot_size: Number of units per lot; tag 38 is quantity times lot_size.
        price: Limit price for tag 44.

    Returns:
        A mutable Message with Symbol, OrderQty, OrdType, and Price set.

    Raises:
        ValueError: If quantity, lot_size, or price is not positive.

    Add the message type, session, order ID, side, and other fields required
    by the counterparty before sending.
    """
    with allure.step("Build default limit-order fields"):
        if quantity <= 0 or lot_size <= 0 or price <= 0:
            raise ValueError("quantity, lot_size and price must be positive")
        message = Message({55: symbol_name, 38: quantity * lot_size, 40: "2", 44: price})
        attach_message(message, "Default limit-order fields")
        return message

