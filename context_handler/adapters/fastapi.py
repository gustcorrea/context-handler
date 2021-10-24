import collections.abc as collections
import typing

import fastapi as _fastapi

from context_handler import _datastructures
from context_handler.factory import generate_state_name


def setup_context_cleaner_middleware(app: _fastapi.FastAPI):
    async def _context_cleaner_middleware(
        request: _fastapi.Request,
        call_next: typing.Callable[
            [_fastapi.Request],
            collections.Coroutine[
                None, None, _fastapi.responses.StreamingResponse
            ],
        ],
    ):
        response = await call_next(request)
        app_state_dict = object.__getattribute__(request.app.state, "_state")
        request_state_dict = object.__getattribute__(request.state, "_state")
        provider_list = _get_provider_list(app_state_dict)
        contexts_from_provider = _get_contexts_from_providers(
            provider_list, request_state_dict
        )
        contexts_by_type = _get_contexts_by_type(request_state_dict)
        await _close_active_contexts(
            frozenset(contexts_from_provider + contexts_by_type)
        )
        return response

    app.middleware("http")(_context_cleaner_middleware)


def _get_provider_list(
    _app_state_dict: dict[str, typing.Any]
) -> list[
    typing.Union[_datastructures.Provider, _datastructures.AsyncProvider]
]:
    def _gen():
        for value in _app_state_dict:
            if isinstance(
                value,
                (_datastructures.Provider, _datastructures.AsyncProvider),
            ):
                yield value

    return list(_gen())


def _get_contexts_from_providers(
    provider_list: list[
        typing.Union[_datastructures.Provider, _datastructures.AsyncProvider]
    ],
    request_state_dict: dict[str, typing.Any],
):
    def _gen():
        for provider in provider_list:
            if (
                context := request_state_dict.get(
                    generate_state_name(type(provider))
                )
            ) is not None:
                yield context

    return list(_gen())


def _get_contexts_by_type(request_state_dict: dict[str, typing.Any]):
    def _gen():
        for value in request_state_dict.values():
            if isinstance(
                value,
                (
                    _datastructures.AbstractSyncContext,
                    _datastructures.AbstractAsyncContext,
                ),
            ):
                yield value

    return list(_gen())


async def _close_active_contexts(
    contexts: frozenset[
        typing.Union[
            _datastructures.AbstractAsyncContext,
            _datastructures.AbstractSyncContext,
        ]
    ]
):
    for ctx in contexts:
        if ctx.client is not None:
            provider = ctx.get_provider()
            if provider.is_closed(ctx.client):
                if isinstance(provider, _datastructures.AsyncProvider):
                    await provider.close_client(ctx.client)
                else:
                    provider.close_client(ctx.client)