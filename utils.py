from typing import Callable, Coroutine, Any, Optional, TypeVar, cast
from typing_extensions import Concatenate, ParamSpec
from functools import wraps

from main import Service

P = ParamSpec("P")
R = TypeVar("R")


def inject_client(service: Service):
    def decorator(
        fn: Callable[P, Coroutine[Any, Any, Any]],
    ) -> Callable[P, Coroutine[Any, Any, Any]]:
        """
        Simple helper to provide a context managed client to a asynchronous function.

        The decorated function _must_ take a `client` kwarg and if a client is passed when
        called it will be used instead of creating a new one, but it will not be context
        managed as it is assumed that the caller is managing the context.
        """

        @wraps(fn)
        async def with_injected_client(*args: P.args, **kwargs: P.kwargs) -> Any:
            return
            # client = cast(Optional["PrefectClient"], kwargs.pop("client", None))
            # client, inferred = get_or_create_client(client)
            # if not inferred:
            #     context = client
            # else:
            #     from prefect.utilities.asyncutils import asyncnullcontext

            #     context = asyncnullcontext()
            # async with context as new_client:
            #     kwargs.setdefault("client", new_client or client)
            #     return await fn(*args, **kwargs)

        return with_injected_client

    return decorator
