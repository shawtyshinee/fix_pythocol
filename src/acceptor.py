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
    _get_session_settings,
    _wait_session_login
)
from .message import Message

__all__ = [
    "Acceptor"
]


class Acceptor:
    """FIX socket acceptor that listens for an initiator session.

    The acceptor uses QuickFIX and defaults to the project's FIX 4.4 setup
    when callers pass ``"FIX.4.4"``. Incoming application messages can be
    handled with rules or answered with a default message.
    """

    def __init__(self, fix_version: t.Literal['FIX.4.4', 'FIX.5.0', 'FIXT.1.1', 'FIX.4.2'], sender_id: str, target_id: str, port: int, **config):
        self.session = fix.SessionID(fix_version, sender_id, target_id)

        settings = _get_session_settings(
            BeginString=fix_version,
            ConnectionType="acceptor",
            DataDictionary=f"{os.path.dirname(__file__)}/static/{fix_version.replace('.', '')}.xml",
            SocketAcceptPort=port,
            TargetCompID=target_id,
            SenderCompID=sender_id,
            ResetOnLogon='Y',
            **config
        )

        store_factory = fix.FileStoreFactory(settings)
        log_factory = fix.FileLogFactory(settings)

        self._application = Application(fix_version)
        self._acceptor = fix.SocketAcceptor(self._application, store_factory, settings, log_factory)

    def start(self) -> None:
        """Start listening and wait until the configured session logs on."""
        with allure.step("Start acceptor and wait for FIX logon"):
            self._acceptor.start()
            _wait_session_login(self._application.get_session())
            self._application.run()

    def stop(self) -> None:
        """Stop the QuickFIX acceptor and its application worker."""
        with allure.step("Stop acceptor"):
            self._acceptor.stop()
            self._application.stop()

    def add_rule(self, condition: t.Callable[[Message], bool], scenario: t.Callable[[Application, Message], None]) -> None:
        """Register a condition and callback for incoming application messages."""
        with allure.step("Register acceptor response rule"):
            self._application.add_rule_scenario(condition, scenario)

    def add_default_response(self, message: Message) -> None:
        """Set the response sent when no registered rule matches."""
        with allure.step("Register acceptor default response"):
            attach_message(message, "Acceptor default response")
            self._application.add_default_response(message)

    def wait_message(self, message_count: int = 1, timeout: int = 5, condition: t.Callable[[t.List[Message]], bool] = None) -> t.List[Message]:
        """Wait for and return received application messages."""
        with allure.step(f"Acceptor waits for {message_count} application message(s)"):
            sleeping_second = 0.3
            wait_message_iteration = timeout / sleeping_second
            count = itertools.count()
            while next(count) <= wait_message_iteration:
                try:
                    messages = self._application.pop_received_message(message_count)
                    if condition is None or condition(messages):
                        attach_messages(messages, "Acceptor received message")
                        return messages
                    time.sleep(sleeping_second)
                except MessageNotFound:
                    time.sleep(sleeping_second)
            raise MessageNotFound("message not found") # PLACEHOLDER
