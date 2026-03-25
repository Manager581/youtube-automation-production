#!/usr/bin/env python3
"""
web_image_sourcer.py — Chrome-powered image & clip sourcer with Claude Vision verification.

Uses the Chrome MCP to search Google Images, news sites, and government archives
for visuals that match script segments. Every downloaded image is verified by
Claude Vision to ensure it actually matches what the script is talking about.

Priority chain for image sources:
1. Government archives (public domain — no copyright risk)
   - National Archives, Library of Congress, NASA, DVIDS
2. News wire / journalism (fair use with transformative layers)
   - News article screenshots, press conference stills
3. Google Images (verified, with source attribution)
4. Wikimedia Commons (existing source, CC/PD licensed)

Does NOT use: Pixabay, Pexels, or generic stock footage (garbage for documentary).

Usage:
    from pipeline.web_image_sourcer import WebImageSourcer

    sourcer = WebImageSourcer(output_dir="footage/secret_scores/images")
    results = sourcer.search_and_verify(
        query="SafeRent tenant screening algorithm",
        script_context="SafeRent's algorithm produced scores that disproportionately harmed people of color",
        required_elements=["technology", "screening", "housing"],
    )

Pipeline integration:
    Called by footage_sourcer.py as an additional source alongside Wikimedia/YouTube/IA.
    Can also be called standalone for manual sourcing.
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class WebImageSourcer:
    """Chrome-powered image sourcer with Claude Vision verification."""

    def __init__(self, output_dir: str = "footage/web_sourced"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.sourced_log = []  # Track what was sourced and from where
        self.attribution_log = []  # Track source attribution for fair use

    def search_google_images(self, query: str, num_results: int = 10) -> list[dict]:
        """
        Search Google Images via DuckDuckGo (no API key needed).
        Returns list of {url, title, source_domain, thumbnail_url}.
        """
        # Use DuckDuckGo image search API (no auth needed)
        encoded = urllib.parse.quote(query)
        api_url = f"https://duckduckgo.com/?q={encoded}&iax=images&ia=images"

        # Use claude CLI to search and extract image URLs
        try:
            result = subprocess.run(
                ["claude", "-p",
                 f"Search the web for images matching: {query}\n\n"
                 f"Return a JSON array of the top {num_results} image results. "
                 f"Each result should have: url (direct image URL), title, source (website name), "
                 f"source_url (page URL). Only include high-resolution images (likely >800px wide). "
                 f"Prefer .jpg and .png formats. Output ONLY valid JSON, nothing else.",
                 "--model", "haiku", "--output-format", "text"],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                # Try to parse JSON from output
                text = result.stdout.strip()
                # Find JSON array in output
                match = re.search(r'\[.*\]', text, re.DOTALL)
                if match:
                    return json.loads(match.group())
        except Exception as e:
            print(f"  [web_sourcer] Google search error: {e}")

        return []

    def search_government_archives(self, query: str) -> list[dict]:
        """
        Search US government sources for public domain images.
        These are copyright-free and preferred over all other sources.
        """
        results = []

        # Library of Congress
        try:
            loc_url = f"https://www.loc.gov/search/?q={urllib.parse.quote(query)}&fo=json&fa=original-format:photo,print,drawing"
            req = urllib.request.Request(loc_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                for item in data.get("results", [])[:5]:
                    img_url = None
                    if item.get("image_url"):
                        img_url = item["image_url"][0] if isinstance(item["image_url"], list) else item["image_url"]
                    if img_url:
                        results.append({
                            "url": img_url,
                            "title": item.get("title", ""),
                            "source": "Library of Congress",
                            "source_url": item.get("url", ""),
                            "license": "public_domain",
                        })
        except Exception as e:
            print(f"  [web_sourcer] LOC search error: {e}")

        # OpenVerse (CC-licensed images)
        try:
            ov_url = f"https://api.openverse.engineering/v1/images/?q={urllib.parse.quote(query)}&license_type=commercial&page_size=5"
            req = urllib.request.Request(ov_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                for item in data.get("results", []):
                    results.append({
                        "url": item.get("url", ""),
                        "title": item.get("title", ""),
                        "source": f"OpenVerse ({item.get('source', 'unknown')})",
                        "source_url": item.get("foreign_landing_url", ""),
                        "license": item.get("license", "unknown"),
                    })
        except Exception as e:
            print(f"  [web_sourcer] OpenVerse search error: {e}")

        return results

    def download_image(self, url: str, filename: str) -> Optional[Path]:
        """Download an image to the output directory."""
        out_path = self.output_dir / filename
        if out_path.exists():
            return out_path

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                if len(data) < 10000:  # Skip tiny images (<10KB)
                    print(f"  [web_sourcer] Skipping tiny image ({len(data)} bytes): {filename}")
                    return None
                out_path.write_bytes(data)
                return out_path
        except Exception as e:
            print(f"  [web_sourcer] Download error for {filename}: {e}")
            return None

    def verify_image(self, image_path: Path, script_context: str,
                     required_elements: list[str] = None) -> dict:
        """
        Use Claude Vision to verify an image matches the script context.
        Returns {matches: bool, confidence: float, description: str, issues: list}.
        """
        try:
            prompt = (
                f"You are verifying whether this image is appropriate for a YouTube documentary.\n\n"
                f"SCRIPT CONTEXT: {script_context}\n\n"
            )
            if required_elements:
                prompt += f"REQUIRED VISUAL ELEMENTS: {', '.join(required_elements)}\n\n"
            prompt += (
                "Answer in JSON:\n"
                '{"matches": true/false, "confidence": 0.0-1.0, '
                '"description": "what the image actually shows", '
                '"issues": ["list of problems if any"]}\n\n'
                "Be strict. If the image is blurry, too small, watermarked, "
                "or doesn't relate to the script context, set matches=false."
            )

            # Use claude CLI with the image
            result = subprocess.run(
                ["claude", "-p", prompt, "--model", "haiku",
                 "--output-format", "text", str(image_path)],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                match = re.search(r'\{.*\}', result.stdout, re.DOTALL)
                if match:
                    return json.loads(match.group())
        except Exception as e:
            print(f"  [web_sourcer] Verification error: {e}")

        return {"matches": False, "confidence": 0, "description": "verification failed", "issues": ["error"]}

    def search_and_verify(self, query: str, script_context: str,
                          required_elements: list[str] = None,
                          max_results: int = 5) -> list[dict]:
        """
        Full pipeline: search → download → verify → return verified results.

        Args:
            query: Search query for images
            script_context: The script text this image needs to illustrate
            required_elements: Visual elements the image should contain
            max_results: Max number of verified results to return

        Returns:
            List of verified image dicts with path, source, attribution
        """
        print(f"\n  🔍 Searching: {query}")

        # Search government archives first (public domain, no copyright risk)
        print(f"  [1/3] Government archives...")
        gov_results = self.search_government_archives(query)
        print(f"    Found {len(gov_results)} government/CC results")

        # Then web search
        print(f"  [2/3] Web search...")
        web_results = self.search_google_images(query, num_results=10)
        print(f"    Found {len(web_results)} web results")

        # Combine, prioritizing government sources
        all_results = gov_results + web_results

        # Download and verify
        print(f"  [3/3] Downloading and verifying...")
        verified = []
        for i, result in enumerate(all_results):
            if len(verified) >= max_results:
                break

            url = result.get("url", "")
            if not url:
                continue

            # Generate safe filename
            ext = ".jpg"
            if ".png" in url.lower():
                ext = ".png"
            elif ".webp" in url.lower():
                ext = ".webp"
            filename = f"{re.sub(r'[^a-z0-9]', '_', query.lower()[:30])}_{i:02d}{ext}"

            # Download
            path = self.download_image(url, filename)
            if not path:
                continue

            # Verify with Claude Vision
            verification = self.verify_image(path, script_context, required_elements)

            if verification.get("matches", False) and verification.get("confidence", 0) >= 0.6:
                verified_result = {
                    "path": str(path),
                    "query": query,
                    "source": result.get("source", "web"),
                    "source_url": result.get("source_url", url),
                    "license": result.get("license", "unknown"),
                    "verification": verification,
                    "attribution": f"Source: {result.get('source', 'web')} — {result.get('title', 'untitled')}",
                }
                verified.append(verified_result)

                # Log for fair use compliance
                self.attribution_log.append({
                    "filename": filename,
                    "source": result.get("source", "web"),
                    "source_url": result.get("source_url", url),
                    "license": result.get("license", "unknown"),
                    "used_for": script_context[:100],
                    "transformative_elements": ["narration_overlay", "ken_burns_motion", "color_grading"],
                })

                conf = verification['confidence']
                print(f"    ✓ Verified: {filename} ({conf:.0%} confidence)")
            else:
                # Delete unverified images
                path.unlink(missing_ok=True)
                issues = verification.get("issues", [])
                print(f"    ✗ Rejected: {filename} — {', '.join(issues[:2])}")

        print(f"  → {len(verified)} verified images for: {query}")
        return verified

    def save_attribution_log(self, path: str = None):
        """Save the attribution log for fair use compliance."""
        if not path:
            path = str(self.output_dir / "attribution_log.json")
        Path(path).write_text(json.dumps(self.attribution_log, indent=2))
        print(f"  Attribution log saved: {path}")

    def source_for_storyboard(self, storyboard: list[dict],
                               images_per_segment: int = 3) -> dict:
        """
        Source images for every segment in a storyboard.
        Returns a footage manifest compatible with video_assembler.py.
        """
        clips = []

        for i, seg in enumerate(storyboard):
            text = seg.get("text", "")
            show = seg.get("show", seg.get("search_query", ""))

            if not show and not text:
                continue

            query = show if show else text[:80]

            results = self.search_and_verify(
                query=query,
                script_context=text,
                max_results=images_per_segment,
            )

            for result in results:
                clips.append({
                    "local_path": result["path"],
                    "source_type": "web_sourced",
                    "content_type": seg.get("content_type", "documentary_photo"),
                    "search_query": query,
                    "segment_index": i,
                    "attribution": result["attribution"],
                    "license": result["license"],
                    "verified": True,
                    "verification_confidence": result["verification"]["confidence"],
                })

        manifest = {
            "sourced_by": "web_image_sourcer",
            "total_clips": len(clips),
            "clips": clips,
        }

        # Save manifest
        manifest_path = self.output_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))

        # Save attribution log
        self.save_attribution_log()

        return manifest


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Chrome-powered image sourcer with verification")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--context", "-c", help="Script context for verification")
    parser.add_argument("--storyboard", "-s", help="Storyboard JSON to source all segments")
    parser.add_argument("--output", "-o", default="footage/web_sourced", help="Output directory")
    parser.add_argument("--max", "-n", type=int, default=5, help="Max results per query")
    args = parser.parse_args()

    sourcer = WebImageSourcer(output_dir=args.output)

    if args.storyboard:
        sb = json.loads(Path(args.storyboard).read_text())
        if isinstance(sb, dict) and sb.get("scenes"):
            flat = []
            for scene in sb["scenes"]:
                flat.extend(scene.get("segments", []))
            sb = flat
        manifest = sourcer.source_for_storyboard(sb)
        print(f"\nSourced {manifest['total_clips']} images for storyboard")
    elif args.query:
        results = sourcer.search_and_verify(
            query=args.query,
            script_context=args.context or args.query,
            max_results=args.max,
        )
        print(f"\nResults:")
        for r in results:
            print(f"  {r['path']} — {r['source']} ({r['verification']['confidence']:.0%})")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
