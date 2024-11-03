#!/usr/bin/env python3
"""A module equipped with tools for caching,
and tracking requests."""
import redis
import requests
from functools import wraps
from typing import Callable


redis_store = redis.Redis()
"""The Redis instance at the module level.
"""


def data_cacher(method: Callable) -> Callable:
    """Stores the output of retrieved data in a cache.
    """
    @wraps(method)
    def invoker(url) -> str:
        """A wrapper function that caches the output.
        """
        redis_store.incr(f'count:{url}')
        result = redis_store.get(f'result:{url}')
        if result:
            return result.decode('utf-8')
        result = method(url)
        redis_store.set(f'count:{url}', 0)
        redis_store.setex(f'result:{url}', 10, result)
        return result
    return invoker


@data_cacher
def get_page(url: str) -> str:
    """Retrieves the content of a URL,
    caches the response, and tracks the request.
    """
    return requests.get(url).text
