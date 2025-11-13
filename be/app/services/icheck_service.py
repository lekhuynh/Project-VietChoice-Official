from __future__ import annotations
from typing import Optional
import re
import asyncio

from bs4 import BeautifulSoup
import aiohttp

from .http_async import get_text_with_session


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)


async def alookup_product_name(barcode: str) -> Optional[str]:
    """
    Tra cứu tên sản phẩm từ iCheck.vn bằng aiohttp + BeautifulSoup (async).
    """
    barcode = str(barcode or '').strip()
    if not re.fullmatch(r"\d{6,14}", barcode):
        return None

    url = f"https://icheck.vn/san-pham/{barcode}"
    headers = {"User-Agent": USER_AGENT}

    timeout = aiohttp.ClientTimeout(total=10)
    connector = aiohttp.TCPConnector(limit=20)
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        try:
            html = await get_text_with_session(session, url, headers=headers, retries=1)
            if not html:
                return None

            soup = BeautifulSoup(html, "html.parser")

            og_tag = soup.find("meta", attrs={"property": "og:title"})
            if og_tag and og_tag.get("content"):
                og_title = og_tag["content"].strip()
                if og_title and og_title.upper() == "KHÁM PHÁ THÊM":
                    return None
                if "icheck" in og_title.lower() or "sản phẩm" in og_title.lower():
                    return None
                return og_title

            for selector in ["h1", "h2", "div.product-name"]:
                tag = soup.select_one(selector)
                if tag:
                    name = tag.get_text(strip=True)
                    if not name:
                        continue
                    if name.upper() == "KHÁM PHÁ THÊM":
                        return None
                    if "icheck" in name.lower() or "sản phẩm" in name.lower():
                        return None
                    return name

            return None

        except Exception as e:
            print(f"[iCheck] ⛔ Connection error: {e}")
            return None


def lookup_product_name(barcode: str) -> Optional[str]:
    """
    Sync wrapper để tương thích code cũ, chạy coroutine phía dưới.
    """
    try:
        return asyncio.run(alookup_product_name(barcode))
    except RuntimeError:
        # Trường hợp đã có event loop (hiếm trong FastAPI sync), tạo loop tạm.
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(alookup_product_name(barcode))
        finally:
            loop.close()


# Safe wrapper usable from async contexts without nesting event loops
def lookup_product_name_safe(barcode: str) -> Optional[str]:
    """
    Resolve product name from iCheck in a way that is safe whether called from
    sync or async contexts. If an event loop is already running in this thread
    (e.g., inside a FastAPI async endpoint), offload to a separate thread and
    run the coroutine there with its own loop.
    """
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            import concurrent.futures

            def _runner() -> Optional[str]:
                return asyncio.run(alookup_product_name(barcode))

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(_runner)
                return fut.result(timeout=20)
    except RuntimeError:
        # No running loop; fall through
        pass

    return asyncio.run(alookup_product_name(barcode))
