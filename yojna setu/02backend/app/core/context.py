import contextvars
from typing import Optional

# Context variable to hold the request_id for the current request thread/task context
request_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("request_id_ctx", default=None)


def get_request_id() -> Optional[str]:
    return request_id_ctx.get()


def set_request_id(req_id: str) -> None:
    request_id_ctx.set(req_id)
