from flask import Markup

from mistune import markdown


def NO_SANITIZER(text: str) -> str:
    return text


def BR_SANITIZER(text: str) -> str:
    return text.replace('\n', '<br/>')


def MK_SANITIZER(text: str) -> str:
    return Markup(markdown(text))
