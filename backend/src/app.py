import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import get_current_user, router as auth_router
from src.config import settings
from src.database import get_db, init_db
from src.logging_config import setup_logging
from src.models import Generation, User
from src.resume_parser import parse_resume
from src.service import (
    GenerationError,
    generate_cover_letter,
    stream_cover_letter,
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    setup_logging(settings.log_level)
    await init_db()
    logging.getLogger(__name__).info("Application started")
    yield


app = FastAPI(title="Cover Letter Generator", lifespan=lifespan)
app.include_router(auth_router)

logger = logging.getLogger(__name__)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


async def _save_generation(
    db: AsyncSession,
    user: User,
    filename: str,
    resume_text: str,
    job_url: str | None,
    job_text: str | None,
    cover_letter: str,
    language: str,
) -> Generation:
    gen = Generation(
        user_id=user.id,
        resume_filename=filename,
        resume_text=resume_text,
        job_url=job_url,
        job_text=job_text or "",
        cover_letter=cover_letter,
        language=language,
    )
    db.add(gen)
    await db.commit()
    await db.refresh(gen)
    return gen


@app.post("/api/generate")
async def generate(
    resume: UploadFile = File(...),
    job_url: str | None = Form(None),
    job_text: str | None = Form(None),
    language: str = Form("ru"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
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

    resume_text = ""
    try:
        resume_text = parse_resume(data, filename)
    except ValueError:
        pass

    await _save_generation(
        db,
        user,
        filename,
        resume_text,
        job_url,
        job_text,
        cover_letter,
        language,
    )

    logger.info("Cover letter generated for '%s'", filename)
    return {"cover_letter": cover_letter}


@app.post("/api/generate/stream")
async def generate_stream(
    resume: UploadFile = File(...),
    job_url: str | None = Form(None),
    job_text: str | None = Form(None),
    language: str = Form("ru"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
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

    resume_text = ""
    try:
        resume_text = parse_resume(data, filename)
    except ValueError:
        pass

    async def sse_generator() -> AsyncIterator[str]:
        full_text = ""
        try:
            async for token in token_stream:
                full_text += token
                yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"
        except GenerationError as exc:
            yield f"error: {exc}\n\n"
        else:
            await _save_generation(
                db,
                user,
                filename,
                resume_text,
                job_url,
                job_text,
                full_text,
                language,
            )

    logger.info("Streaming cover letter for '%s'", filename)
    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/history")
async def get_history(
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    stmt = (
        select(Generation)
        .where(Generation.user_id == user.id)
        .order_by(Generation.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    generations = result.scalars().all()

    return [
        {
            "id": g.id,
            "resume_filename": g.resume_filename,
            "job_url": g.job_url,
            "cover_letter": g.cover_letter,
            "language": g.language,
            "created_at": g.created_at.isoformat(),
        }
        for g in generations
    ]


@app.delete("/api/history/{generation_id}")
async def delete_history_entry(
    generation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    gen = await db.get(Generation, generation_id)
    if not gen or gen.user_id != user.id:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(gen)
    await db.commit()
    return {"status": "deleted"}
