#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
narration_aligner.py — Word-level forced alignment for narration audio.

Uses OpenAI Whisper to extract exact timestamps for every word/sentence
in the narration WAV. The director uses these timestamps instead of
estimating from word count at ~150 WPM.

Output: JSON with sentence-level and word-level timestamps.

Usage:
    python -m pipeline_v2.narration_aligner \
        --narration audio/breaking_law/narration.wav \
        --script scripts/raw_breaking_law_v45.txt \
        --output audio/breaking_law/narration_alignment.json
"""

import argparse
import json
import os
import sys
import re

# Fix SSL cert issue for tiktoken (Whisper dependency)
try:
    import certifi
    os.environ.setdefault('SSL_CERT_FILE', certifi.where())
    os.environ.setdefault('REQUESTS_CA_BUNDLE', certifi.where())
except ImportError:
    pass


def _patch_whisper_tokenizer():
    """Monkey-patch whisper's tokenizer to handle encoding correctly on Python 3.13."""
    import whisper.tokenizer as wt
    import base64
    import tiktoken
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def patched_get_encoding(name="gpt2", num_languages=99):
        vocab_path = os.path.join(os.path.dirname(wt.__file__), "assets", f"{name}.tiktoken")
        ranks = {
            base64.b64decode(token): int(rank)
            for token, rank in (
                line.split() for line in open(vocab_path, encoding="utf-8") if line.strip()
            )
        }
        n_vocab = len(ranks)
        special_tokens = {}
        specials = [
            "<|endoftext|>",
            "<|startoftranscript|>",
            *[f"<|{lang}|>" for lang in list(wt.LANGUAGES.keys())[:num_languages]],
            "<|translate|>",
            "<|transcribe|>",
            "<|startoflm|>",
            "<|startofprev|>",
            "<|nospeech|>",
            "<|notimestamps|>",
            *[f"<|{i * 0.02:.2f}|>" for i in range(1501)],
        ]
        for token in specials:
            special_tokens[token] = n_vocab
            n_vocab += 1
        return tiktoken.Encoding(
            name=os.path.basename(vocab_path),
            explicit_n_vocab=n_vocab,
            pat_str=r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+""",
            mergeable_ranks=ranks,
            special_tokens=special_tokens,
        )

    wt.get_encoding = patched_get_encoding


def align_narration(narration_path: str, script_path: str = None,
                    model_size: str = "base", output_path: str = None) -> dict:
    """Run Whisper on narration WAV and extract word-level timestamps.

    Args:
        narration_path: Path to narration WAV file.
        script_path: Optional script text file (used to verify alignment quality).
        model_size: Whisper model size (tiny/base/small/medium/large).
        output_path: Where to write the alignment JSON.

    Returns:
        dict with sentences and word-level timestamps.
    """
    import whisper

    print(f"\n{'='*60}")
    print(f"Narration Aligner — Whisper {model_size}")
    print(f"{'='*60}")
    print(f"  Audio: {narration_path}")

    if not os.path.exists(narration_path):
        print(f"  ERROR: File not found: {narration_path}")
        sys.exit(1)

    # Load model
    # Patch whisper tokenizer for Python 3.13 encoding compatibility
    _patch_whisper_tokenizer()

    print(f"  Loading Whisper {model_size} model...")
    model = whisper.load_model(model_size)

    # Transcribe with word-level timestamps
    print(f"  Transcribing with word timestamps...")
    result = model.transcribe(
        narration_path,
        word_timestamps=True,
        language="en",
        verbose=False,
    )

    # Extract segments (sentence-level)
    sentences = []
    words_all = []

    for seg in result.get("segments", []):
        sentence = {
            "id": seg["id"],
            "text": seg["text"].strip(),
            "start": round(seg["start"], 3),
            "end": round(seg["end"], 3),
            "words": [],
        }

        for w in seg.get("words", []):
            word_entry = {
                "word": w["word"].strip(),
                "start": round(w["start"], 3),
                "end": round(w["end"], 3),
            }
            sentence["words"].append(word_entry)
            words_all.append(word_entry)

        sentences.append(sentence)

    # Summary stats
    total_dur = sentences[-1]["end"] if sentences else 0
    total_words = len(words_all)
    avg_wpm = (total_words / total_dur * 60) if total_dur > 0 else 0

    print(f"  Sentences: {len(sentences)}")
    print(f"  Words: {total_words}")
    print(f"  Duration: {total_dur:.1f}s ({total_dur/60:.1f} min)")
    print(f"  Average WPM: {avg_wpm:.0f}")

    # If script provided, verify alignment quality
    script_text = None
    if script_path and os.path.exists(script_path):
        with open(script_path, encoding="utf-8") as f:
            script_text = f.read()

        # Simple check: count matching words
        script_words = set(re.findall(r'\w+', script_text.lower()))
        whisper_words = set(w["word"].lower() for w in words_all)
        overlap = len(script_words & whisper_words)
        coverage = overlap / len(script_words) * 100 if script_words else 0
        print(f"  Script word coverage: {coverage:.0f}% ({overlap}/{len(script_words)} unique words)")

    # Build output
    alignment = {
        "narration_path": os.path.abspath(narration_path),
        "model": model_size,
        "duration_sec": total_dur,
        "total_words": total_words,
        "avg_wpm": round(avg_wpm, 1),
        "sentences": sentences,
    }

    # Write output
    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(alignment, f, indent=2, ensure_ascii=False)
        print(f"  Output: {output_path}")
        print(f"  Size: {os.path.getsize(output_path):,} bytes")

    print(f"\n  Done.")
    return alignment


def match_script_to_alignment(script_segments: list, alignment: dict) -> list:
    """Match script segments (from the enhanced script) to Whisper timestamps.

    Each script segment has text. We find the best matching Whisper sentence(s)
    and assign their timestamps to the segment.

    Args:
        script_segments: List of dicts with at least a 'text' field.
        alignment: Output from align_narration().

    Returns:
        script_segments with added _timeline_start_sec and _timeline_end_sec.
    """
    whisper_sentences = alignment.get("sentences", [])
    if not whisper_sentences:
        return script_segments

    # Build a flat list of (word, timestamp) for matching
    all_words = []
    for sent in whisper_sentences:
        for w in sent.get("words", []):
            all_words.append((w["word"].lower().strip(), w["start"], w["end"]))

    word_idx = 0
    for seg in script_segments:
        seg_text = seg.get("text", "")
        # Remove markup like [BEAT], [PAUSE:1], [VOICE:tense]
        clean_text = re.sub(r'\[.*?\]', '', seg_text).strip()
        seg_words = re.findall(r'\w+', clean_text.lower())

        if not seg_words:
            continue

        # Find the first matching word in the whisper output
        best_start_idx = word_idx
        first_word = seg_words[0]

        # Search forward from current position
        for i in range(word_idx, min(word_idx + 200, len(all_words))):
            if all_words[i][0] == first_word:
                best_start_idx = i
                break

        # Find the last matching word
        last_word = seg_words[-1]
        best_end_idx = min(best_start_idx + len(seg_words) + 10, len(all_words) - 1)
        for i in range(best_start_idx + len(seg_words) - 1,
                       min(best_start_idx + len(seg_words) + 20, len(all_words))):
            if i < len(all_words) and all_words[i][0] == last_word:
                best_end_idx = i
                break

        if best_start_idx < len(all_words) and best_end_idx < len(all_words):
            seg["_timeline_start_sec"] = all_words[best_start_idx][1]
            seg["_timeline_end_sec"] = all_words[best_end_idx][2]
            word_idx = best_end_idx + 1

    return script_segments


def main():
    parser = argparse.ArgumentParser(
        description="Narration Aligner — Whisper word-level timestamps"
    )
    parser.add_argument("--narration", required=True,
                        help="Path to narration WAV file")
    parser.add_argument("--script",
                        help="Path to script text file (for quality check)")
    parser.add_argument("--output", default="narration_alignment.json",
                        help="Output JSON path")
    parser.add_argument("--model", default="base",
                        choices=["tiny", "base", "small", "medium", "large"],
                        help="Whisper model size (default: base)")
    args = parser.parse_args()

    alignment = align_narration(
        narration_path=args.narration,
        script_path=args.script,
        model_size=args.model,
        output_path=args.output,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
