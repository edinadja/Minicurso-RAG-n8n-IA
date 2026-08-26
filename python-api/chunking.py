"""
Etapa de CHUNKING: divide um texto longo em pedaços menores (chunks),
com sobreposição entre eles, para que cada trecho tenha contexto
suficiente para gerar embeddings e ser recuperado depois.
"""

from typing import List


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Divide o texto em chunks de aproximadamente `chunk_size` caracteres,
    com `overlap` caracteres de sobreposição entre chunks consecutivos.

    Uma sobreposição evita que uma informação importante seja "cortada"
    exatamente na fronteira entre dois chunks.
    """
    text = text.strip().replace("\r\n", "\n")
    if not text:
        return []

    if chunk_size <= overlap:
        raise ValueError("chunk_size deve ser maior que overlap")

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == text_length:
            break
        start = end - overlap

    return chunks
