import keyword
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

DICTIONARY_URL = (
    "https://raw.githubusercontent.com/quickfix/quickfix/"
    "master/spec/FIX50SP2.xml"
)

OUTPUT = Path("fix_tags.py")
MIN_TAG = 1
MAX_TAG = 1139


def generate_fix_tags() -> None:
    """
    Function to generate enum with fix tags. Generates enum with tags from 1 to 1139
    run: python generate_tags.py
    result: file fix_tags.py with IntEnum
    """
    with urllib.request.urlopen(DICTIONARY_URL) as response:
        root = ET.fromstring(response.read())

    fields = root.find("fields")

    if fields is None:
        raise ValueError("FIX dictionary has no fields section")

    tags = {}

    for field in fields.findall("field"):
        number = int(field.attrib["number"])
        name = field.attrib["name"]

        if not MIN_TAG <= number <= MAX_TAG:
            continue

        if not name.isidentifier() or keyword.iskeyword(name):
            name = re.sub(r"\W", "_", name)

            if name[0].isdigit():
                name = f"Tag_{name}"

            if keyword.iskeyword(name):
                name += "_"

        if name in tags.values():
            raise ValueError(f"Duplicate field name: {name}")

        tags[number] = name

    lines = [
        "from enum import IntEnum",
        "",
        "",
        "class FixTags(IntEnum):",
    ]

    for number, name in sorted(tags.items()):
        lines.append(f"    {name} = {number}")

    OUTPUT.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print(f"Generated {len(tags)} FIX tags")
    print(f"Saved to {OUTPUT.resolve()}")


if __name__ == "__main__":
    generate_fix_tags()