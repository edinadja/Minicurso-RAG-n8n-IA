# RAG na Prática: Integrando Python, n8n e IA Generativa

Minicurso introdutório/intermediário (1h40) para estudantes de graduação em TI.
Construção prática de uma aplicação de **Retrieval-Augmented Generation (RAG)**
combinando **n8n** (orquestração), **Python** (processamento de documentos) e
**IA generativa via OpenRouter** (embeddings e LLM).

## Arquitetura

```
                        ┌──────────────┐
   documento ─────────▶ │     n8n      │  orquestrador do fluxo
                        │ (webhooks,   │
   pergunta ──────────▶ │  HTTP calls) │────────▶ OpenRouter (LLM)
                        └──────┬───────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │   Python API      │  extração, chunking,
                      │  (FastAPI)        │  embeddings (OpenRouter),
                      │                   │  busca vetorial
                      └────────┬─────────┘
                               ▼
                      ┌─────────────────┐
                      │     Qdrant        │  banco vetorial
                      └─────────────────┘
```

- **n8n**: recebe o documento/pergunta, chama a Python API e o LLM (via
  OpenRouter), monta o fluxo visualmente — é o "orquestrador" da ementa.
- **Python API**: faz as etapas de processamento — extração de texto,
  chunking, geração de embeddings (via OpenRouter) e busca por similaridade
  no Qdrant.
- **Qdrant**: banco de dados vetorial onde os embeddings dos chunks ficam
  armazenados.
- **OpenRouter**: fornece o modelo de embeddings e o LLM de chat através de
  uma única chave de API compatível com OpenAI. Optamos por essa opção para
  manter o setup dos alunos simples: sem download de modelos, sem exigir
  RAM/CPU do notebook, funciona em qualquer máquina com internet.

## Estrutura de pastas

```
rag-minicurso/
├── docker-compose.yml        # sobe n8n, qdrant e a python-api
├── .env.example                # copiar para .env e colar sua chave do OpenRouter
├── docs/                        # documentos de exemplo para os testes
│   └── exemplo_politica_home_office.txt
├── python-api/                  # aplicação Python (FastAPI)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                   # endpoints /ingest e /search
│   ├── extraction.py             # extração de texto (.txt/.pdf)
│   ├── chunking.py               # divisão do texto em chunks
│   ├── embeddings.py             # geração de embeddings via OpenRouter
│   └── vector_store.py           # integração com o Qdrant
└── n8n/
    └── workflows/
        ├── starter-aluno.json          # esqueleto para os alunos montarem em aula
        └── solucao-rag-completo.json   # fluxo completo de referência (instrutor)
```

## Pré-requisitos

- Docker Desktop instalado e rodando (Windows/Mac/Linux)
- Internet estável no local da aula (todo o fluxo depende do OpenRouter)
- Uma chave de API do OpenRouter — crie em https://openrouter.ai/settings/keys
  (não pede cartão de crédito para criar a conta)

## Sobre a chave de API (leia antes da aula)

O jeito mais simples é o **instrutor** criar uma única chave e compartilhar
com a turma (via `.env` já preenchido, distribuído no início da aula), com
um pequeno crédito pré-pago (ex.: US$ 5) na conta do OpenRouter.

- **Evite modelos `:free`** para uma turma inteira: o limite compartilhado é
  de cerca de 50 requisições/dia por chave, o que estoura rápido com vários
  alunos testando ao mesmo tempo.
- Modelos pagos como `meta-llama/llama-3.3-70b-instruct` custam centavos por
  milhão de tokens — o gasto de uma turma inteira no minicurso normalmente
  fica bem abaixo de US$ 1.
- Se preferir, cada aluno pode criar sua própria chave gratuita — nesse caso,
  cada um edita seu próprio `.env` com sua chave.

## Setup

