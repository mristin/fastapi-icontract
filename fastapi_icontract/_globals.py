"""Define global variables used throughout the module."""
from typing import TypeVar, Callable, Any

CallableT = TypeVar("CallableT", bound=Callable[..., Any])
