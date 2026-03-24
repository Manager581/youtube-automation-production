#!/usr/bin/env python3
"""
Test Google Veo 2 video generation via Gemini API.
Free tier, no local model loading, runs via cloud API.

Usage:
    venv/bin/python scripts/test_veo2.py
"""

import os
import sys
import time
import pathlib

def main():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not set. Get one free at https://aistudio.google.com/apikey")
        sys.exit(1)

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("ERROR: google-genai not installed. Run: pip install google-genai")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    prompt = (
        "A dark hotel room at 3am, 1950s decor. A shadowy figure silhouetted against "
        "a dimly lit window. Suddenly the window glass shatters outward and the figure "
        "falls through into the night. Noir cinematic lighting, dramatic camera angle "
        "looking from inside the room toward the window. Dark, moody, atmospheric."
    )

    output_path = pathlib.Path("output/veo2_hotel_test.mp4")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("GOOGLE VEO 2 — Video Generation Test")
    print("=" * 60)
    print(f"\nPrompt: {prompt[:80]}...")
    print(f"Output: {output_path}")
    print("\nSubmitting generation request...")

    try:
        operation = client.models.generate_videos(
            model="veo-2.0-generate-001",
            prompt=prompt,
            config=types.GenerateVideosConfig(
                number_of_videos=1,
                duration_seconds=5,
                aspect_ratio="16:9",
            ),
        )
    except Exception as e:
        print(f"\nERROR submitting request: {e}")
        print("\nThis could mean:")
        print("  - Veo 2 isn't available in your region")
        print("  - The API key doesn't have video generation enabled")
        print("  - Free tier quota exceeded")
        sys.exit(1)

    print("Request submitted. Polling for completion...")
    start_time = time.time()

    while not operation.done:
        elapsed = time.time() - start_time
        print(f"  Waiting... ({elapsed:.0f}s elapsed)", end="\r")
        time.sleep(10)
        try:
            operation = client.operations.get(operation)
        except Exception as e:
            print(f"\nERROR polling: {e}")
            sys.exit(1)

    elapsed = time.time() - start_time
    print(f"\nGeneration complete in {elapsed:.0f}s")

    if not operation.result or not operation.result.generated_videos:
        print("ERROR: No videos in result")
        print(f"Operation: {operation}")
        sys.exit(1)

    for i, video in enumerate(operation.result.generated_videos):
        out = output_path if i == 0 else output_path.with_stem(f"{output_path.stem}_{i}")
        out.write_bytes(video.video.video_bytes)
        size_mb = out.stat().st_size / (1024 * 1024)
        print(f"\nSaved: {out} ({size_mb:.1f} MB)")

    print(f"\nDONE — open {output_path} to review")
    print("=" * 60)


if __name__ == "__main__":
    main()
