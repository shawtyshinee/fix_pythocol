"""Helpers for attaching readable FIX messages to Allure reports."""

import allure

from .helpers import SOH
from .message import Message


def attach_message(message: Message, name: str) -> None:
    """Attach the message's tag-value fields, preserving their order."""
    text = repr(message).replace(SOH, "\n").rstrip("\n")
    if not message.is_string():
        parties = message.model_dump_parties(use_tag_id=True)
        if parties:
            text += f"\nParty groups: {parties}"
    allure.attach(text, name=name, attachment_type=allure.attachment_type.TEXT)


def attach_messages(messages: list[Message], name: str) -> None:
    """Attach each message separately so every result remains readable."""
    for index, message in enumerate(messages, start=1):
        attach_message(message, f"{name} {index}")
