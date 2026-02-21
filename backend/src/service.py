import logging
from typing import Any
from urllib.parse import urlparse

from langchain_core.messages import BaseMessage

from src.chain import get_chain
from src.job_scraper import scrape_job
from src.resume_parser import parse_resume

logger = logging.getLogger(__name__)


class GenerationError(Exception):
    """Raised when cover letter generation fails."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.status_code = status_code


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        msg = f"Invalid URL: {url}. Must be an HTTP(S) link."
        raise GenerationError(msg, status_code=400)


def _log_token_usage(usage: dict[str, Any]) -> None:
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    details = usage.get("input_token_details", {})
    cache_read = details.get("cache_read", 0)
    cache_creation = details.get("cache_creation", 0)
    uncached = input_tokens - cache_read

    logger.info(
        "Token usage: input=%d (cached=%d, new=%d, "
        "cache_creation=%d), output=%d, total=%d",
        input_tokens,
        cache_read,
        uncached,
        cache_creation,
        output_tokens,
        input_tokens + output_tokens,
    )


async def _resolve_job_description(
    job_url: str | None,
    job_text: str | None,
) -> str:
    if job_text and job_text.strip():
        logger.info("Using provided job text (%d chars)", len(job_text))
        return job_text.strip()

    if not job_url:
        msg = "Provide either a job URL or job description text."
        raise GenerationError(msg, status_code=400)

    _validate_url(job_url)

    try:
        return await scrape_job(job_url)
    except Exception as exc:
        logger.exception("Failed to scrape job URL: %s", job_url)
        msg = f"Could not fetch job page: {exc}"
        raise GenerationError(msg, status_code=422) from exc


async def generate_cover_letter(
    resume_data: bytes,
    filename: str,
    *,
    job_url: str | None = None,
    job_text: str | None = None,
    language: str = "ru",
) -> str:
    try:
        resume_text = parse_resume(resume_data, filename)
    except ValueError as exc:
        raise GenerationError(str(exc), status_code=400) from exc

    if not resume_text.strip():
        msg = "Could not extract text from the resume."
        raise GenerationError(msg, status_code=400)

    job_description = await _resolve_job_description(job_url, job_text)

    chain = get_chain()
    logger.info(
        "Generating cover letter (lang=%s, resume=%d chars, job=%d chars)",
        language,
        len(resume_text),
        len(job_description),
    )

    try:
        message: BaseMessage = await chain.ainvoke(
            {
                "resume_text": resume_text,
                "job_description": job_description,
                "language": language,
            }
        )
    except Exception as exc:
        logger.exception("LLM call failed")
        msg = f"LLM generation failed: {exc}"
        raise GenerationError(msg, status_code=502) from exc

    usage = getattr(message, "usage_metadata", None)
    if usage:
        _log_token_usage(usage)

    return str(message.content)
