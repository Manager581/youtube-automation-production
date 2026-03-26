#!/usr/bin/env python3
"""
soundbite_analyzer.py — Finds the best audio punch-through moments from source clips.

Reads SRT transcripts (from whisper) and the narration script, then identifies
5-8 second soundbites where the source clip's audio should punch through the
narration for maximum documentary impact.

Selection criteria:
1. RELEVANCE: Soundbite content must match a specific section of the narration script
2. IMPACT: Prefer shocking stats, damning quotes, emotional testimony, authority figures
3. BREVITY: 5-8 seconds — enough to land, not enough to trigger Content ID
4. DIVERSITY: Spread across different sources, don't over-use any one clip
5. FAIR USE: Respects limits from fair_use_guard.py

Pipeline position:
    [WHISPER TRANSCRIPTS] + [NARRATION SCRIPT] → [SOUNDBITE ANALYZER] → [DIRECTOR]

Usage:
    from pipeline.soundbite_analyzer import SoundbiteAnalyzer

    analyzer = SoundbiteAnalyzer(
        transcripts_dir="path/to/srt/files",
        script_path="path/to/script.md",
    )
    soundbites = analyzer.find_soundbites()
"""

import json
import re
from pathlib import Path
from typing import Optional


# ── Impact scoring keywords ────────────────────────────────────────────────
# Higher-weighted keywords indicate more impactful soundbite candidates

IMPACT_KEYWORDS = {
    # Shocking statistics / numbers
    "billion": 3, "million": 3, "percent": 2, "thousand": 1,
    "ninety": 2, "eighty": 2, "seventy": 2, "sixty": 2,

    # Damning accusations / revelations
    "denied": 4, "rejected": 4, "discriminat": 4, "illegal": 4,
    "violated": 4, "sued": 3, "lawsuit": 3, "settlement": 3,
    "guilty": 4, "convicted": 3, "charged": 3, "indicted": 3,
    "collusion": 4, "cartel": 4, "price fixing": 4,

    # Emotional testimony
    "never heard": 3, "didn't know": 3, "no idea": 3,
    "can't believe": 3, "devastating": 3, "heartbreaking": 3,
    "outrageous": 3, "unconscionable": 3,

    # Authority figures speaking
    "senator": 2, "congressman": 2, "judge": 2, "attorney general": 3,
    "department of justice": 3, "fbi": 2, "ftc": 2, "eeoc": 2,
    "secretary": 2, "director": 2, "commissioner": 2,

    # Key entities in the script
    "realpage": 3, "lexisnexis": 3, "hirevue": 3, "cigna": 3,
    "saferent": 3, "corelogic": 3, "workday": 3, "transunion": 3,
    "thoma bravo": 3, "carlyle": 3, "verisk": 3,

    # Algorithmic / scoring language
    "algorithm": 2, "score": 2, "data": 1, "screening": 2,
    "automated": 2, "artificial intelligence": 3, "machine learning": 2,
    "bias": 3, "biased": 3, "discriminatory": 3,

    # Calls to action / direct address
    "you should know": 3, "what they don't tell you": 4,
    "here's the problem": 3, "think about that": 3,
}

# Patterns that indicate a strong standalone soundbite
SOUNDBITE_PATTERNS = [
    # Direct quotes or testimony
    (r'(?:he|she|they) (?:said|told|testified|admitted|claimed)', 3),
    # Questions (rhetorical or probing)
    (r'\?', 2),
    # Declarative damning statements
    (r'(?:the truth is|the reality is|the fact is|what happened was)', 4),
    # Numbers with context
    (r'\d+[\s,]*(?:billion|million|percent|thousand|hundred)', 3),
    # Named person speaking
    (r'(?:Dr\.|Senator|Representative|Professor|CEO|Director)\s+[A-Z]', 2),
]


def parse_srt(srt_path: Path) -> list[dict]:
    """Parse an SRT file into a list of timed text segments."""
    segments = []
    content = srt_path.read_text(encoding="utf-8", errors="replace")

    # Split by double newline (SRT block separator)
    blocks = re.split(r'\n\n+', content.strip())

    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue

        # Parse timestamp line: "00:01:23,456 --> 00:01:27,890"
        time_match = re.match(
            r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})',
            lines[1]
        )
        if not time_match:
            continue

        h1, m1, s1, ms1, h2, m2, s2, ms2 = time_match.groups()
        start_sec = int(h1) * 3600 + int(m1) * 60 + int(s1) + int(ms1) / 1000
        end_sec = int(h2) * 3600 + int(m2) * 60 + int(s2) + int(ms2) / 1000

        text = ' '.join(lines[2:]).strip()
        if text:
            segments.append({
                "start_sec": start_sec,
                "end_sec": end_sec,
                "duration_sec": end_sec - start_sec,
                "text": text,
            })

    return segments


