import os
import json
import re
import time
import requests
from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
SUPADATA_API_KEY = os.getenv("SUPADATA_API_KEY")


def get_channel_videos(channel_id: str):
    """Fetch all video IDs and titles from a YouTube channel"""
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    videos = []
    next_page_token = None

    channel_response = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    ).execute()

    uploads_playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    while True:
        playlist_response = youtube.playlistItems().list(
            part="snippet",
            playlistId=uploads_playlist_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        for item in playlist_response["items"]:
            videos.append({
                "video_id": item["snippet"]["resourceId"]["videoId"],
                "title": item["snippet"]["title"],
                "published_at": item["snippet"]["publishedAt"]
            })

        next_page_token = playlist_response.get("nextPageToken")
        if not next_page_token:
            break

    return videos


def get_playlist_videos(playlist_id: str):
    """Fetch all video IDs from a YouTube playlist"""
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    videos = []
    next_page_token = None

    while True:
        response = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        for item in response["items"]:
            videos.append({
                "video_id": item["snippet"]["resourceId"]["videoId"],
                "title": item["snippet"]["title"],
                "published_at": item["snippet"]["publishedAt"]
            })

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return videos


def get_transcript_supadata(video_id: str, video_title: str):
    """Fetch transcript using Supadata API — no proxies, no cookies, no IP bans"""
    try:
        response = requests.get(
            "https://api.supadata.ai/v1/youtube/transcript",
            params={"videoId": video_id, "text": "false"},
            headers={"x-api-key": SUPADATA_API_KEY},
            timeout=30
        )

        if response.status_code == 404:
            print(f"  ⚠️  No transcript available for: {video_title}")
            return []

        if response.status_code == 429:
            print(f"  ⚠️  Supadata rate limit hit, waiting 5s...")
            time.sleep(5)
            return get_transcript_supadata(video_id, video_title)

        if response.status_code != 200:
            print(f"  ⚠️  Supadata error {response.status_code} for: {video_title}")
            return []

        data = response.json()
        content = data.get("content", [])

        if not content:
            print(f"  ⚠️  Empty transcript for: {video_title}")
            return []

        # Chunk into ~300 word chunks with timestamps
        chunks = []
        current_chunk = ""
        current_start = 0
        word_count = 0

        for segment in content:
            text = segment.get("text", "").strip()
            if not text:
                continue

            # Supadata returns offset in milliseconds
            start = segment.get("offset", 0) / 1000

            if word_count == 0:
                current_start = start

            current_chunk += " " + text
            word_count += len(text.split())

            if word_count >= 300:
                chunks.append({
                    "video_id": video_id,
                    "video_title": video_title,
                    "text": current_chunk.strip(),
                    "start_time": current_start,
                    "youtube_link": f"https://www.youtube.com/watch?v={video_id}&t={int(current_start)}s"
                })
                current_chunk = ""
                word_count = 0
                current_start = start

        # Don't forget last chunk
        if current_chunk.strip():
            chunks.append({
                "video_id": video_id,
                "video_title": video_title,
                "text": current_chunk.strip(),
                "start_time": current_start,
                "youtube_link": f"https://www.youtube.com/watch?v={video_id}&t={int(current_start)}s"
            })

        return chunks

    except Exception as e:
        print(f"  ⚠️  Error fetching transcript for {video_title}: {e}")
        return []


def ingest_channel(channel_id: str, max_videos: int = 50):
    """Main function — fetch all videos and their transcripts"""
    print(f"\n🔍 Fetching videos from channel/playlist: {channel_id}")

    # Check if playlist or channel
    if channel_id.startswith("PL") or channel_id.startswith("FL"):
        videos = get_playlist_videos(channel_id)
    else:
        videos = get_channel_videos(channel_id)

    # Cap at max_videos
    if len(videos) > max_videos:
        print(f"⚠️  Found {len(videos)} videos — limiting to {max_videos}")
        videos = videos[:max_videos]

    print(f"✅ Processing {len(videos)} videos\n")

    all_chunks = []

    for i, video in enumerate(videos):
        print(f"📝 Processing ({i+1}/{len(videos)}): {video['title']}")
        chunks = get_transcript_supadata(video["video_id"], video["title"])
        all_chunks.extend(chunks)
        print(f"   → {len(chunks)} chunks extracted")

        # Small delay to respect rate limits
        time.sleep(0.5)

    print(f"\n✅ Total chunks ready for embedding: {len(all_chunks)}")
    return all_chunks


def save_chunks(chunks: list, filename: str = "chunks_cache.json"):
    """Save chunks to file so we don't re-fetch from YouTube"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved {len(chunks)} chunks to {filename}")


def load_chunks(filename: str = "chunks_cache.json"):
    """Load chunks from cache file"""
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        if len(chunks) == 0:
            print("⚠️  Cache is empty — will re-fetch")
            return None
        print(f"✅ Loaded {len(chunks)} chunks from cache")
        return chunks
    return None


if __name__ == "__main__":
    CHANNEL_ID = "UCXUPKJO5MZQN11PqgIvyuvQ"
    chunks = load_chunks()

    if not chunks:
        chunks = ingest_channel(CHANNEL_ID)
        if chunks:
            save_chunks(chunks)

    if chunks:
        print("\n--- Sample chunk ---")
        print(f"Video: {chunks[0]['video_title']}")
        print(f"Timestamp: {chunks[0]['start_time']}s")
        print(f"Link: {chunks[0]['youtube_link']}")
        print(f"Text preview: {chunks[0]['text'][:200]}...")
    else:
        print("\n❌ No chunks extracted")