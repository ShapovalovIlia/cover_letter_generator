import logging

from src.chain import get_chain
from src.job_scraper import scrape_job
from src.resume_parser import parse_resume

logger = logging.getLogger(__name__)


class GenerationError(Exception):
    """Raised when cover letter generation fails."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.status_code = status_code


async def generate_cover_letter(
    resume_data: bytes,
    filename: str,
    job_url: str,
    language: str = "ru",
) -> str:
    try:
        resume_text = parse_resume(resume_data, filename)
    except ValueError as exc:
        raise GenerationError(str(exc), status_code=400) from exc

    if not resume_text.strip():
        msg = "Could not extract text from the resume."
        raise GenerationError(msg, status_code=400)

    try:
        job_description = await scrape_job(job_url)
    except Exception as exc:
        logger.exception("Failed to scrape job URL: %s", job_url)
        msg = f"Could not fetch job page: {exc}"
        raise GenerationError(msg, status_code=422) from exc

    chain = get_chain()
    logger.info(
        "Generating cover letter (lang=%s, resume=%d chars, job=%d chars)",
        language,
        len(resume_text),
        len(job_description),
    )

    try:
        return await chain.ainvoke(
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