def _score_impact(text: str) -> float:
    """Score how impactful a piece of text would be as a soundbite."""
    text_lower = text.lower()
    score = 0.0

    # Keyword matching
    for keyword, weight in IMPACT_KEYWORDS.items():
        if keyword in text_lower:
            score += weight

    # Pattern matching
    for pattern, weight in SOUNDBITE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            score += weight

    # Length penalty — too short is unclear, too long is risky
    word_count = len(text.split())
    if word_count < 5:
        score *= 0.3  # Too short to be meaningful
    elif word_count < 10:
        score *= 0.7  # A bit short
    elif word_count > 40:
        score *= 0.6  # Too long — will need trimming

    return score


def _find_relevant_script_section(soundbite_text: str, script_sections: list[dict]) -> Optional[dict]:
    """Find which section of the narration script a soundbite is most relevant to."""
    bite_words = set(soundbite_text.lower().split())

    best_match = None
    best_overlap = 0

    for section in script_sections:
        section_words = set(section["text"].lower().split())
        overlap = len(bite_words & section_words)
        # Weighted by section length (don't bias toward long sections)
        if section_words:
            normalized = overlap / min(len(bite_words), 30)
            if normalized > best_overlap:
                best_overlap = normalized
                best_match = section

    return best_match if best_overlap > 0.15 else None


