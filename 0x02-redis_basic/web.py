#!/usr/bin/env python3
""" Expiring web cache module """

from functools import wraps
import redis
import requests
from typing import Callable

# Initialize Redis client connection
r = redis.Redis()


def count_calls(method: Callable) -> Callable:
    """
    A decorator to count how many
    times a method is called.

    Args:
        method (Callable): The method to be decorated.

    Returns:
        Callable: The wrapped method
        that increments the call count.
    """
    @wraps(method)
    def wrapper(*args, **kwargs):
        url = args[0]
        # Increment the count in Redis for the specific URL
        r.incr(f"count:{url}")
        # Execute the original method and return its output
        return method(*args, **kwargs)

    return wrapper


@count_calls
def get_page(url: str) -> str:
    """
    Fetches the HTML content from a given URL
    and caches it in Redis with an expiration time.

    Args:
        url (str): The URL to fetch.

    Returns:
        str: The HTML content of the page.
    """
    # Check if the content is already cached in Redis
    cached_content = r.get(f"cache:{url}")
    if cached_content:
        # If cached, decode and return the content
        return cached_content.decode('utf-8')

    # If not cached, fetch the content using requests
    response = requests.get(url)
    html_content = response.text

    # Cache the content in Redis with a 10-second expiration time
    r.setex(f"cache:{url}", 10, html_content)

    return html_content


if __name__ == "__main__":
    # Test the function with a slow response URL
    url = "http://slowwly.robertomurray.co.uk"
    print(get_page(url))  # Fetch and cache the page
    print(get_page(url))  # Retrieve the cached page
