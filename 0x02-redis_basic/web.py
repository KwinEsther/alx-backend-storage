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
        key = f"count:{url}"
        # Increment the count in Redis for the specific URL
        count = r.incr(key)
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
    cache_key = f"cache:{url}"
    count_key = f"count:{url}"

    # Check if the content is already cached in Redis
    cached_content = r.get(cache_key)
    if cached_content:
        # If cached, decode and return the content
        return cached_content.decode('utf-8')

    # If not cached, fetch the content using requests
    response = requests.get(url)
    html_content = response.text

    # Cache the content in Redis with a 10-second expiration time
    r.setex(cache_key, 10, html_content)

    return html_content

def get_count(url: str) -> int:
    """
    Get the number of times a URL has been accessed.

    Args:
        url (str): The URL to check.

    Returns:
        int: The number of times the URL has been accessed.
    """
    count = r.get(f"count:{url}")
    return int(count) if count else 0

def reset_count(url: str) -> None:
    """
    Reset the access count for a URL.

    Args:
        url (str): The URL to reset.
    """
    r.delete(f"count:{url}")

if __name__ == "__main__":
    # Clear any existing data
    r.flushall()

    url = "http://google.com"

    # Test 1: Initial count should be 0
    initial_count = get_count(url)
    assert initial_count == 0, f"Expected count 0, got {initial_count}"

    # Test 2: Count should increment when page is fetched
    get_page(url)
    count_after_first = get_count(url)
    assert count_after_first == 1, f"Expected count 1, got {count_after_first}"

    # Test 3: Count should increment again
    get_page(url)
    count_after_second = get_count(url)
    assert count_after_second == 2, f"Expected count 2, got {count_after_second}"

    # Test 4: Content should be cached for 10 seconds
    import time
    cached_content = r.get(f"cache:{url}")
    assert cached_content is not None, "Content should be cached"

    # Test 5: Cache should expire after 10 seconds
    time.sleep(11)
    expired_content = r.get(f"cache:{url}")
    assert expired_content is None, "Cache should have expired"

    print("All tests passed!")
