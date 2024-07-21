from typing import Any


class StatsResponse:
    def __init__(self, status: str, message: str, **kwargs: Any):
        self.status = status
        self.message = message
        self.data = kwargs

    @classmethod
    def error(cls, message: str) -> "StatsResponse":
        return cls(status="error", message=message)

    @classmethod
    def success(cls, message: str, **kwargs: Any) -> "StatsResponse":
        return cls(status="success", message=message, **kwargs)
