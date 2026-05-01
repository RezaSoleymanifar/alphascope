"""PDF download + text extraction. Cached on disk."""
from __future__ import annotations

from pathlib import Path

import httpx
import pypdf

CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "papers"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def download_pdf(url: str, paper_id: str, force: bool = False) -> Path:
    """Download a PDF to data/papers/{paper_id}.pdf. Returns path."""
    out = CACHE_DIR / f"{paper_id}.pdf"
    if out.exists() and not force:
        return out
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; AlphaArchive/0.1; +https://alpha-archive.io)",
    }
    with httpx.Client(headers=headers, follow_redirects=True, timeout=60) as client:
        r = client.get(url)
        r.raise_for_status()
        out.write_bytes(r.content)
    return out


def extract_text(pdf_path: Path, max_pages: int = 50) -> str:
    """Extract plain text from a PDF (first `max_pages` pages)."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)
    reader = pypdf.PdfReader(str(pdf_path))
    parts = []
    for i, page in enumerate(reader.pages[:max_pages]):
        try:
            parts.append(page.extract_text() or "")
        except Exception as e:
            parts.append(f"[page {i} extract error: {e}]")
    text = "\n\n".join(parts)
    return _normalize(text)


def _normalize(s: str) -> str:
    import re
    s = s.replace("\r", "\n")
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


if __name__ == "__main__":
    # Smoke: pull a known arXiv paper
    pdf = download_pdf("https://arxiv.org/pdf/2403.16527.pdf", "test_arxiv")
    print(f"downloaded -> {pdf}, size={pdf.stat().st_size}")
    txt = extract_text(pdf, max_pages=3)
    print(f"text first 800 chars:\n{txt[:800]}")
