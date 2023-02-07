from collections import OrderedDict
from copy import deepcopy
from typing import Iterator, Type

from six import text_type


def ordered_dict_to_dict(d: dict) -> dict:
    """
    Converts inner OrderedDict to bare dict
    """
    ret: dict = {}
    new_d: dict = deepcopy(d)
    for k, v in new_d.items():
        if isinstance(v, OrderedDict):
            v: dict = dict(v)
        if isinstance(v, dict):
            v: dict = ordered_dict_to_dict(v)
        ret[k] = v
    return ret


class StringLike(object):
    """
    Class to mimic the behavior of a regular string. Classes that inherit (or
    mixin) this class must implement the `__str__` magic method. Whatever that
    method returns is used by the various string-like methods.
    """

    def __getattr__(self, attr):
        """
        Forwards any non-magic methods to the resulting string's class. This
        allows support for string methods like `upper()`, `lower()`, etc.
        """
        string: str = self.text_type(self)
        if hasattr(string, attr):
            return getattr(string, attr)
        raise AttributeError(attr)

    def __len__(self) -> int:
        return len(self.text_type(self))

    def __getitem__(self, key) -> str:
        return self.text_type(self)[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.text_type(self))

    def __contains__(self, item) -> bool:
        return item in self.text_type(self)

    def __add__(self, other):
        return self.text_type(self) + other

    def __radd__(self, other):
        return other + self.text_type(self)

    def __mul__(self, other):
        return self.text_type(self) * other

    def __rmul__(self, other):
        return other * self.text_type(self)

    def __lt__(self, other):
        return self.text_type(self) < other

    def __le__(self, other):
        return self.text_type(self) <= other

    def __eq__(self, other):
        return self.text_type(self) == other

    def __ne__(self, other):
        return self.text_type(self) != other

    def __gt__(self, other):
        return self.text_type(self) > other

    def __ge__(self, other):
        return self.text_type(self) >= other

    @property
    def text_type(self) -> Type[str]:
        return text_type


class LazyString(StringLike):
    """
    A lazy string *without* caching. The resulting string is regenerated for
    every request.
    """

    def __init__(self, func) -> None:
        """
        Creates a `LazyString` object using `func` as the delayed closure.
        `func` must return a string.
        """
        self._func = func

    def __str__(self):
        """
        Returns the actual string.
        """
        return self.text_type(self._func())


class CachedLazyString(LazyString):
    """
    A lazy string with caching.
    """

    def __init__(self, func) -> None:
        """
        Uses `__init__()` from the parent and initializes a cache.
        """
        super(CachedLazyString, self).__init__(func)
        self._cache = None

    def __str__(self):
        """
        Returns the actual string and caches the result.
        """
        if not self._cache:
            self._cache = self.text_type(self._func())
        return self._cache
