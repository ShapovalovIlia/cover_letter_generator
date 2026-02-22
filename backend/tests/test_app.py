from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.app import app
from src.auth import get_current_user
from src.database import Base, engine
from src.models import Generation, User
from src.service import GenerationError

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
async def _setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


_test_user = User(
    id="test-user-id",
    google_id="google-123",
    email="test@example.com",
    name="Test User",
    picture="",
)


async def _override_current_user() -> User:
    return _test_user


@pytest.fixture(autouse=True)
def _mock_auth():
    app.dependency_overrides[get_current_user] = _override_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
async def db_with_user():
    from src.database import async_session

    async with async_session() as session:
        session.add(
            User(
                id="test-user-id",
                google_id="google-123",
                email="test@example.com",
                name="Test User",
                picture="",
            )
        )
        await session.commit()
        yield session


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
        with (
            patch(
                "src.app.generate_cover_letter",
                new_callable=AsyncMock,
                return_value=expected,
            ),
            patch(
                "src.app.parse_resume",
                return_value="parsed resume text",
            ),
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
        with (
            patch(
                "src.app.generate_cover_letter",
                new_callable=AsyncMock,
                return_value=expected,
            ),
            patch(
                "src.app.parse_resume",
                return_value="parsed resume text",
            ),
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


class TestGenerateStream:
    async def test_stream_success(
        self, client: AsyncClient, sample_pdf_bytes: bytes
    ) -> None:
        async def fake_stream(**_kw: object) -> AsyncIterator[str]:
            for word in ["Hello", " ", "world"]:
                yield word

        with (
            patch(
                "src.app.stream_cover_letter",
                side_effect=fake_stream,
            ),
            patch(
                "src.app.parse_resume",
                return_value="parsed resume text",
            ),
        ):
            resp = await client.post(
                "/api/generate/stream",
                files={"resume": ("cv.pdf", sample_pdf_bytes)},
                data={
                    "job_url": "https://example.com/job",
                    "language": "en",
                },
            )

        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        body = resp.text
        assert "data: Hello" in body
        assert "data: world" in body
        assert "data: [DONE]" in body


class TestHistory:
    async def test_empty_history(
        self, client: AsyncClient, db_with_user: None
    ) -> None:
        resp = await client.get("/api/history")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_history(
        self, client: AsyncClient, db_with_user: None
    ) -> None:
        from src.database import async_session

        async with async_session() as session:
            session.add(
                Generation(
                    user_id="test-user-id",
                    resume_filename="cv.pdf",
                    resume_text="resume text",
                    job_url="https://example.com",
                    job_text="job description",
                    cover_letter="cover letter text",
                    language="ru",
                )
            )
            await session.commit()

        resp = await client.get("/api/history")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["cover_letter"] == "cover letter text"
        assert data[0]["resume_filename"] == "cv.pdf"

    async def test_delete_history(
        self, client: AsyncClient, db_with_user: None
    ) -> None:
        from src.database import async_session

        async with async_session() as session:
            gen = Generation(
                user_id="test-user-id",
                resume_filename="cv.pdf",
                resume_text="resume text",
                job_text="job description",
                cover_letter="cover letter text",
            )
            session.add(gen)
            await session.commit()
            await session.refresh(gen)
            gen_id = gen.id

        resp = await client.delete(f"/api/history/{gen_id}")
        assert resp.status_code == 200

        resp = await client.get("/api/history")
        assert resp.json() == []

    async def test_delete_not_found(
        self, client: AsyncClient, db_with_user: None
    ) -> None:
        resp = await client.delete("/api/history/non-existent-id")
        assert resp.status_code == 404
