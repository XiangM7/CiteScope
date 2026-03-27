# CiteScope

CiteScope is a local-first MVP for grounded research assistance. Users upload PDFs or add web pages, the backend parses and chunks the content, stores chunk metadata in SQLite, indexes embeddings in Chroma, retrieves relevant evidence for a question, and returns an answer with inspectable citations and retrieved snippets. A small evaluation module runs baseline retrieval and citation checks against predefined cases.

## Architecture Summary

- Frontend: Next.js + TypeScript + Tailwind CSS
- Backend: FastAPI + SQLAlchemy + Pydantic
- Database: SQLite
- Vector store: Chroma with persistent local storage
- PDF parsing: PyMuPDF
- Web parsing: `httpx` + BeautifulSoup with simple readability-style extraction heuristics
- Default local providers:
  - Embeddings use a deterministic `HashingVectorizer`-based embedding service
  - Answers use deterministic extractive synthesis from retrieved evidence
- Optional remote providers:
  - Switch to any OpenAI-compatible chat or embedding endpoint via environment variables

## Folder Structure

```text
.
├── backend
│   ├── app
│   │   ├── core
│   │   ├── db
│   │   ├── models
│   │   ├── routers
│   │   ├── schemas
│   │   ├── services
│   │   └── utils
│   ├── data
│   └── requirements.txt
├── frontend
│   ├── app
│   ├── components
│   └── lib
└── .env.example
```

## Setup Instructions

### 1. Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
uvicorn app.main:app --reload --app-dir backend
```

The backend starts on `http://localhost:8000`.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

The frontend starts on `http://localhost:3000`.

## Environment Variables

### Backend

- `DATABASE_URL`: SQLite connection string. Default points at `backend/data/citescope.db`.
- `UPLOADS_DIR`: local directory for uploaded PDFs.
- `CHROMA_DIR`: local directory for persistent Chroma data.
- `CORS_ORIGINS`: comma-separated frontend origins.
- `CHUNK_SIZE_CHARS`: paragraph chunk target size.
- `CHUNK_OVERLAP_CHARS`: overlap copied into the next chunk.
- `RETRIEVAL_TOP_K`: default number of retrieved chunks.
- `REQUEST_TIMEOUT_SECONDS`: timeout for web fetches and remote model calls.
- `HASHING_DIMENSIONS`: dimensions for the local deterministic embedding service.

### Answer Provider

- `LLM_PROVIDER`: `local` or `openai_compatible`.
- `LLM_BASE_URL`: base URL for an OpenAI-compatible chat endpoint.
- `LLM_API_KEY`: bearer token for the chat endpoint.
- `LLM_MODEL`: model name for the chat endpoint.

### Embedding Provider

- `EMBEDDING_PROVIDER`: `local` or `openai_compatible`.
- `EMBEDDING_BASE_URL`: base URL for an OpenAI-compatible embeddings endpoint.
- `EMBEDDING_API_KEY`: bearer token for the embeddings endpoint.
- `EMBEDDING_MODEL`: model name for the embeddings endpoint.

### Frontend

- `NEXT_PUBLIC_API_BASE_URL`: FastAPI base URL. Defaults to `http://localhost:8000`.

## How Ingestion Works

1. `POST /documents/upload` stores PDF files on the local filesystem and creates a `documents` row with status `uploaded`.
2. `POST /documents/web` stores a web source row with the original URL and status `uploaded`.
3. `POST /documents/{document_id}/index` parses the source:
   - PDFs are read with PyMuPDF page by page.
   - Web pages are fetched with `httpx` and reduced to readable body text using BeautifulSoup heuristics.
4. The chunker groups paragraphs into configurable chunks with overlap.
5. Each chunk stores:
   - `document_id`
   - `chunk_index`
   - `page_number` for PDFs when available
   - `section_title`
   - `metadata_json`
6. Chunks are inserted into SQLite and then upserted into Chroma with matching metadata.
7. Successful documents move to `indexed`. Failures move to `failed`.

## How Retrieval Works

1. The embedding service converts all chunks into vectors.
2. Chroma persists those vectors locally.
3. `POST /chat/ask` embeds the incoming question and retrieves top-k chunks.
4. The API returns both the answer and the retrieved chunk payloads so retrieval remains visible in the UI.

The default local embedding service is intentionally deterministic and inspectable. It uses a hashing vectorizer rather than a neural embedding model so the project runs locally without external dependencies. You can switch to a remote embedding endpoint later by setting `EMBEDDING_PROVIDER=openai_compatible`.

## How Grounded Answers Work

1. Retrieved chunks are passed to the answer service.
2. The answer service uses a strict grounded-answer prompt when `LLM_PROVIDER=openai_compatible`.
3. The default `local` answer provider ranks question-relevant sentences from retrieved chunks and builds a concise extractive answer from that evidence only.
4. If no sentence is sufficiently supported, the answer explicitly says evidence is insufficient.

This keeps the MVP runnable out of the box while preserving a clean provider abstraction for later LLM upgrades.

## How Citations Work

- Citations are always built from retrieved chunk metadata.
- PDF citations include document title, chunk id, and page number when available.
- Web citations include document title, chunk id, and source URL.
- The chat UI shows both the compact citation list and the full retrieved evidence snippets.

## How Evaluation Works

- After a document is indexed, CiteScope auto-generates a few lightweight eval cases from representative chunks.
- Each eval case stores:
  - `question`
  - `reference_answer`
  - `expected_document_id`
  - `expected_page_numbers`
- `POST /eval/run` executes all eval cases through the same retrieval and answer pipeline.
- Each result stores:
  - `retrieved_chunk_ids`
  - `answer_text`
  - `citation_json`
  - `retrieval_hit`
  - `citation_correct`
  - `answer_score`

Scoring is intentionally simple:

- `retrieval_hit` checks whether retrieved chunks include the expected document and page.
- `citation_correct` checks whether returned citations include the expected document and page.
- `answer_score` is a token-overlap heuristic against the reference answer.

## Main Routes

- `POST /documents/upload`
- `POST /documents/web`
- `GET /documents`
- `GET /documents/{document_id}`
- `POST /documents/{document_id}/index`
- `POST /chat/ask`
- `GET /eval/cases`
- `POST /eval/run`
- `GET /eval/results`

## Known Limitations

- The default `local` answer provider is extractive, not a full generative LLM.
- The default `local` embedding provider is lexical and deterministic, not semantic in the same way as modern neural embeddings.
- No OCR is included for scanned PDFs.
- Web extraction is heuristic and may be imperfect on heavily scripted sites.
- Eval cases are auto-generated from indexed text for MVP simplicity rather than hand-curated.
- There is no authentication or multi-user separation.

## Future Improvements

- Add OCR fallback for scanned PDFs.
- Support manual eval case authoring in the UI.
- Add PDF page preview links and source detail views.
- Add reranking and hybrid lexical/vector retrieval.
- Add streaming answers and richer citation formatting.
- Support collections, tagging, and source deletion workflows.
