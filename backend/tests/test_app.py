from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.app import app
from src.service import GenerationError

pytestmark = pytest.mark.asyncio


@pytest.fixture
def client() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    )


class TestHealth:
    async def test_ok(self, client: AsyncClient) -> None:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestGenerate:
    async def test_success_with_url(
        self, client: AsyncClient, sample_pdf_bytes: bytes
    ) -> None:
        expected = "Dear Hiring Manager, ..."
        with patch(
            "src.app.generate_cover_letter",
            new_callable=AsyncMock,
            return_value=expected,
        ):
            resp = await client.post(
                "/api/generate",
                files={"resume": ("cv.pdf", sample_pdf_bytes)},
                data={
                    "job_url": "https://example.com/job",
                    "language": "en",
                },
            )

        assert resp.status_code == 200
        assert resp.json()["cover_letter"] == expected

    async def test_success_with_job_text(
        self, client: AsyncClient, sample_pdf_bytes: bytes
    ) -> None:
        expected = "Generated letter"
        with patch(
            "src.app.generate_cover_letter",
            new_callable=AsyncMock,
            return_value=expected,
        ):
            resp = await client.post(
                "/api/generate",
                files={"resume": ("cv.pdf", sample_pdf_bytes)},
                data={
                    "job_text": "Python developer at Acme",
                    "language": "ru",
                },
            )

        assert resp.status_code == 200
        assert resp.json()["cover_letter"] == expected

    async def test_generation_error_400(
        self, client: AsyncClient, sample_pdf_bytes: bytes
    ) -> None:
        with patch(
            "src.app.generate_cover_letter",
            new_callable=AsyncMock,
            side_effect=GenerationError("Unsupported format", status_code=400),
        ):
            resp = await client.post(
                "/api/generate",
                files={"resume": ("cv.txt", b"text")},
                data={"job_url": "https://example.com/job"},
            )

        assert resp.status_code == 400
        assert "Unsupported format" in resp.json()["detail"]

    async def test_generation_error_502(
        self, client: AsyncClient, sample_pdf_bytes: bytes
    ) -> None:
        with patch(
            "src.app.generate_cover_letter",
            new_callable=AsyncMock,
            side_effect=GenerationError(
                "LLM generation failed", status_code=502
            ),
        ):
            resp = await client.post(
                "/api/generate",
                files={"resume": ("cv.pdf", sample_pdf_bytes)},
                data={"job_url": "https://example.com/job"},
            )

        assert resp.status_code == 502

    async def test_missing_resume(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/generate",
            data={"job_url": "https://example.com/job"},
        )
        assert resp.status_code == 422

    async def test_no_job_input(
        self, client: AsyncClient, sample_pdf_bytes: bytes
    ) -> None:
        with patch(
            "src.app.generate_cover_letter",
            new_callable=AsyncMock,
            side_effect=GenerationError(
                "Provide either a job URL or job description text.",
                status_code=400,
            ),
        ):
            resp = await client.post(
                "/api/generate",
                files={"resume": ("cv.pdf", sample_pdf_bytes)},
            )

        assert resp.status_code == 400
