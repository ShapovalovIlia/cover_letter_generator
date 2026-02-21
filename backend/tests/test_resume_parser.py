import pytest

from src.resume_parser import parse_resume


class TestParseResume:
    def test_pdf(self, sample_pdf_bytes: bytes) -> None:
        text = parse_resume(sample_pdf_bytes, "resume.pdf")
        assert "John Doe" in text
        assert "Software Engineer" in text

    def test_pdf_uppercase_ext(self, sample_pdf_bytes: bytes) -> None:
        text = parse_resume(sample_pdf_bytes, "resume.PDF")
        assert "John Doe" in text

    def test_docx(self, sample_docx_bytes: bytes) -> None:
        text = parse_resume(sample_docx_bytes, "resume.docx")
        assert "Jane Smith" in text
        assert "Product Manager" in text

    def test_docx_uppercase_ext(self, sample_docx_bytes: bytes) -> None:
        text = parse_resume(sample_docx_bytes, "resume.DOCX")
        assert "Jane Smith" in text

    def test_unsupported_format_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported file format"):
            parse_resume(b"data", "resume.txt")

    def test_unsupported_format_no_ext(self) -> None:
        with pytest.raises(ValueError, match="Unsupported file format"):
            parse_resume(b"data", "resume")
