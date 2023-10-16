import json
from collections import OrderedDict
from copy import deepcopy
from typing import Any, Union, Dict

import yaml
from six import text_type


def ordered_dict_to_dict(d: Union[Dict, OrderedDict]) -> Dict:
    """
    Converts inner OrderedDict to bare dict

    :param d: OrderedDict
    :type d: Any

    :return: dict
    :rtype: dict
    """
    ret: Dict = {}
    new_d: Any = deepcopy(d)
    for k, v in new_d.items():
        if isinstance(v, OrderedDict):
            v = dict(v)
        if isinstance(v, dict):
            v = ordered_dict_to_dict(v)
        ret[k] = v
    return ret


def json_to_yaml(content: str) -> str:
    """
    Convert json to yaml

    :param content: json content
    :type content: str

    :return: yaml content
    :rtype: str
    """
    loaded_json: Any = json.loads(content)
    parsed_yaml: str = yaml.dump(loaded_json)

    return parsed_yaml


class StringLike:
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
        string = self.text_type(self)
        if hasattr(string, attr):
            return getattr(string, attr)
        raise AttributeError(attr)

    def __len__(self):
        return len(self.text_type(self))

    def __getitem__(self, key):
        return self.text_type(self)[key]

    def __iter__(self):
        return iter(self.text_type(self))

    def __contains__(self, item):
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
    def text_type(self):
        return text_type
