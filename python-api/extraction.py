"""
Etapa de EXTRAÇÃO: lê o conteúdo bruto de um arquivo enviado pelo aluno
(.txt ou .pdf) e devolve o texto puro para as próximas etapas do RAG.
"""

import io
from pypdf import PdfReader


def extract_text(filename: str, content: bytes) -> str:
    lower_name = filename.lower()

    if lower_name.endswith(".pdf"):
        return _extract_pdf(content)

    if lower_name.endswith(".txt") or lower_name.endswith(".md"):
        return content.decode("utf-8", errors="ignore")

    raise ValueError(
        f"Formato de arquivo não suportado: '{filename}'. "
        "Use .txt, .md ou .pdf."
    )


def _extract_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    pages_text = []
    for page in reader.pages:
        pages_text.append(page.extract_text() or "")
    return "\n".join(pages_text)
