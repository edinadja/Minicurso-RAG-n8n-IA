"""
Etapa de EMBEDDINGS: transforma um texto em um vetor numérico que
representa seu significado semântico. Chunks e perguntas usam a MESMA
função de embedding para que possam ser comparados no banco vetorial.

Usa o OpenRouter (API compatível com a OpenAI), que dá acesso a modelos
de embeddings de diferentes provedores com uma única chave.
"""

import os
from openai import OpenAI

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_EMBEDDING_MODEL = os.getenv("OPENROUTER_EMBEDDING_MODEL", "openai/text-embedding-3-small")

_client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)


def get_embedding(text: str) -> list[float]:
    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY não configurada. Copie .env.example para .env "
            "e cole sua chave gerada em https://openrouter.ai/settings/keys"
        )
    response = _client.embeddings.create(
        model=OPENROUTER_EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding


def get_embedding_dimension() -> int:
    """Descobre a dimensão do vetor gerando um embedding de teste.
    Usado para criar a collection no Qdrant com o tamanho correto."""
    sample = get_embedding("dimensão de teste")
    return len(sample)
