import os
import threading
import time
import typing as t

import quickfix as fix

from .exception import MessageNotFound
from .helpers import (
    TAGS_HEADERS_44_LIST,
    TAGS_HEADERS_50_LIST,
    TAGS_HEADERS_T11_LIST,
    PARTIES_TAG_LIST,
    PARTY_TAG_COUNT,
    _message_set_field
)
from .message import Message

__all__ = [
    "Application"
]


class Application(fix.Application):
    def __init__(self, fix_version: t.Literal['FIX.4.4', 'FIX.5.0', 'FIXT.1.1', 'FIX.4.2']):
        super().__init__()
        self.fix_version = fix_version
        self.session_id = None
        self.received_messages_stack = []
        self.receieved_admin_messages_stack = []
        self.scenario_rule_container = {}
        self.default_response: t.Optional[Message] = None
        self.run_event = threading.Event()

    def _fix_to_domain_message(self, message: fix.Message) -> Message:
        return Message(from_string=message.toString())

    def _domain_to_fix_message(self, message: Message, kwargs: t.MutableMapping = None) -> fix.Message:
        if message.is_string():
            data_dictionary = fix.DataDictionary(f"{os.path.dirname(__file__)}/static/{self.fix_version.replace('.', '')}.xml")
            fix_message = fix.Message(repr(message), data_dictionary, True)
            return fix_message
        
        if kwargs is not None:
            message_dict = {**kwargs, **message.model_dump(use_tag_id=True)}
        else:
            message_dict = message.model_dump(use_tag_id=True)

        fix_message = fix.Message()

        for key, value in message_dict.items():
            if key in TAGS_HEADERS_44_LIST and message_dict.get(8).strip() in ('FIX.4.4', 'FIX.4.2'):
                fix_message.getHeader().setField(fix.StringField(key, value))
            elif key in TAGS_HEADERS_50_LIST and message_dict.get(8).strip() == 'FIX.5.0':
                fix_message.getHeader().setField(fix.StringField(key, value))
            elif key in TAGS_HEADERS_T11_LIST and message_dict.git(8).strip() == 'FIXT.1.1':
                fix_message.getHeader().setField(fix.StringField(key, value))
            elif int(key) not in PARTIES_TAG_LIST and int(key) != PARTIES_TAG_LIST:
                fix_message = _message_set_field(fix_message, key, value)

        if PARTY_TAG_COUNT in message_dict.keys():
            parties = fix.Groups(PARTY_TAG_COUNT, int(message.get(PARTY_TAG_COUNT)))
            for party in message.model_dump_parties(use_tag_id=True):
                for tag_id in PARTIES_TAG_LIST:
                    parties.setField(fix.StringField(tag_id, party.get(tag_id)))
                fix_message.addGroup(parties)
        
        return fix_message

    def get_session(self) -> fix.SessionID:
        return self.session_id

    def pop_received_message(self, count: int = 1) -> t.List[Message]:
        if len(self.received_messages_stack) < count:
            raise MessageNotFound(f"Messages in stack {str(len(self.received_messages_stack))}, not {str(count)}")
        response = []
        for i in range(count):
            response.append(self.received_messages_stack.pop(i))
        return response

    def pop_received_admin_message(self, count: int = 1) -> t.List[Message]:
        if len(self.receieved_admin_messages_stack) < count:
            raise MessageNotFound(f"Messages in admin stack {str(len(self.receieved_admin_messages_stack))}, not {str(count)}")
        response = []
        for i in range(count):
            response.append(self.receieved_admin_messages_stack.pop(i))
        return response

    def clear_messages_stack(self) -> None:
        self.received_messages_stack.clear()

    def add_rule_scenario(self, key: t.Callable, value: t.Callable) -> None:
        self.scenario_rule_container[key] = value

    def remove_rule_scenario(self, key: t.Callable) -> t.Callable:
        return self.scenario_rule_container.pop(key)

    def add_default_response(self, message: Message) -> None:
        self.default_response = message

    def clear_default_response(self) -> None:
        self.default_response = None

    def clear_all_rule_scenario(self) -> None:
        self.scenario_rule_container = {}

    def onCreate(self, session_id: fix.SessionID) -> None:
        self.session_id = session_id

    def onLogon(self, session_id: fix.SessionID) -> None: return

    def onLogout(self, session_id: fix.SessionID) -> None: return

    def toAdmin(self, message: fix.Message, session_id: fix.SessionID) -> None: return

    def toApp(self, message: fix.Message, session_id: fix.SessionID) -> None: return

    def fromAdmin(self, message: fix.Message, session_id: fix.SessionID) -> None:
        message = self._fix_to_domain_message(message)
        self.receieved_admin_messages_stack.insert(0, message)

    def fromApp(self, message: fix.Message, session_id: fix.SessionID) -> None:
        message = self._fix_to_domain_message(message)
        self.received_messages_stack.insert(0, message)

        for key, value in self.scenario_rule_container.items():
            if key(message):
                value(self, message)
                break
        else:
            if self.default_response is not None:
                self.send(self.default_response)

    def send(self, message: Message) -> None:
        message = self._domain_to_fix_message(message)
        fix.Session.sendToTarget(message, self.session_id)

    def run(self) -> None:
        def worker() -> None:
            while not self.run_event.is_set():
                time.sleep(0.2)
        thread = threading.Thread(target=worker)
        thread.start()

    def stop(self) -> None:
        self.run_event.set()
