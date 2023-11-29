from typing import Union, TypeVar


def bool_str(value: bool) -> str:
    return str(value).lower()


T = TypeVar("T")


def first_not_none(*args: Union[T, None]) -> Union[T, None]:
    for arg in args:
        if arg is not None:
            return arg
    return None
