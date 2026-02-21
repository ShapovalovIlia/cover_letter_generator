import logging

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_MAX_CHARS = 6000

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
}

_STRIP_TAGS = frozenset(
    {
        "script",
        "style",
        "nav",
        "footer",
        "header",
        "noscript",
        "svg",
        "img",
        "iframe",
        "form",
    }
)


def _truncate(text: str, max_chars: int = _MAX_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars].rsplit("\n", maxsplit=1)[0]
    logger.info(
        "Truncated scraped text from %d to %d chars",
        len(text),
        len(cut),
    )
    return cut


async def scrape_job(url: str) -> str:
    logger.info("Scraping job page: %s", url)

    async with httpx.AsyncClient(
        headers=_HEADERS,
        follow_redirects=True,
        timeout=30,
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")

    for tag in soup.find_all(_STRIP_TAGS):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    result = _truncate("\n".join(lines))

    logger.info("Scraped %d chars from %s", len(result), url)
    return result
