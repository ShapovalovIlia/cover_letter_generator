import io
import logging
from collections.abc import Callable

import docx
import pymupdf

logger = logging.getLogger(__name__)

_SUPPORTED_EXTENSIONS = (".pdf", ".docx")


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
    ext = "." + filename.rsplit(".", maxsplit=1)[-1].lower()

    parser = _PARSERS.get(ext)
    if parser is None:
        msg = (
            f"Unsupported file format: {filename}. "
            f"Use {', '.join(_SUPPORTED_EXTENSIONS)}."
        )
        raise ValueError(msg)

    logger.info("Parsing resume '%s' (%s)", filename, ext)
    return parser(data)
