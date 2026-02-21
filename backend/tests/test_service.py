from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from src.service import GenerationError, generate_cover_letter

pytestmark = pytest.mark.asyncio


def _fake_message(content: str) -> SimpleNamespace:
    return SimpleNamespace(content=content, usage_metadata=None)


class TestGenerateCoverLetter:
    async def test_unsupported_format(self) -> None:
        with pytest.raises(GenerationError, match="Unsupported") as exc_info:
            await generate_cover_letter(
                b"data", "file.txt", job_url="https://x.com"
            )
        assert exc_info.value.status_code == 400

    async def test_empty_resume(self, sample_pdf_bytes: bytes) -> None:
        with (
            patch("src.service.parse_resume", return_value="   "),
            pytest.raises(
                GenerationError, match="Could not extract"
            ) as exc_info,
        ):
            await generate_cover_letter(
                sample_pdf_bytes, "r.pdf", job_url="https://x.com"
            )
        assert exc_info.value.status_code == 400

    async def test_invalid_url(self) -> None:
        with (
            patch(
                "src.service.parse_resume",
                return_value="John Doe, engineer",
            ),
            pytest.raises(GenerationError, match="Invalid URL") as exc_info,
        ):
            await generate_cover_letter(b"data", "r.pdf", job_url="not-a-url")
        assert exc_info.value.status_code == 400

    async def test_missing_job_input(self) -> None:
        with (
            patch(
                "src.service.parse_resume",
                return_value="John Doe, engineer",
            ),
            pytest.raises(GenerationError, match="Provide either") as exc_info,
        ):
            await generate_cover_letter(b"data", "r.pdf")
        assert exc_info.value.status_code == 400

    async def test_scrape_failure(self) -> None:
        with (
            patch(
                "src.service.parse_resume",
                return_value="John Doe, engineer",
            ),
            patch(
                "src.service.scrape_job",
                side_effect=RuntimeError("connection failed"),
            ),
            pytest.raises(
                GenerationError, match="Could not fetch"
            ) as exc_info,
        ):
            await generate_cover_letter(
                b"data", "r.pdf", job_url="https://x.com"
            )
        assert exc_info.value.status_code == 422

    async def test_llm_failure(self) -> None:
        mock_chain = AsyncMock()
        mock_chain.ainvoke = AsyncMock(side_effect=RuntimeError("LLM down"))

        with (
            patch(
                "src.service.parse_resume",
                return_value="John Doe, engineer",
            ),
            patch(
                "src.service.scrape_job",
                new_callable=AsyncMock,
                return_value="Python developer needed",
            ),
            patch("src.service.get_chain", return_value=mock_chain),
            pytest.raises(
                GenerationError, match="LLM generation failed"
            ) as exc_info,
        ):
            await generate_cover_letter(
                b"data", "r.pdf", job_url="https://x.com"
            )
        assert exc_info.value.status_code == 502

    async def test_success_with_url(self) -> None:
        expected = "Dear Hiring Manager..."
        mock_chain = AsyncMock()
        mock_chain.ainvoke = AsyncMock(
            return_value=_fake_message(expected),
        )

        with (
            patch(
                "src.service.parse_resume",
                return_value="John Doe, engineer",
            ),
            patch(
                "src.service.scrape_job",
                new_callable=AsyncMock,
                return_value="Python developer needed",
            ) as mock_scrape,
            patch("src.service.get_chain", return_value=mock_chain),
        ):
            result = await generate_cover_letter(
                b"data", "r.pdf", job_url="https://x.com", language="en"
            )

        assert result == expected
        mock_scrape.assert_awaited_once_with("https://x.com")
        call_args = mock_chain.ainvoke.call_args[0][0]
        assert call_args["language"] == "en"
        assert call_args["resume_text"] == "John Doe, engineer"
        assert call_args["job_description"] == "Python developer needed"

    async def test_success_with_job_text(self) -> None:
        expected = "Cover letter text"
        mock_chain = AsyncMock()
        mock_chain.ainvoke = AsyncMock(
            return_value=_fake_message(expected),
        )

        with (
            patch(
                "src.service.parse_resume",
                return_value="John Doe, engineer",
            ),
            patch(
                "src.service.scrape_job",
                new_callable=AsyncMock,
            ) as mock_scrape,
            patch("src.service.get_chain", return_value=mock_chain),
        ):
            result = await generate_cover_letter(
                b"data",
                "r.pdf",
                job_text="Python developer needed at Acme Corp",
            )

        assert result == expected
        mock_scrape.assert_not_awaited()
        call_args = mock_chain.ainvoke.call_args[0][0]
        assert "Acme Corp" in call_args["job_description"]

    async def test_success_with_token_usage(self) -> None:
        msg = SimpleNamespace(
            content="Hello!",
            usage_metadata={
                "input_tokens": 100,
                "output_tokens": 50,
                "input_token_details": {
                    "cache_read": 80,
                    "cache_creation": 0,
                },
            },
        )
        mock_chain = AsyncMock()
        mock_chain.ainvoke = AsyncMock(return_value=msg)

        with (
            patch(
                "src.service.parse_resume",
                return_value="resume text",
            ),
            patch(
                "src.service.scrape_job",
                new_callable=AsyncMock,
                return_value="job desc",
            ),
            patch("src.service.get_chain", return_value=mock_chain),
        ):
            result = await generate_cover_letter(
                b"data", "r.pdf", job_url="https://x.com"
            )

        assert result == "Hello!"
