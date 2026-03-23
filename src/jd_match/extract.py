import io
from pathlib import PurePosixPath

SUPPORTED = {".pdf", ".docx", ".md", ".txt", ".text"}
_MAX_PDF_PAGES = 5


def extract_text(filename: str, content: bytes) -> str:
    """Extract plain text from uploaded file bytes."""
    # Use only the basename to avoid path traversal; strip non-ASCII
    safe_name = PurePosixPath(filename).name
    ext = PurePosixPath(safe_name).suffix.lower()
    # Reject unexpected extensions (including empty)
    if ext not in SUPPORTED:
        raise ValueError("Unsupported file type. Use PDF, DOCX, MD, or TXT.")
    if ext == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(content))
        if len(reader.pages) > _MAX_PDF_PAGES:
            raise ValueError(f"PDF too long ({len(reader.pages)} pages, max {_MAX_PDF_PAGES})")
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    elif ext == ".docx":
        from docx import Document
        doc = Document(io.BytesIO(content))
        return "\n".join(p.text for p in doc.paragraphs)
    else:  # .md, .txt, .text
        return content.decode("utf-8", errors="replace")
