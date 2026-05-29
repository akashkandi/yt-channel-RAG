import os
import importlib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="YouTube Knowledge Base API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str
    n_results: int = 5


class IngestRequest(BaseModel):
    channel_id: str


@app.get("/")
def root():
    return {"status": "running", "message": "YouTube Knowledge Base API"}


@app.get("/health")
def health():
    from embedder import get_collection
    collection = get_collection()
    return {
        "status": "healthy",
        "chunks_in_db": collection.count()
    }


@app.get("/videos")
def get_videos():
    from ingestor import load_chunks
    chunks = load_chunks()
    if not chunks:
        return {"videos": [], "total": 0}

    seen = set()
    videos = []
    for chunk in chunks:
        vid_id = chunk["video_id"]
        if vid_id not in seen:
            seen.add(vid_id)
            videos.append({
                "video_id": vid_id,
                "title": chunk["video_title"],
                "url": f"https://www.youtube.com/watch?v={vid_id}"
            })

    return {"videos": videos, "total": len(videos)}


@app.post("/ask")
def ask(request: QuestionRequest):
    from embedder import get_collection
    from retriever import ask_question

    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    collection = get_collection()
    if collection.count() == 0:
        raise HTTPException(status_code=400, detail="No videos ingested yet.")

    result = ask_question(request.question, request.n_results)
    return result


@app.post("/ingest")
async def ingest(request: IngestRequest):
    from ingestor import ingest_channel, save_chunks
    import chromadb

    channel_input = request.channel_id.strip()

    # --- Resolve channel/playlist ID ---
    if "youtube.com/@" in channel_input:
        handle = channel_input.split("/@")[-1].split("/")[0].split("?")[0]
        try:
            from googleapiclient.discovery import build
            youtube = build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY"))
            response = youtube.channels().list(
                part="id,snippet",
                forHandle=handle
            ).execute()
            if not response.get("items"):
                raise HTTPException(status_code=404, detail=f"Channel @{handle} not found")
            channel_id = response["items"][0]["id"]
            channel_name = response["items"][0]["snippet"]["title"]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not resolve channel: {str(e)}")

    elif "youtube.com/channel/" in channel_input:
        channel_id = channel_input.split("/channel/")[-1].split("/")[0].split("?")[0]
        channel_name = channel_id

    elif "list=" in channel_input:
        channel_id = channel_input.split("list=")[-1].split("&")[0]
        channel_name = f"Playlist {channel_id[:20]}"

    elif channel_input.startswith("PL") or channel_input.startswith("FL"):
        channel_id = channel_input
        channel_name = f"Playlist {channel_id[:20]}"

    elif channel_input.startswith("UC"):
        channel_id = channel_input
        channel_name = channel_id

    else:
        raise HTTPException(
            status_code=400,
            detail="Provide a YouTube channel URL (youtube.com/@channel), playlist URL, or channel ID starting with UC"
        )

    try:
        # Step 1 — delete old ChromaDB collection
        import embedder
        try:
            embedder.chroma_client.delete_collection("youtube_knowledge_base")
            print("✅ Deleted old ChromaDB collection")
        except Exception:
            pass

        # Step 2 — create fresh collection directly
        fresh_collection = embedder.chroma_client.get_or_create_collection(
            name="youtube_knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )
        # Update the module-level collection reference
        embedder.collection = fresh_collection
        print("✅ Created fresh ChromaDB collection")

        # Step 3 — ingest videos
        chunks = ingest_channel(channel_id, max_videos=50)
        if not chunks:
            raise HTTPException(status_code=400, detail="No transcripts found for this channel or playlist")

        # Step 4 — save cache
        save_chunks(chunks)

        # Step 5 — embed into fresh collection
        embedder.embed_chunks(chunks)

        return {
            "status": "success",
            "channel_id": channel_id,
            "channel_name": channel_name,
            "videos_processed": len(set(c["video_id"] for c in chunks)),
            "chunks_created": len(chunks)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
def get_stats():
    from embedder import get_collection
    from ingestor import load_chunks

    collection = get_collection()
    chunks = load_chunks()

    if not chunks:
        return {"total_chunks": 0, "total_videos": 0}

    unique_videos = len(set(c["video_id"] for c in chunks))

    return {
        "total_chunks": collection.count(),
        "total_videos": unique_videos,
        "embedding_model": "text-embedding-3-small",
        "llm_model": "gpt-4o-mini"
    }