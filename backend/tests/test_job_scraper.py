import httpx
import pytest
import respx

from src.job_scraper import scrape_job

pytestmark = pytest.mark.asyncio


_SAMPLE_HTML = """\
<html>
<head><title>Job</title></head>
<body>
  <nav><a href="/">Home</a></nav>
  <script>var x = 1;</script>
  <style>body { color: red; }</style>
  <main>
    <h1>Python Developer</h1>
    <p>We are looking for a Python developer.</p>
    <ul>
      <li>3+ years experience</li>
      <li>FastAPI knowledge</li>
    </ul>
  </main>
  <footer>Copyright 2025</footer>
</body>
</html>
"""


class TestScrapeJob:
    @respx.mock
    async def test_extracts_text(self) -> None:
        url = "https://example.com/job/123"
        respx.get(url).mock(
            return_value=httpx.Response(200, text=_SAMPLE_HTML)
        )

        result = await scrape_job(url)

        assert "Python Developer" in result
        assert "3+ years experience" in result
        assert "FastAPI knowledge" in result

    @respx.mock
    async def test_strips_nav_footer_script(self) -> None:
        url = "https://example.com/job/456"
        respx.get(url).mock(
            return_value=httpx.Response(200, text=_SAMPLE_HTML)
        )

        result = await scrape_job(url)

        assert "Home" not in result
        assert "Copyright" not in result
        assert "var x" not in result
        assert "color: red" not in result

    @respx.mock
    async def test_http_error_raises(self) -> None:
        url = "https://example.com/job/404"
        respx.get(url).mock(return_value=httpx.Response(404))

        with pytest.raises(httpx.HTTPStatusError):
            await scrape_job(url)

    @respx.mock
    async def test_empty_page(self) -> None:
        url = "https://example.com/empty"
        respx.get(url).mock(
            return_value=httpx.Response(200, text="<html><body></body></html>")
        )

        result = await scrape_job(url)
        assert result == ""

    @respx.mock
    async def test_truncates_long_text(self) -> None:
        long_body = "\n".join(f"<p>Line {i}</p>" for i in range(2000))
        html = f"<html><body>{long_body}</body></html>"
        url = "https://example.com/job/long"
        respx.get(url).mock(return_value=httpx.Response(200, text=html))

        result = await scrape_job(url)
        assert len(result) <= 6000
