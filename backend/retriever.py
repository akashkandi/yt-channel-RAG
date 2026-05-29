import os
from dotenv import load_dotenv
from openai import OpenAI
from embedder import query_collection

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def clean_text(text: str) -> str:
    """Remove repetitive phrases from YouTube auto-captions"""
    words = text.split()
    cleaned = []
    seen_phrases = set()
    i = 0
    while i < len(words):
        phrase = " ".join(words[i:i+6])
        if phrase not in seen_phrases:
            cleaned.append(words[i])
            seen_phrases.add(phrase)
        i += 1
    return " ".join(cleaned)


def ask_question(question: str, n_results: int = 5):
    """Main RAG function — retrieve relevant chunks and generate answer"""

    # Step 1 — retrieve relevant chunks from ChromaDB
    results = query_collection(question, n_results=n_results)

    if not results["documents"][0]:
        return {
            "answer": "I couldn't find relevant information in the knowledge base.",
            "citations": [],
            "retrieval_score": 0,
            "cross_video_synthesis": None,
            "unique_videos_count": 0
        }

    # Step 2 — build context from retrieved chunks
    chunks = results["documents"][0]
    metadatas = results["metadatas"][0]

    context_parts = []
    citations = []

    for i, (chunk, meta) in enumerate(zip(chunks, metadatas)):
        cleaned = clean_text(chunk)
        context_parts.append(
            f"[Source {i+1}] From '{meta['video_title']}' at {int(meta['start_time'])}s:\n{cleaned}"
        )
        citations.append({
            "video_title": meta["video_title"],
            "start_time": meta["start_time"],
            "youtube_link": meta["youtube_link"],
            "source_num": i + 1
        })

    context = "\n\n".join(context_parts)

    # Step 3 — generate main answer
    prompt = f"""You are an AI assistant that answers questions based ONLY on the provided YouTube video transcripts from Andrej Karpathy's channel.

Answer the question using the provided sources. For each key point you make, cite which source it came from using [Source N].
If the sources don't contain enough information, say so clearly.
Be concise but thorough.

SOURCES:
{context}

QUESTION: {question}

ANSWER:"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant that answers questions about machine learning and AI based on Andrej Karpathy's YouTube videos. Always cite your sources."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=800
    )

    answer = response.choices[0].message.content

    # Step 4 — cross-video synthesis if multiple videos involved
    unique_videos = list(set(c["video_title"] for c in citations))
    cross_video_synthesis = None

    if len(unique_videos) >= 2:
        synthesis_prompt = f"""The following sources from DIFFERENT YouTube videos all relate to the question: "{question}"

{context}

In 2-3 sentences, explain:
1. How these different videos approach or explain this topic differently
2. What unique angle or depth each video adds

Be specific about which video covers which aspect. Keep it concise."""

        synthesis_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert at synthesizing information across multiple sources."},
                {"role": "user", "content": synthesis_prompt}
            ],
            temperature=0.3,
            max_tokens=300
        )
        cross_video_synthesis = synthesis_response.choices[0].message.content

    # Step 5 — score retrieval quality
    score_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an evaluator. Respond with only a number between 1-10."},
            {"role": "user", "content": f"On a scale of 1-10, how relevant are these retrieved chunks to the question?\n\nQuestion: {question}\n\nChunks: {context[:500]}\n\nScore (1-10 only):"}
        ],
        temperature=0,
        max_tokens=5
    )

    try:
        retrieval_score = int(score_response.choices[0].message.content.strip())
    except Exception:
        retrieval_score = 5

    return {
        "answer": answer,
        "citations": citations,
        "retrieval_score": retrieval_score,
        "cross_video_synthesis": cross_video_synthesis,
        "unique_videos_count": len(unique_videos)
    }


if __name__ == "__main__":
    question = "How does backpropagation relate to building GPT?"
    print(f"Q: {question}\n")
    result = ask_question(question)
    print(f"ANSWER:\n{result['answer']}\n")
    if result["cross_video_synthesis"]:
        print(f"CROSS-VIDEO SYNTHESIS:\n{result['cross_video_synthesis']}\n")
    print(f"RETRIEVAL SCORE: {result['retrieval_score']}/10")
    print(f"VIDEOS REFERENCED: {result['unique_videos_count']}")