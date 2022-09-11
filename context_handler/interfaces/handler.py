import typing

from context_handler.interfaces.adapter import Adapter
from context_handler.interfaces.adapter import AsyncAdapter
from context_handler.typedef import AsyncT
from context_handler.typedef import T
from context_handler.utils import lazy


class Handler(typing.Protocol[T]):
    adapter: Adapter[T]

    def __init__(self, adapter: Adapter[T]) -> None:
        ...

    def is_active(self) -> bool:
        """Returns if current handler has an active context"""
        ...

    client: lazy.LazyPropertyDescriptor['Handler', T]

    def open(self) -> typing.ContextManager[None]:
        """Initializes an internal client"""
        ...

    def begin(self) -> typing.ContextManager[T]:
        """Returns initialized internal client
        or new client if none is found"""
        ...


class AsyncHandler(typing.Protocol[AsyncT]):
    adapter: AsyncAdapter[AsyncT]

    def __init__(self, adapter: AsyncAdapter[AsyncT]) -> None:
        ...

    def is_active(self) -> bool:
        """Returns if current handler has an active context"""
        ...

    async def client(self) -> AsyncT:
        """Returns internal client or creates a new one"""
        ...

    def open(self) -> typing.AsyncContextManager[None]:
        """Initializes an internal client"""
        ...

    def begin(self) -> typing.AsyncContextManager[AsyncT]:
        """Returns initialized internal client
        or new client if none is found"""
        ...