from typing import Any, Callable, Optional, TypeVar

from flask import request, Response

DecoratedCallable = TypeVar('DecoratedCallable', bound=Callable[..., Any])


class AuthHelper:
    def __init__(self, config: dict) -> None:
        self.config: dict = config

    def check(self, username: Optional[str], password: Optional[str]) -> bool:
        return username == self.config.get('PAGE_AUTH_USERNAME') and password == self.config.get('PAGE_AUTH_PASSWORD')

    def auth(self) -> bool:
        req_auth = request.authorization
        return (req_auth is not None and req_auth.type == 'basic' and self.check(req_auth.username, req_auth.password))

    def ask(self) -> Response:
        return Response(status=401, headers={'WWW-Authenticate': 'Basic realm OpenAPI Documentation'})

    def do_auth(self) -> None:
        if self.config.get("PAGE_AUTH"):
            if not self.auth():
                self.ask()
