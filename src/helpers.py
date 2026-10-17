import itertools
import os
import time
import uuid

import quickfix as fix

from .exception import SocketConnectionError

__all__ = [
    "SOH",
    "calculate_checksum"
]

SOH = chr(0x01)

TAGS_HEADERS_44_LIST = [
    8, 9, 35, 49, 56, 115, 128, 90, 91, 34, 50,
    142, 57, 143, 116, 144, 129, 145, 43, 97, 52,
    122, 212, 213, 347, 369, 627, 628, 629, 630
]

TAGS_HEADERS_50_LIST = [
    8, 9, 35, 49, 56, 115, 128, 90, 91, 34,
    50, 142, 57, 143, 116, 144, 129, 145, 43,
    97, 52, 122, 212, 213, 347, 369, 1128, 1129
]

TAGS_HEADERS_T11_LIST = [
    8, 9, 35, 1128, 1156, 1129, 49, 56, 115, 128,
    98, 91, 34, 50, 142, 57, 143, 116, 144, 129,
    145, 43, 97, 52, 122, 212, 213, 347, 369
]

PARTIES_TAG_LIST = [448, 447, 452]
PARTY_TAG_COUNT = 453


def calculate_checksum(message: str) -> str:
    count = 0
    for i in message:
        count += ord(i)
    count %= 256
    if len(str(count)) < 3:
        count = ('0' * (3-len(str(count)))) + str(count)
    else:
        count = str(count)
    return count


def _message_set_field(message: fix.Message, tag_id: int, value: int | float | str | bool) -> fix.Message:
    if isinstance(value, str):
        field = fix.StringField(tag_id, value)
    elif isinstance(value, int):
        field = fix.IntField(tag_id, value)
    elif isinstance(value, bool):
        field = fix.BoolField(tag_id, value)
    else:
        field = fix.DoubleField(tag_id, value)

    message.setField(field)

    return message


def _get_session_dictionary(**config) -> fix.Dictionary:
    dictionary = fix.Dictionary()

    for setting_name in config:
        if isinstance(config.get(setting_name), str):
            dictionary.setString(setting_name, config.get(setting_name))
        elif isinstance(config.get(setting_name), int):
            dictionary.setInt(setting_name, config.get(setting_name))
        elif isinstance(config.get(setting_name), bool):
            dictionary.setBool(setting_name, config.get(setting_name))
        elif isinstance(config.get(setting_name), float):
            dictionary.getDouble(setting_name, config.get(setting_name))

    return dictionary


def _get_session_settings(**config) -> fix.SessionSettings:
    with open(f"{os.path.dirname(__file__)}/fix.default.cfg", 'r') as file:
        settings = file.readlines()

    # config = list(config.items())
    config = [[str(i), str(j)] for i, j in list(config.items())]
    config = [f"{'='.join(i)}\n" for i in config]
    settings.append("\n[SESSION]\n")
    settings += config
    path_config_name = f"{os.path.dirname(__file__)}/{str(uuid.uuid4())}.cfg"

    with open(path_config_name, 'w') as file:
        file.writelines(settings)
    session_settings = fix.SessionSettings(path_config_name)

    if os.path.isfile(path_config_name):
        os.remove(path_config_name)

    return session_settings


def _wait_session_login(session_id: fix.SessionID, timeout: int = 5) -> None:
    sleeping_second = 0.3
    wait_session_iteration = timeout / sleeping_second
    count = itertools.count()
    while not fix.Session.lookupSession(session_id).isLoggedOn():
        time.sleep(sleeping_second)
        if next(count) == wait_session_iteration:
            raise SocketConnectionError(f"Timeout exceeded. Session {str(session_id)} expired")
