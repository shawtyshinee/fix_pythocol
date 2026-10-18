import itertools
import os
import time
import typing as t

import allure
import quickfix as fix

from .application import Application
from .allure_reporting import attach_message, attach_messages
from .exception import MessageNotFound
from .helpers import (
    SOH,
    _get_session_dictionary,
    _wait_session_login
)
from .message import Message

__all__ = [
    "Initiator"
]


class Initiator:
    """FIX socket initiator that connects to an :class:`Acceptor` session.

    Messages sent through this object receive the FIX header fields required
    by the configured session when those fields are not already present.
    """

    def __init__(self, fix_version: t.Literal['FIX.4.4', 'FIX.5.0', 'FIXT.1.1', 'FIX.4.2'], 
                 sender_id: str, target_id: str, port: int, host: str = "0.0.0.0", **config):
        settings = fix.SessionSettings(f"{os.path.dirname(__file__)}/fix.default.cfg")
        self.session = fix.SessionID(fix_version, sender_id, target_id)

        dictionary = _get_session_dictionary(
            BeginString=fix_version,
            ConnectionType="initiator",
            DataDictionary=f"{os.path.dirname(__file__)}/static/{fix_version.replace('.', '')}.xml",
            SocketConnectHost=host,
            SocketConnectPort=port,
            TargetCompID=target_id,
            SenderCompID=sender_id,
            **config
        )

        settings.set(self.session, dictionary)
        store_factory = fix.FileStoreFactory(settings)
        log_factory = fix.FileLogFactory(settings)

        self._application = Application(fix_version)
        self._initiator = fix.SocketInitiator(self._application, store_factory, settings, log_factory)

    def __wait_application_message(self, pop_message: t.Callable[[int], t.List[Message]], message_count: int = 1, timeout: int = 5, 
                                   condition: t.Callable[[t.List[Message]], bool] = None) -> t.List[Message]:
        sleeping_second = 0.3
        wait_message_iteration = timeout / sleeping_second
        count = itertools.count()
        while next(count) <= wait_message_iteration:
            try:
                messages = pop_message(message_count)
                if condition is not None and condition(messages):
                    return messages
                elif condition is None:
                    return messages
                time.sleep(sleeping_second)
            except MessageNotFound:
                time.sleep(sleeping_second)
        raise MessageNotFound("message not found") # PLACEHOLDER

    def start(self) -> None:
        """Start the initiator and wait until the session logs on."""
        with allure.step("Start initiator and wait for FIX logon"):
            self._initiator.start()
            _wait_session_login(self._application.get_session())

    def stop(self) -> None:
        """Stop the QuickFIX initiator."""
        with allure.step("Stop initiator"):
            self._initiator.stop()

    def send(self, message: Message) -> None:
        """Send a domain message to the connected acceptor."""
        with allure.step("Send FIX message from initiator"):
            if not message.is_string():
                __required_field_tag_ids = {
                    8: str(self.session.getBeginString()).split("=")[1].replace(SOH, ''),
                    49: str(self.session.getSenderCompID()).split("=")[1].replace(SOH, ''),
                    56: str(self.session.getTargetCompID()).split("=")[1].replace(SOH, '')
                }
                for key, value in __required_field_tag_ids.items():
                    if key not in message.model_dump(use_tag_id=True).keys():
                        message.update({key: value})

            attach_message(message, "Initiator outgoing message")
            self._application.send(message)

    def wait_message(self, message_count: int = 1, timeout: int = 5, 
                     condition: t.Callable[[t.List[Message]], bool] = None) -> t.List[Message]:
        """Wait for and return received application messages."""
        with allure.step(f"Initiator waits for {message_count} application message(s)"):
            messages = self.__wait_application_message(
                self._application.pop_received_message, message_count,
                timeout, condition
            )
            attach_messages(messages, "Initiator received application message")
            return messages

    def wait_admin_message(self, message_count: int = 1, timeout: int = 5, 
                           condition: t.Callable[[t.List[Message]], bool] = None) -> t.List[Message]:
        """Wait for and return received administrative messages."""
        with allure.step(f"Initiator waits for {message_count} administrative message(s)"):
            messages = self.__wait_application_message(
                self._application.pop_received_admin_message, message_count,
                timeout, condition
            )
            attach_messages(messages, "Initiator received administrative message")
            return messages
