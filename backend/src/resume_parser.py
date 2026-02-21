import io
import logging
from collections.abc import Callable
from pathlib import PurePath

import docx
import pymupdf

logger = logging.getLogger(__name__)


def _parse_pdf(data: bytes) -> str:
    with pymupdf.open(stream=data, filetype="pdf") as doc:  # type: ignore[no-untyped-call]
        pages: list[str] = [page.get_text() for page in doc]
        return "\n".join(pages).strip()


def _parse_docx(data: bytes) -> str:
    doc = docx.Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


_PARSERS: dict[str, Callable[[bytes], str]] = {
    ".pdf": _parse_pdf,
    ".docx": _parse_docx,
}


def parse_resume(data: bytes, filename: str) -> str:
    ext = PurePath(filename).suffix.lower()

    parser = _PARSERS.get(ext)
    if parser is None:
        supported = ", ".join(_PARSERS)
        msg = f"Unsupported file format: {filename}. Use {supported}."
        raise ValueError(msg)

    logger.info("Parsing resume '%s' (%s)", filename, ext)
    return parser(data)
