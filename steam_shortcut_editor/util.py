import re
from os import PathLike
from typing import Any, TypeAlias

PathInput: TypeAlias = PathLike[Any] | str

number_regex = re.compile(r"\d+")


def is_numeric_str(s: str) -> bool:
    return bool(number_regex.match(s))


def multiples_of(
    number: int,
    constant: int,
) -> int:
    """
    calculates the smallest number of times a given constant can fully "fit into" a number,
    rounding up to ensure at least one full multiple is returned
    """
    return max(1, (number // constant) + (1 if number % constant != 0 else 0))