class SoundbiteAnalyzer:
    """Finds the best audio punch-through moments from source clip transcripts."""

    def __init__(self, transcripts_dir: str, script_path: str,
                 clips_dir: Optional[str] = None):
        self.transcripts_dir = Path(transcripts_dir)
        self.script_path = Path(script_path)
        self.clips_dir = Path(clips_dir) if clips_dir else None
        self._script_sections = None

    def _load_script_sections(self) -> list[dict]:
        """Parse the narration script into sections with approximate timing."""
        if self._script_sections is not None:
            return self._script_sections

        content = self.script_path.read_text(encoding="utf-8")

        # Split by --- (section breaks in the script)
        raw_sections = re.split(r'\n---+\n', content)

        sections = []
        # Approximate timing: ~139 WPM narration rate
        wpm = 139.0
        cumulative_sec = 0.0

        for i, raw in enumerate(raw_sections):
            text = raw.strip()
            if not text or text.startswith('#'):
                # Skip headers-only sections
                lines = [l for l in text.split('\n') if not l.startswith('#') and l.strip()]
                text = ' '.join(lines)
                if not text:
                    continue

            word_count = len(text.split())
            duration_sec = word_count / wpm * 60

            sections.append({
                "index": i,
                "text": text,
                "word_count": word_count,
                "start_sec": cumulative_sec,
                "end_sec": cumulative_sec + duration_sec,
                "duration_sec": duration_sec,
            })
            cumulative_sec += duration_sec

        self._script_sections = sections
        return sections

    def _load_transcripts(self) -> dict[str, list[dict]]:
        """Load all SRT transcripts, keyed by source clip name."""
        transcripts = {}
        for srt_file in sorted(self.transcripts_dir.glob("*.srt")):
            clip_name = srt_file.stem
            segments = parse_srt(srt_file)
            if segments:
                transcripts[clip_name] = segments
        return transcripts

    def _build_candidate_soundbites(
        self, transcript_segments: list[dict], min_sec: float = 3.0, max_sec: float = 8.0
    ) -> list[dict]:
        """
        Build candidate soundbites by merging consecutive transcript segments
        into windows of 3-8 seconds.
        """
        candidates = []

        for i in range(len(transcript_segments)):
            # Start a window from this segment
            merged_text = []
            window_start = transcript_segments[i]["start_sec"]
            window_end = transcript_segments[i]["end_sec"]

            for j in range(i, len(transcript_segments)):
                seg = transcript_segments[j]
                window_end = seg["end_sec"]
                duration = window_end - window_start

                merged_text.append(seg["text"])

                if duration >= min_sec:
                    if duration <= max_sec:
                        candidates.append({
                            "start_sec": window_start,
                            "end_sec": window_end,
                            "duration_sec": round(duration, 2),
                            "text": ' '.join(merged_text),
                            "segment_range": (i, j),
                        })
                    else:
                        break  # Window too long, move to next start

        return candidates

    def find_soundbites(
        self,
        max_per_source: int = 3,
        max_total: int = 12,
        min_impact_score: float = 4.0,
    ) -> list[dict]:
        """
        Find the best soundbites across all source clips.

        Returns a list of soundbite dicts, sorted by placement in the video timeline:
        [
            {
                "source_clip": "60 Minutes...",
                "source_path": "clips/60 Minutes....mp4",
                "start_sec": 45.2,       # In the source clip
                "end_sec": 51.8,
                "duration_sec": 6.6,
                "text": "What the soundbite says",
                "impact_score": 12.5,
                "script_section_index": 2,
                "timeline_position_sec": 180.0,  # Where in the final video
                "narration_duck_start_sec": 179.0,
                "narration_duck_end_sec": 187.0,
            }
        ]
        """
        script_sections = self._load_script_sections()
        transcripts = self._load_transcripts()

        if not transcripts:
            print("WARNING: No transcripts found. Run whisper first.")
            return []

        # Phase 1: Score all candidates from all sources
        all_candidates = []

        for clip_name, segments in transcripts.items():
            candidates = self._build_candidate_soundbites(segments)

            for cand in candidates:
                impact = _score_impact(cand["text"])
                if impact < min_impact_score:
                    continue

                # Find which script section this matches
                match = _find_relevant_script_section(cand["text"], script_sections)
                if not match:
                    continue

                all_candidates.append({
                    "source_clip": clip_name,
                    "source_path": str(
                        self.clips_dir / f"{clip_name}.mp4"
                    ) if self.clips_dir else clip_name,
                    "start_sec": cand["start_sec"],
                    "end_sec": cand["end_sec"],
                    "duration_sec": cand["duration_sec"],
                    "text": cand["text"],
                    "impact_score": round(impact, 1),
                    "script_section_index": match["index"],
                    "timeline_position_sec": round(
                        (match["start_sec"] + match["end_sec"]) / 2, 1
                    ),
                })

        # Phase 2: Select best soundbites with diversity constraints
        all_candidates.sort(key=lambda c: c["impact_score"], reverse=True)

        selected = []
        source_counts = {}
        used_timeline_positions = []

        for cand in all_candidates:
            if len(selected) >= max_total:
                break

            source = cand["source_clip"]
            if source_counts.get(source, 0) >= max_per_source:
                continue

            # Don't place two soundbites too close together (min 45s apart)
            pos = cand["timeline_position_sec"]
            too_close = any(abs(pos - used) < 45 for used in used_timeline_positions)
            if too_close:
                continue

            # Add duck timing (1s before, 1s after soundbite)
            cand["narration_duck_start_sec"] = round(pos - 1.0, 1)
            cand["narration_duck_end_sec"] = round(
                pos + cand["duration_sec"] + 1.0, 1
            )
            cand["is_soundbite"] = True
            cand["has_source_audio"] = True
            cand["has_narration_context"] = True

            selected.append(cand)
            source_counts[source] = source_counts.get(source, 0) + 1
            used_timeline_positions.append(pos)

        # Sort by timeline position for sequential placement
        selected.sort(key=lambda s: s["timeline_position_sec"])

        return selected

    def generate_report(self, soundbites: list[dict]) -> str:
        """Generate a human-readable report of selected soundbites."""
        if not soundbites:
            return "No soundbites selected."

        lines = [
            "# Soundbite Punch-Through Plan",
            f"Total soundbites: {len(soundbites)}",
            f"Sources used: {len(set(s['source_clip'] for s in soundbites))}",
            "",
        ]

        for i, sb in enumerate(soundbites, 1):
            lines.extend([
                f"## Soundbite {i}",
                f"- **Source:** {sb['source_clip']}",
                f"- **Clip time:** {sb['start_sec']:.1f}s - {sb['end_sec']:.1f}s "
                f"({sb['duration_sec']:.1f}s)",
                f"- **Text:** \"{sb['text'][:120]}...\"" if len(sb['text']) > 120
                else f"- **Text:** \"{sb['text']}\"",
                f"- **Impact score:** {sb['impact_score']}",
                f"- **Timeline position:** {sb['timeline_position_sec']:.0f}s "
                f"({sb['timeline_position_sec'] / 60:.1f} min)",
                f"- **Duck narration:** {sb['narration_duck_start_sec']:.1f}s - "
                f"{sb['narration_duck_end_sec']:.1f}s",
                "",
            ])

        # Fair use summary
        source_totals = {}
        for sb in soundbites:
            src = sb["source_clip"]
            source_totals[src] = source_totals.get(src, 0) + sb["duration_sec"]

        lines.extend([
            "## Fair Use Summary",
            "| Source | Total Audio (s) | Count |",
            "|--------|----------------|-------|",
        ])
        for src, total in sorted(source_totals.items()):
            count = sum(1 for s in soundbites if s["source_clip"] == src)
            lines.append(f"| {src[:40]} | {total:.1f} | {count} |")

        return '\n'.join(lines)


def main():
    """CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(description="Find best soundbites from source clips")
    parser.add_argument("--transcripts", required=True, help="Directory of SRT files")
    parser.add_argument("--script", required=True, help="Narration script path")
    parser.add_argument("--clips", help="Directory of source clip MP4s")
    parser.add_argument("--max-total", type=int, default=12, help="Max soundbites")
    parser.add_argument("--max-per-source", type=int, default=3, help="Max per source")
    parser.add_argument("--out", help="Output JSON path")
    parser.add_argument("--report", action="store_true", help="Print report")
    args = parser.parse_args()

    analyzer = SoundbiteAnalyzer(
        transcripts_dir=args.transcripts,
        script_path=args.script,
        clips_dir=args.clips,
    )

    soundbites = analyzer.find_soundbites(
        max_total=args.max_total,
        max_per_source=args.max_per_source,
    )

    if args.report or not args.out:
        print(analyzer.generate_report(soundbites))

    if args.out:
        out_path = Path(args.out)
        out_path.write_text(json.dumps(soundbites, indent=2))
        print(f"\nSaved {len(soundbites)} soundbites to {out_path}")


if __name__ == "__main__":
    main()
