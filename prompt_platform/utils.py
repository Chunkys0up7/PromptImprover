"""
This module contains shared utility functions for the application.
"""
import asyncio

def run_async(coro):
    """Run an async coroutine in a running event loop or a new one."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro) 