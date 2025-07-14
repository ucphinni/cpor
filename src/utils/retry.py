"""Retry utilities for the application."""
import asyncio
from functools import wraps
from typing import Type, Callable, Any, Optional, Union
from google.api_core import retry as google_retry

def with_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    A decorator that implements retry logic with exponential backoff.
    
    Args:
        max_retries: Maximum number of retries before giving up
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Multiplier applied to delay between retries
        exceptions: Tuple of exceptions to catch and retry on
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        raise last_exception
                    
                    await asyncio.sleep(min(delay, max_delay))
                    delay *= backoff_factor
            
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator

def create_retry_decorator(
    predicate: Optional[Callable[[Exception], bool]] = None,
    **retry_kwargs: Any
) -> google_retry.Retry:
    """
    Create a Google Cloud retry decorator with custom settings.
    
    Args:
        predicate: A function that takes an exception and returns True if retry should happen
        **retry_kwargs: Additional arguments to pass to Retry constructor
    """
    return google_retry.Retry(
        predicate=predicate or google_retry.if_exception_type(Exception),
        **retry_kwargs
    )
