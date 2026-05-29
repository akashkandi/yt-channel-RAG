<div align="center">

# 🎬 YT-Channel-RAG

### Chat with any YouTube channel using RAG + Cross-Video Synthesis

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-FF6B35?style=for-the-badge)](https://trychroma.com)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)

[Live Demo](https://your-url.onrender.com) · [API Docs](https://your-url.onrender.com/docs) · [LinkedIn](https://linkedin.com/in/akashkandi)

</div>

---

## Overview

YT-Channel-RAG ingests an entire YouTube channel or playlist and turns it into a searchable knowledge base. Ask any question and get accurate, cited answers with clickable timestamps — sourced from across multiple videos simultaneously.

Unlike basic "chat with YouTube" tools that process one video at a time, this system builds a persistent vector store across an entire channel and adds **Cross-Video Synthesis** — automatically comparing how different videos in the channel approach the same topic.

---

## Features

- 🔗 **Any YouTube URL** — channel, playlist, or video link
- 🧠 **Full RAG Pipeline** — semantic chunking → vector embeddings → retrieval → cited generation
- ✦ **Cross-Video Synthesis** — synthesizes perspectives across multiple videos in a single answer
- 📍 **Timestamp Citations** — every source links to the exact moment in the video
- 📊 **Retrieval Quality Scoring** — each answer is automatically evaluated by a second LLM call
- 🐳 **Docker Ready** — single `docker-compose up` to run the full stack

---

## Tech Stack

| Component | Technology |
|---|---|
| Backend API | Python 3.11 + FastAPI |
| Frontend | React 18 |
| Vector Database | ChromaDB (cosine similarity) |
| Embeddings | OpenAI `text-embedding-3-small` |
| Language Model | GPT-4o-mini |
| Transcript Fetching | Supadata API |
| YouTube Metadata | Google YouTube Data API v3 |
| Deployment | Docker + docker-compose |

---

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│                     INGESTION PIPELINE                   │
│                                                         │
│  YouTube URL  ──►  YouTube Data API  ──►  Video List    │
│                                               │         │
│                    Supadata API  ◄────────────┘         │
│                         │                               │
│                    Transcripts                          │
│                         │                               │
│              Chunk text (~300 words)                    │
│              + preserve timestamp & video metadata      │
│                         │                               │
│         OpenAI text-embedding-3-small                   │
│              (1536-dim vectors)                         │
│                         │                               │
│              ChromaDB Vector Store                      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                      QUERY PIPELINE                      │
│                                                         │
│  User Question  ──►  Embed Question                     │
│                            │                            │
│               Cosine Similarity Search                  │
│               ChromaDB → Top 5 Chunks                   │
│                            │                            │
│          GPT-4o-mini generates cited answer             │
│          with [Source N] + timestamp links              │
│                            │                            │
│     ┌──────────────────────┴───────────────────┐       │
│     │                                           │       │
│  2+ videos?                              Always runs    │
│     │                                           │       │
│  Cross-Video Synthesis              Retrieval Quality   │
│  (2nd LLM call)                     Score 1-10         │
│                                     (3rd LLM call)      │
└─────────────────────────────────────────────────────────┘
```

---

## Notable Technical Decisions

**Transcript Fetching via Supadata API**
YouTube aggressively rate-limits automated transcript requests. After evaluating `youtube-transcript-api` (IP blocks after ~10 requests), rotating datacenter proxies (407 auth errors), and cookie-based auth (removed in latest library versions), Supadata was selected as the production-grade solution — handling bot detection at scale without IP management.

**Timestamp Metadata Preservation**
Every text chunk stores `video_id`, `video_title`, `start_time`, and `youtube_link` as ChromaDB metadata. The chunking logic tracks the start timestamp of each 300-word window so citations link to the exact moment — not just the video.

**ChromaDB Collection Hot-Swap**
Re-ingesting a new channel requires replacing the vector collection without a server restart. Solved by directly updating `embedder.collection` at the module level after recreation — ensuring all active FastAPI routes reference the fresh collection immediately.

---

## Getting Started

### Prerequisites
- Python 3.11+, Node.js 18+
- [OpenAI API key](https://platform.openai.com)
- [Google Cloud API key](https://console.cloud.google.com) (YouTube Data API v3 enabled)
- [Supadata API key](https://supadata.ai) (free tier available)

### Installation

```bash
git clone https://github.com/akashkandi/yt-channel-RAG.git
cd yt-channel-RAG

# Backend
cd backend
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt

# Create backend/.env
OPENAI_API_KEY=sk-...
YOUTUBE_API_KEY=AIza...
SUPADATA_API_KEY=...

# Start backend
uvicorn main:app --reload

# Frontend (new terminal)
cd ../frontend && npm install && npm start
```

### Docker

```bash
docker-compose up
# Frontend → http://localhost:3000
# Backend  → http://localhost:8000
# API Docs → http://localhost:8000/docs
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/ingest` | Ingest a YouTube channel, playlist, or video URL |
| `POST` | `/ask` | Ask a question → answer + citations + synthesis |
| `GET` | `/videos` | List all ingested videos |
| `GET` | `/stats` | Knowledge base stats |
| `GET` | `/docs` | Swagger UI |

---

## Project Structure

```
yt-channel-rag/
├── backend/
│   ├── main.py          # FastAPI app + all endpoints
│   ├── ingestor.py      # YouTube ingestion pipeline
│   ├── embedder.py      # ChromaDB + OpenAI embeddings
│   ├── retriever.py     # RAG pipeline + cross-video synthesis
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   └── App.css
│   └── Dockerfile
└── docker-compose.yml
```

---

<div align="center">

Built by **Akash Kandi** — MS Computer Science

[GitHub](https://github.com/akashkandi) · [LinkedIn](https://linkedin.com/in/akashkandi)

</div>
