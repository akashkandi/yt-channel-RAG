# YT-Channel-RAG

Chat with any YouTube channel or playlist using RAG. Paste a URL, ask questions, get cited answers with clickable timestamps across multiple videos.

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://reactjs.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?logo=openai&logoColor=white)](https://openai.com)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://docker.com)

**[Live Demo](https://yt-channel-rag.onrender.com)** . **[API Docs](https://yt-channel-rag-backend.onrender.com/docs)**
---

## Features

- Load any YouTube channel, playlist, or video URL
- Full RAG pipeline — chunking, vector embeddings, semantic retrieval, cited generation
- **Cross-Video Synthesis** — when an answer spans multiple videos, the system explains how each video approaches the topic differently
- Every citation links to the exact timestamp in the source video
- Automatic retrieval quality scoring on every response
- Dockerized for one-command deployment

---

## Tech Stack

| | |
|---|---|
| Backend | Python 3.11 + FastAPI |
| Frontend | React 18 |
| Vector Database | ChromaDB |
| Embeddings | OpenAI text-embedding-3-small |
| LLM | GPT-4o-mini |
| Deployment | Docker + docker-compose |

---

## Setup

```bash
git clone https://github.com/akashkandi/yt-channel-RAG.git
cd yt-channel-RAG/backend

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:
```
OPENAI_API_KEY=sk-...
YOUTUBE_API_KEY=AIza...
SUPADATA_API_KEY=...
```

```bash
# Backend
uvicorn main:app --reload

# Frontend (new terminal)
cd ../frontend && npm install && npm start

# Or with Docker
docker-compose up
```

---

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/ingest` | Load a YouTube channel, playlist, or video |
| `POST` | `/ask` | Ask a question → cited answer + synthesis |
| `GET` | `/videos` | List ingested videos |
| `GET` | `/stats` | Knowledge base statistics |
| `GET` | `/docs` | Swagger UI |

---

## Project Structure

```
yt-channel-rag/
├── backend/
│   ├── main.py        # FastAPI endpoints
│   ├── ingestor.py    # YouTube ingestion pipeline
│   ├── embedder.py    # ChromaDB + OpenAI embeddings
│   ├── retriever.py   # RAG + cross-video synthesis
│   └── Dockerfile
├── frontend/
│   └── src/App.js
└── docker-compose.yml
```

---

Built by **Akash Kandi** — MS Computer Science · [LinkedIn](https://linkedin.com/in/akashkandi)
