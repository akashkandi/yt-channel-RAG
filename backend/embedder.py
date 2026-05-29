import os
import chromadb
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize ChromaDB — saves to disk so you don't re-embed every time
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(
    name="youtube_knowledge_base",
    metadata={"hnsw:space": "cosine"}
)


def get_embedding(text: str):
    """Convert text to embedding vector using OpenAI"""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def embed_chunks(chunks: list):
    """Embed all chunks and store in ChromaDB"""
    print(f"\n🔢 Embedding {len(chunks)} chunks into ChromaDB...")

    batch_size = 50
    total_batches = (len(chunks) // batch_size) + 1

    for batch_num in range(0, len(chunks), batch_size):
        batch = chunks[batch_num:batch_num + batch_size]
        current_batch = (batch_num // batch_size) + 1
        print(f"  Processing batch {current_batch}/{total_batches}...")

        texts = [chunk["text"] for chunk in batch]
        ids = [f"{chunk['video_id']}_{batch_num + i}" for i, chunk in enumerate(batch)]

        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        embeddings = [item.embedding for item in response.data]

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=[{
                "video_id": chunk["video_id"],
                "video_title": chunk["video_title"],
                "start_time": chunk["start_time"],
                "youtube_link": chunk["youtube_link"]
            } for chunk in batch]
        )

    print(f"✅ Successfully stored {len(chunks)} chunks in ChromaDB")
    return collection


def query_collection(question: str, n_results: int = 5):
    """Find most relevant chunks for a question"""
    question_embedding = get_embedding(question)

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=n_results
    )

    return results


def get_collection():
    """Return existing collection"""
    return collection


if __name__ == "__main__":
    from ingestor import load_chunks, ingest_channel, save_chunks

    chunks = load_chunks()

    if not chunks:
        print("No cache found — fetching from YouTube...")
        CHANNEL_ID = "UCXUPKJO5MZQN11PqgIvyuvQ"
        chunks = ingest_channel(CHANNEL_ID)
        if chunks:
            save_chunks(chunks)

    if not chunks:
        print("❌ No chunks available — run ingestor.py first")
        exit()

    existing = collection.count()
    if existing > 0:
        print(f"✅ ChromaDB already has {existing} chunks — skipping re-embedding")
    else:
        embed_chunks(chunks)

    print("\n🔍 Testing query: 'what is backpropagation?'")
    results = query_collection("what is backpropagation?", n_results=3)

    print("\n--- Top 3 results ---")
    for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
        print(f"\n[{i+1}] Video: {meta['video_title']}")
        print(f"    Timestamp: {meta['start_time']}s")
        print(f"    Link: {meta['youtube_link']}")
        print(f"    Text: {doc[:150]}...")