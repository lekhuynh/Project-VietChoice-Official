import asyncio
from typing import Any, Dict, Iterable, List, Optional

import aiohttp


# A small helper module for shared async HTTP utilities.
# Note: Prefer reusing a single ClientSession per batch to maximize throughput.

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=15)


async def get_json(url: str, *, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, retries: int = 1) -> Optional[Dict[str, Any]]:
    """Simple JSON GET using its own session (useful for one-offs)."""
    for attempt in range(retries + 1):
        try:
            async with aiohttp.ClientSession(timeout=DEFAULT_TIMEOUT) as session:
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status == 200:
                        # Some APIs may respond with non-standard content-type
                        return await resp.json(content_type=None)
        except Exception:
            await asyncio.sleep(0.4 * (attempt + 1))
            continue
    return None


async def get_text(url: str, *, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, retries: int = 1) -> Optional[str]:
    """Simple TEXT GET using its own session (useful for one-offs)."""
    for attempt in range(retries + 1):
        try:
            async with aiohttp.ClientSession(timeout=DEFAULT_TIMEOUT) as session:
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status == 200:
                        return await resp.text()
        except Exception:
            await asyncio.sleep(0.4 * (attempt + 1))
            continue
    return None


async def get_json_with_session(session: aiohttp.ClientSession, url: str, *, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, retries: int = 1) -> Optional[Dict[str, Any]]:
    """JSON GET reusing a provided session. Retries with backoff."""
    for attempt in range(retries + 1):
        try:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    return await resp.json(content_type=None)
        except Exception:
            await asyncio.sleep(0.4 * (attempt + 1))
            continue
    return None


async def get_text_with_session(session: aiohttp.ClientSession, url: str, *, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, retries: int = 1) -> Optional[str]:
    """TEXT GET reusing a provided session. Retries with backoff."""
    for attempt in range(retries + 1):
        try:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    return await resp.text()
        except Exception:
            await asyncio.sleep(0.4 * (attempt + 1))
            continue
    return None


async def bounded_gather(coros: Iterable[asyncio.Future], limit: int = 50) -> List[Any]:
    """Run coroutines with a concurrency limit and gather results preserving order."""
    semaphore = asyncio.Semaphore(limit)

    async def run_with_sem(coro):
        async with semaphore:
            return await coro

    tasks = [asyncio.create_task(run_with_sem(c)) for c in coros]
    return await asyncio.gather(*tasks)
