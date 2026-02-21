import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from src.config import settings
from src.logging_config import setup_logging
from src.service import (
    GenerationError,
    generate_cover_letter,
    stream_cover_letter,
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    setup_logging(settings.log_level)
    logging.getLogger(__name__).info("Application started")
    yield


app = FastAPI(title="Cover Letter Generator", lifespan=lifespan)

logger = logging.getLogger(__name__)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/generate")
async def generate(
    resume: UploadFile = File(...),
    job_url: str | None = Form(None),
    job_text: str | None = Form(None),
    language: str = Form("ru"),
) -> dict[str, str]:
    data = await resume.read()
    filename = resume.filename or "file.pdf"

    try:
        cover_letter = await generate_cover_letter(
            resume_data=data,
            filename=filename,
            job_url=job_url,
            job_text=job_text,
            language=language,
        )
    except GenerationError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=str(exc)
        ) from exc

    logger.info("Cover letter generated for '%s'", filename)
    return {"cover_letter": cover_letter}


@app.post("/api/generate/stream")
async def generate_stream(
    resume: UploadFile = File(...),
    job_url: str | None = Form(None),
    job_text: str | None = Form(None),
    language: str = Form("ru"),
) -> StreamingResponse:
    data = await resume.read()
    filename = resume.filename or "file.pdf"

    try:
        token_stream = stream_cover_letter(
            resume_data=data,
            filename=filename,
            job_url=job_url,
            job_text=job_text,
            language=language,
        )
    except GenerationError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=str(exc)
        ) from exc

    async def sse_generator() -> AsyncIterator[str]:
        try:
            async for token in token_stream:
                yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"
        except GenerationError as exc:
            yield f"error: {exc}\n\n"

    logger.info("Streaming cover letter for '%s'", filename)
    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