```bash
# 1. Entrar na pasta do projeto
cd rag-minicurso

# 2. Criar o arquivo de variáveis de ambiente
cp .env.example .env
# Edite o .env e cole sua OPENROUTER_API_KEY

# 3. Subir os containers
docker compose up -d
```

Verifique se tudo subiu corretamente:

```bash
docker compose ps
```

Você deve ver 3 containers rodando: `rag_n8n`, `rag_qdrant` e `rag_python_api`.

## Acessos

| Serviço      | URL                              | Observação                          |
|--------------|-----------------------------------|--------------------------------------|
| n8n          | http://localhost:5678             | usuário `admin` / senha `minicurso123` |
| Python API   | http://localhost:8000/docs        | Swagger com todos os endpoints       |
| Qdrant       | http://localhost:6333/dashboard   | visualização das collections/vetores |

> Altere o usuário/senha do n8n no `docker-compose.yml`, se desejar.

## Importando os workflows no n8n

1. Acesse http://localhost:5678
2. Clique em **Workflows > Import from File**
3. Importe `n8n/workflows/starter-aluno.json` para os alunos completarem em
   aula (contém apenas os triggers e notas explicando cada passo)
4. No node de chamada ao LLM, crie uma credencial **Header Auth** com
   `Name = Authorization` e `Value = Bearer sk-or-sua-chave-aqui`
5. O arquivo `n8n/workflows/solucao-rag-completo.json` é a versão de
   referência do instrutor — útil para consulta ou para demonstrar o fluxo
   pronto no início/fim da aula.


## Testando manualmente (sem n8n) via Swagger

Abra http://localhost:8000/docs e:

1. Use o endpoint `POST /ingest` para enviar `docs/exemplo_politica_home_office.txt`
2. Confira em `GET /status` que os chunks foram indexados
3. Use `POST /search` com uma pergunta, ex.: `"Quantos dias de home office são permitidos?"`,
   para ver os chunks recuperados e o contexto montado

## Testando o fluxo completo via n8n (webhook)

Depois de montar/ativar o fluxo de pergunta e resposta:

```bash
curl -X POST http://localhost:5678/webhook/perguntar \
  -H "Content-Type: application/json" \
  -d '{"question": "Quantos dias de home office são permitidos por semana?"}'
```

## Discussão de limitações (sugestão para a parte final)

- Faça uma pergunta cuja resposta **não está** no documento e observe o
  modelo alucinar ou responder sem evidência.
- Compare o resultado ajustando o prompt para instruir o LLM a dizer
  "não sei" quando o contexto não tiver a resposta.
- Teste `top_k` diferente em `/search` (poucos ou muitos chunks) e discuta o
  impacto no contexto enviado ao LLM.

## Trocando de modelo

Basta alterar `OPENROUTER_EMBEDDING_MODEL` e `OPENROUTER_CHAT_MODEL` no
`.env` (e reiniciar `docker compose restart python-api`), além do campo
`model` no node HTTP Request do n8n. A lista completa de modelos disponíveis
está em https://openrouter.ai/models.

> Atenção: ao trocar o modelo de embeddings, a dimensão do vetor pode mudar.
> É necessário recriar a collection no Qdrant (apague-a pelo dashboard ou
> use um `QDRANT_COLLECTION` diferente no `.env`) antes de reindexar os
> documentos.

## Problemas comuns

- **Erro 401 no node do OpenRouter**: confira se a credencial Header Auth
  está com `Bearer ` (com espaço) antes da chave.
- **Erro 429 (rate limit)**: geralmente indica que a chave está usando um
  modelo `:free` com muitos alunos ao mesmo tempo — troque para um modelo
  pago barato.
- **`n8n` não enxerga `python-api`**: use sempre o nome do serviço do
  `docker-compose.yml` (`http://python-api:8000`), nunca `localhost`, pois
  os containers se comunicam pela rede interna do Docker.

## Encerrando o ambiente

```bash
docker compose down          # para os containers, mantém os dados
docker compose down -v       # para os containers e apaga os dados (reset total)
```
