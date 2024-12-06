import struct
from copy import copy
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Container, TypeAlias, Union

from steam_shortcut_editor import constants
from steam_shortcut_editor.util import PathInput, is_numeric_str


@dataclass
class ObjectParserConfig:
    date_properties: Container[str] = field(
        default_factory=lambda: copy(constants.DATE_PROPERTIES)
    )
    auto_convert_booleans: bool = True
    auto_convert_arrays: bool = True


ParsedValue: TypeAlias = Union["ParsedObj", str | datetime | bool | int]
ParsedObj: TypeAlias = dict[str, ParsedValue] | list[ParsedValue]


@dataclass
class ObjectParser:
    buffer: bytes
    cursor: int = 0
    options: ObjectParserConfig = field(default_factory=ObjectParserConfig)

    def read_str(self) -> str:
        start = self.cursor
        while self.buffer[self.cursor] != constants.special.STRING_END:
            self.cursor += 1
        value = self.buffer[start : self.cursor].decode(constants.UTF8)
        self.cursor += 1
        return value

    def read_int(self) -> int:
        start = self.cursor
        self.cursor += 4
        value = struct.unpack("<i", self.buffer[start : self.cursor])[0]
        if not isinstance(value, int):
            raise TypeError(f"expected {int}, got {value!r}")
        return value

    def read(self) -> ParsedObj:
        obj: dict[str, ParsedValue] = {}
        while self.cursor < len(self.buffer):
            type_ = self.buffer[self.cursor]

            self.cursor += 1

            if type_ == constants.special.OBJECT_END:
                break

            key = self.read_str()

            value: ParsedValue
            match type_:
                case constants.types.OBJECT:
                    value = self.read()
                case constants.types.STRING:
                    value = self.read_str()
                case constants.types.INT:
                    value = self.read_int()
                    if key in self.options.date_properties:
                        value = datetime.fromtimestamp(value) if value else False
                    elif self.options.auto_convert_booleans and value in {0, 1}:
                        value = bool(value)
                case _:
                    raise ValueError(f"unrecognised type 0x{type_:0>2x}")

            obj[key] = value

        if self.options.auto_convert_arrays and all(is_numeric_str(key) for key in obj):
            return list(obj.values())

        return obj


def parse_file(
    file_path: PathInput,
    opts: ObjectParserConfig | None = None,
) -> ParsedObj:
    file_path = Path(file_path)

    if opts is None:
        opts = ObjectParserConfig()

    with open(file_path, "rb") as f:
        data = f.read()

    obj = ObjectParser(
        buffer=data,
        options=opts,
    )
    result = obj.read()

    return result
