from markupsafe import Markup
from mistune import markdown


def NO_SANITIZER(text):
    return text


def BR_SANITIZER(text):
    return text.replace("\n", "<br/>") if text else text


def MK_SANITIZER(text):
    return Markup(markdown(text)) if text else text