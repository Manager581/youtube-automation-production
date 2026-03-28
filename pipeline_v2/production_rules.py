#!/usr/bin/env python3
"""
production_rules.py — Content-to-production mapping using LearnByLeo rules.

Maps narrative functions to production decisions: cut frequency, motion type,
SFX placement, chapter transitions, and visual composition.

All rules derived from playbook/editing.json — NO legacy benchmarks.

Usage:
    from pipeline_v2.production_rules import ProductionRules
    rules = ProductionRules()
    spec = rules.get_segment_spec("tension_build", "The evidence was mounting...")
"""

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class ProductionRules:
    """Content-to-production mapping engine based on LearnByLeo playbook."""

    def __init__(self):
        self.playbook = self._load_playbook()
        self.cut_benchmarks = self.playbook["tactics"]["visual_variety"]
        self.sound_design = self.playbook["tactics"]["sound_design"]
        self.chapter_transitions = self.playbook["tactics"]["chapter_transitions"]
        self.editing_rhythm = self.playbook["tactics"]["editing_rhythm"]
        self.narrative_mapping = self.playbook["tactics"].get("narrative_visual_mapping", {})

    def _load_playbook(self) -> dict:
        path = os.path.join(PROJECT_ROOT, "playbook/editing.json")
        with open(path) as f:
            return json.load(f)

    # ── Narrative Classification ────────────────────────────────────────

    NARRATIVE_FUNCTIONS = {
        "hook_opening": {
            "description": "First 30 seconds — grab attention immediately",
            "cut_interval_sec": (3, 5),
            "motion": "slow_zoom_in",
            "sfx_density": "low",
            "hold_multiplier": 1.0,
        },
        "context_background": {
            "description": "Setting the scene, providing background",
            "cut_interval_sec": (5, 7),
            "motion": "slow_zoom_in",
            "sfx_density": "minimal",
            "hold_multiplier": 1.0,
        },
        "character_intro": {
            "description": "Introducing a person or entity",
            "cut_interval_sec": (4, 6),
            "motion": "zoom_to_face",
            "sfx_density": "low",
            "hold_multiplier": 1.2,
        },
        "tension_build": {
            "description": "Building suspense or anticipation",
            "cut_interval_sec": (4, 6),
            "motion": "faster_zoom_in",
            "sfx_density": "medium",
            "hold_multiplier": 1.0,
        },
        "reveal": {
            "description": "Revealing a key fact or plot point",
            "cut_interval_sec": (2, 4),
            "motion": "extreme_zoom",
            "sfx_density": "high",
            "hold_multiplier": 1.8,
        },
        "stakes_moment": {
            "description": "High stakes — consequences become clear",
            "cut_interval_sec": (3, 5),
            "motion": "zoom_in",
            "sfx_density": "medium",
            "hold_multiplier": 1.4,
        },
        "climax": {
            "description": "Peak emotional or narrative moment",
            "cut_interval_sec": (2, 4),
            "motion": "extreme_zoom",
            "sfx_density": "high",
            "hold_multiplier": 1.8,
        },
        "aftermath": {
            "description": "Consequences and resolution",
            "cut_interval_sec": (5, 7),
            "motion": "slow_zoom_out",
            "sfx_density": "low",
            "hold_multiplier": 1.0,
        },
        "chapter_transition": {
            "description": "Transition between major sections",
            "cut_interval_sec": (3, 5),
            "motion": "static",
            "sfx_density": "none",
            "hold_multiplier": 1.5,
        },
    }

    # ── SFX Types ───────────────────────────────────────────────────────

    SFX_TYPES = {
        "whoosh": {
            "use": "Movement, transitions, visual elements entering/exiting",
            "files": ["whoosh_01.wav", "whoosh_02.wav", "whoosh_03.wav"],
        },
        "highlight": {
            "use": "Emphasis on key words or visuals",
            "files": ["shimmer_01.wav", "shimmer_02.wav"],
        },
        "impact": {
            "use": "Release tension, emphasize major moments",
            "files": ["impact_01.wav", "impact_02.wav"],
        },
        "riser": {
            "use": "Build tension ONLY before genuinely important moments",
            "files": ["tension_01.wav"],
        },
        "hit": {
            "use": "Punctuate major reveals. Pair with risers.",
            "files": ["impact_01.wav", "impact_02.wav"],
        },
        "drone": {
            "use": "Mystery and suspense background layer",
            "files": ["rumble_01.wav", "rumble_02.wav"],
        },
    }

    # ── Chapter Transition Sequence ─────────────────────────────────────

    def get_chapter_transition_spec(self) -> dict:
        """
        Return the 5-step chapter transition sequence from the playbook.

        Steps:
          1. Concluding punch (2-4s) — last sentence is punchy, emotionally loaded
          2. Dramatic silence (2-5s) — narration stops, music continues/swells
          3. Music bridge (5-40s) — music fills gap, signals new chapter
          4. Chapter card (2-4s) — white serif typewriter text on dark background
          5. New hook — fresh compelling line/image resets attention
        """
        return self.chapter_transitions

    # ── Segment Spec ────────────────────────────────────────────────────

    def get_segment_spec(self, narrative_function: str, text: str = "") -> dict:
        """
        Get production spec for a segment based on its narrative function.

        Args:
            narrative_function: One of NARRATIVE_FUNCTIONS keys
            text: Narration text (for keyword-based SFX matching)

        Returns:
            Dict with cut_interval, motion, sfx, hold_multiplier, etc.
        """
        func = self.NARRATIVE_FUNCTIONS.get(
            narrative_function,
            self.NARRATIVE_FUNCTIONS["context_background"]
        )

        spec = {
            "narrative_function": narrative_function,
            "cut_interval_sec": func["cut_interval_sec"],
            "motion": func["motion"],
            "sfx_density": func["sfx_density"],
            "hold_multiplier": func["hold_multiplier"],
            "sfx_suggestion": self._suggest_sfx(narrative_function, text),
            "transition": self._suggest_transition(narrative_function),
        }

        return spec

    def _suggest_sfx(self, narrative_function: str, text: str) -> dict:
        """Suggest SFX based on narrative function and text content."""
        text_lower = text.lower()

        # Content-matched SFX via keywords
        if any(w in text_lower for w in ["crash", "smash", "break", "shatter"]):
            return {"type": "impact", "trigger": "destruction keyword"}
        if any(w in text_lower for w in ["explosion", "bomb", "blast", "detonate"]):
            return {"type": "impact", "trigger": "explosion keyword"}
        if any(w in text_lower for w in ["secret", "hidden", "classified", "confidential"]):
            return {"type": "drone", "trigger": "secrecy keyword"}
        if any(w in text_lower for w in ["revealed", "discovered", "uncovered", "exposed"]):
            return {"type": "hit", "trigger": "revelation keyword"}
        if any(w in text_lower for w in ["suddenly", "without warning", "out of nowhere"]):
            return {"type": "impact", "trigger": "surprise keyword"}

        # Narrative-function-based defaults
        sfx_map = {
            "hook_opening": {"type": "drone", "trigger": "establish mood"},
            "tension_build": {"type": "riser", "trigger": "building tension"},
            "reveal": {"type": "hit", "trigger": "narrative reveal"},
            "climax": {"type": "impact", "trigger": "climax moment"},
            "chapter_transition": {"type": "whoosh", "trigger": "transition"},
            "character_intro": {"type": "highlight", "trigger": "character entrance"},
        }

        return sfx_map.get(narrative_function, {"type": "none", "trigger": ""})

    def _suggest_transition(self, narrative_function: str) -> str:
        """Suggest transition type based on narrative function."""
        transition_map = {
            "hook_opening": "fade_from_black",
            "chapter_transition": "fade_to_black",
            "aftermath": "dissolve",
            "reveal": "hard_cut",
            "climax": "hard_cut",
        }
        return transition_map.get(narrative_function, "hard_cut")

    # ── Text Overlay Rules ──────────────────────────────────────────────

    TEXT_OVERLAY_SIZES = {
        "date": 72,
        "name": 64,
        "entity": 56,
        "location": 52,
        "quote": 44,
    }

    def get_text_size(self, style: str) -> int:
        """Get text overlay size for a given style."""
        return self.TEXT_OVERLAY_SIZES.get(style, 56)

    # ── Classify Script Chunk ───────────────────────────────────────────

    def classify_chunk(self, text: str, position_ratio: float = 0.5) -> str:
        """
        Classify a script chunk into a narrative function based on keywords
        and position in the video.

        Args:
            text: Script text chunk
            position_ratio: Position in video (0.0 = start, 1.0 = end)

        Returns:
            Narrative function string
        """
        text_lower = text.lower()

        # Position-based heuristics
        if position_ratio < 0.03:
            return "hook_opening"
        if position_ratio > 0.95:
            return "aftermath"

        # Keyword-based classification
        if any(w in text_lower for w in ["chapter", "part ", "act "]):
            return "chapter_transition"
        if any(w in text_lower for w in ["revealed", "truth", "discovered", "turns out",
                                          "the answer", "it was"]):
            return "reveal"
        if any(w in text_lower for w in ["but then", "suddenly", "everything changed",
                                          "that's when", "the moment"]):
            return "climax"
        if any(w in text_lower for w in ["this meant", "stakes", "if they failed",
                                          "consequences", "at risk"]):
            return "stakes_moment"
        if any(w in text_lower for w in ["growing", "mounting", "suspicion", "tension",
                                          "something was wrong"]):
            return "tension_build"
        if any(w in text_lower for w in ["born in", "grew up", "his name", "her name",
                                          "meet ", "known as"]):
            return "character_intro"
        if any(w in text_lower for w in ["after", "in the end", "eventually", "today",
                                          "legacy", "since then"]):
            return "aftermath"

        return "context_background"


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Production rules engine")
    parser.add_argument("--classify", help="Classify a text chunk", type=str)
    parser.add_argument("--spec", help="Get spec for a narrative function", type=str)
    parser.add_argument("--chapter-transition", action="store_true",
                        help="Show chapter transition sequence")
    args = parser.parse_args()

    rules = ProductionRules()

    if args.chapter_transition:
        print(json.dumps(rules.get_chapter_transition_spec(), indent=2))
    elif args.spec:
        spec = rules.get_segment_spec(args.spec, "")
        print(json.dumps(spec, indent=2))
    elif args.classify:
        func = rules.classify_chunk(args.classify)
        spec = rules.get_segment_spec(func, args.classify)
        print(f"Classification: {func}")
        print(json.dumps(spec, indent=2))
    else:
        # Show all narrative functions
        print("Available narrative functions:")
        for name, func in ProductionRules.NARRATIVE_FUNCTIONS.items():
            print(f"  {name}: {func['description']}")
            print(f"    Cut interval: {func['cut_interval_sec']}s, Motion: {func['motion']}")


if __name__ == "__main__":
    main()
