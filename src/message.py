import typing as t

from .helpers import (
    SOH,
    PARTIES_TAG_LIST,
    PARTY_TAG_COUNT
)

from .tags import FixTags

__all__ = [
    "Message"
]


def _string_tag_id_to_tag_name(tag_id: str) -> str:
    tag_name = int(tag_id.replace('_', ''))
    try:
        tag_name = FixTags(tag_name).name
    except (ValueError, KeyError):
        tag_name = tag_id
    return tag_name

class Message:
    def __init__(self, tag_map: t.MutableMapping = None, from_string: str = None, **tags):
        self.__party_value_tag_id = []
        if from_string is not None:
            tag_list = [i.split('=') for i in from_string.split(SOH)[:-1]]
            tag_map = {f"_{str(key)}": value for key, value in tag_list}
            for key, value in tag_map.items():
                key = _string_tag_id_to_tag_name(key)
                setattr(self, key, value)

            if self.__dict__.get(FixTags(PARTY_TAG_COUNT).name) is not None:
                party_value = from_string[from_string.find(str(PARTY_TAG_COUNT)):].split(SOH)
                party_value = party_value[1:len(PARTIES_TAG_LIST) * int(self.__dict__.get(FixTags(PARTY_TAG_COUNT).name)) + 1]
                self.__party_value_tag_id = [tuple(i.split('=')) for i in party_value]
                for tag_id in PARTIES_TAG_LIST:
                    try:
                        self.__dict__.pop(FixTags(tag_id).name)
                    except KeyError:
                        pass

        elif tag_map is not None:
            if tag_map.get("party_value") is not None:
                self.__update_parties(tag_map)
            tag_map = {(f"_{str(key)}" if isinstance(key, int) else key): value for key, value, in tag_map.items()}
            for key, value in tag_map.items():
                if key.replace('_', '').isdigit():
                    key = _string_tag_id_to_tag_name(key)
                setattr(self, key, value)

        if tags.get("party_value") is not None:
            self.__update_parties(tags)
        for key, value in tags.items():
            if key.replace('_', '').isdigit():
                key = _string_tag_id_to_tag_name(key)
            setattr(self, key, value)

        self.__message_from_string = from_string
        self.__message_tag_id = {
            (int(key.replace('_', '')) if key.replace('_', '').isdigit()
             else FixTags[key].value): value for key, value in self.__dict__.items() if not key.startswith("_Message__")
        }

    def __str__(self) -> str:
        if self.__message_from_string is None:
            message = [(i[0], str(i[1])) for i in list(self.model_dump().items())]
            message = '\n'.join(['='.join(i) for i in message])

        else:
            message = self.__message_from_string.replace(SOH, '\n')

        return message

    def __repr__(self) -> str:
        if self.__message_from_string is None:
            message = [(i[0], str(i[1])) for i in list(self.model_dump(use_tag_id=True).items())]
            message = SOH.join(["=".join((str(i[0]), i[1])) for i in message])
            message += SOH
        else:
            message = self.__message_from_string

        return message

    def __update_parties(self, parties_dict: t.MutableMapping) -> None:
        self.__party_value_tag_id = []
        party_value = parties_dict.pop("party_value")
        for party in party_value:
            party_int_value = {
                (int(key) if str(key).strip().isdigit() 
                 else FixTags[key.strip()].value): value for key, value in party.items()
            }
            self.__party_value_tag_id.append(party_int_value)

    def is_string(self) -> bool:
        return isinstance(self.__message_from_string, str)

    def get(self, tag: int | str) -> str | None:
        if isinstance(tag, int):
            value = self.__message_tag_id.get(tag)
        else:
            value = self.__dict__.get(tag)
        return value

    def update(self, tag_map: t.MutableMapping = None, from_string: str = None, **tags) -> None:
        if from_string is not None:
            tag_list = [i.split('=') for i in from_string.split(SOH)[:-1]]
            tag_map = {f"_{str(key)}": value for key, value in tag_list}
            for key, value in tag_map.items():
                key = _string_tag_id_to_tag_name(key)
                setattr(self, key, value)

            if self.__dict__.get(FixTags(PARTY_TAG_COUNT).name) is not None:
                self.__party_value_tag_id = []
                party_value = from_string[from_string.find(str(PARTY_TAG_COUNT)):].split(SOH)
                party_value = party_value[1: len(PARTIES_TAG_LIST) * int(self.__dict__.get(FixTags(PARTY_TAG_COUNT).name)) + 1]
                self.__party_value_tag_id = [tuple(i.split('=')) for i in party_value]
                for tag_id in PARTIES_TAG_LIST:
                    try:
                        self.__dict__.pop(FixTags(tag_id).name)
                    except KeyError:
                        pass

        elif tag_map is not None:
            if tag_map.get("party_value") is not None:
                self.__update_parties(tag_map)
            tag_map = {(f"_{str(key)}" if isinstance(key, int) else key): value for key, value in tag_map.items()}
            for key, value in tag_map.items():
                if key.replace('_', '').isdigit():
                    key = _string_tag_id_to_tag_name(key)
                setattr(self, key, value)

        if tags.get("party_value") is not None:
            self.__update_parties(tags)

        for key, value in tags.items():
            if key.replace('_', '').isdigit():
                key = _string_tag_id_to_tag_name(key)
            setattr(self, key, value)

        self.__message_from_string = None
        self.__message_tag_id.update({
            (int(key.replace('_', '')) if key.replace('_', '').isdigit() 
             else FixTags[key].value): value for key, value in self.__dict__.items() if not key.startswith("_Message__")
        })

    def pop(self, tag: int | str) -> str:
        if isinstance(tag, int):
            value = self.__message_tag_id.pop(tag)
            self.__dict__.pop(FixTags(tag).name)
        elif tag.strip() == "party_value":
            value = self.__party_value_tag_id
            self.__party_value_tag_id = []
        else:
            value = self.__dict__.pop(tag)
            self.__message_tag_id.pop(FixTags[tag].value)
        self.__message_from_string = None
        return value

    def model_dump(self, use_tag_id: bool = False) -> t.MutableMapping:
        if use_tag_id:
            dump_dict = self.__message_tag_id
        else:
            dump_dict = {key: value for key, value in self.__dict__.items() if not key.startswith("_Message__")}
        return dump_dict

    def model_dump_parties(self, use_tag_id: bool = False) -> t.List:
        if use_tag_id:
            dump_dict = self.__party_value_tag_id
        else:
            dump_dict = [
                {(FixTags(int(key)).name if str(key).isdigit() 
                  else key): value for key, value in i.items()} for i in self.__party_value_tag_id
            ]
        return dump_dict
