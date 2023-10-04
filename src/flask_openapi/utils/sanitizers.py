from markupsafe import Markup
from mistune import markdown


def NO_SANITIZER(text: str) -> str:
    return text


def BR_SANITIZER(text: str) -> str:
    return text.replace("\n", "<br/>") if text else text


def MK_SANITIZER(text: str) -> str:
    return Markup(markdown(text)) if text else text
