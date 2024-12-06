import struct
import sys
from dataclasses import dataclass, field
from datetime import datetime

from steam_shortcut_editor import constants
from steam_shortcut_editor.parser import ParsedObj, ParsedValue
from steam_shortcut_editor.util import PathInput, multiples_of


@dataclass
class ObjectWriter:
    buffer: bytearray = field(default_factory=bytearray)
    cursor: int = 0
    alloc_size: int = 256

    def extend_if_needed(
        self,
        new_amount_of_bytes: int,
    ) -> None:
        if len(self.buffer) >= self.cursor + new_amount_of_bytes:
            return
        remaining_size = new_amount_of_bytes - (len(self.buffer) - self.cursor)
        multiples_of_alloc = multiples_of(remaining_size, self.alloc_size)
        self.buffer += bytearray(multiples_of_alloc * self.alloc_size)

    def append_str(
        self,
        value: str,
    ) -> None:
        length_in_bytes = len(value.encode(constants.UTF8))
        self.extend_if_needed(length_in_bytes + 1)

        start = self.cursor
        self.cursor += length_in_bytes

        self.buffer[start : self.cursor] = value.encode(constants.UTF8)
        self.buffer[self.cursor] = constants.special.STRING_END

        self.cursor += 1

    def append_num(
        self,
        value: int | float,
    ) -> None:
        self.extend_if_needed(4)
        struct.pack_into("<i", self.buffer, self.cursor, value)
        self.cursor += 4

    def append_value(
        self,
        value: ParsedValue,
    ) -> None:
        if value is None:
            value = ""
        elif isinstance(value, bool):
            value = int(value)
        elif isinstance(value, datetime):
            value = int(value.timestamp())

        if isinstance(value, str):
            self.append_str(value)
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            self.append_num(value)
        elif isinstance(value, (dict, list)):
            items = value.items() if isinstance(value, dict) else enumerate(value)

            for key, prop_value in items:
                constant = None

                if prop_value is None or isinstance(prop_value, str):
                    constant = constants.types.STRING
                elif isinstance(prop_value, (int, float, bool, datetime)):
                    constant = constants.types.INT
                elif isinstance(prop_value, (dict, list)):
                    constant = constants.types.OBJECT
                else:
                    raise ValueError(
                        f"Writer encountered unhandled value: {prop_value!r}"
                    )

                key_encoded = str(key).encode(constants.UTF8)
                length_in_bytes = len(key_encoded)
                self.extend_if_needed(length_in_bytes + 2)
                self.buffer[self.cursor] = constant
                self.cursor += 1

                start = self.cursor
                self.cursor += length_in_bytes
                self.buffer[start : self.cursor] = key_encoded

                self.buffer[self.cursor] = constants.special.PROPERTY_NAME_END
                self.cursor += 1

                self.append_value(prop_value)

            self.extend_if_needed(1)
            self.buffer[self.cursor] = constants.special.OBJECT_END
            self.cursor += 1
        else:
            raise ValueError(f"Writer encountered unhandled value: {value}")

    @property
    def data(self) -> bytearray:
        return self.buffer[: self.cursor]


def write_file(
    obj: ParsedObj,
    file_path: PathInput,
) -> None:

    buffer = ObjectWriter()

    # try to predict object size to reduce number of allocations
    buffer.extend_if_needed(sys.getsizeof(obj))

    buffer.append_value(obj)

    with open(file_path, "wb") as f:
        f.write(buffer.data)
