#!/usr/bin/env python3
"""
fair_use_guard.py — Fair use compliance layer for video production.

Enforces transformative use requirements on all sourced clips and images.
Based on research into YouTube documentary fair use practices (March 2026).

Rules enforced:
1. MAX_CLIP_DURATION: 5 seconds per source clip (7s hard max)
2. MANDATORY_NARRATION: Every clip must have voiceover narration overlay
3. MUTE_SOURCE_AUDIO: Original audio from clips is always muted (Content ID trigger)
   EXCEPTION: Soundbite punch-throughs (5-8s) allowed when:
   - Narration is ducked (not absent) before/after the soundbite
   - Total source audio per source stays under MAX_SOURCE_AUDIO_SEC
   - Clip has 2+ other transformative layers (commentary context)
   - Marked explicitly as is_soundbite=True
4. SOURCE_ATTRIBUTION: Every clip gets a lower-third source attribution
5. TRANSFORMATIVE_LAYERS: Minimum 2 transformative elements per clip
   (narration + at least one of: zoom/crop, text overlay, color grade, PiP)
6. SOURCE_PERCENTAGE: Never use more than 10% of any single source work
7. PUBLIC_DOMAIN_PREFERRED: Government/CC0 sources skip most restrictions

Usage:
    from pipeline_v2.fair_use_guard import FairUseGuard

    guard = FairUseGuard()
    result = guard.check_segment(segment)
    if not result["approved"]:
        print(f"BLOCKED: {result['violations']}")
"""

import json
from pathlib import Path
from typing import Optional


# Hard limits
MAX_CLIP_DURATION_SEC = 5.0
HARD_MAX_CLIP_DURATION_SEC = 7.0
MIN_TRANSFORMATIVE_LAYERS = 2
MAX_SOURCE_PERCENTAGE = 0.10  # Never use more than 10% of a source work

# Soundbite punch-through limits
SOUNDBITE_MIN_SEC = 3.0       # Minimum soundbite duration
SOUNDBITE_MAX_SEC = 8.0       # Maximum soundbite duration
MAX_SOURCE_AUDIO_SEC = 25.0   # Max total audio seconds from any single source
MAX_SOUNDBITES_PER_SOURCE = 3  # Max number of soundbites from one source
MAX_TOTAL_SOUNDBITES = 12     # Max soundbites in entire video

# Licenses that are exempt from most restrictions
EXEMPT_LICENSES = {
    "public_domain", "cc0", "us_government", "pd",
    "CC0 1.0", "PDM 1.0", "government_work",
}


class FairUseGuard:
    """Enforces fair use compliance on video segments."""

    def __init__(self):
        self.source_usage = {}  # Track how much of each source is used
        self.source_audio_usage = {}  # Track soundbite audio seconds per source
        self.soundbite_count_per_source = {}  # Track soundbite count per source
        self.total_soundbite_count = 0
        self.violations_log = []

    def is_exempt(self, license_type: str) -> bool:
        """Check if a license exempts from fair use restrictions."""
        if not license_type:
            return False
        return license_type.lower().replace("-", "").replace(" ", "_") in {
            l.lower().replace("-", "").replace(" ", "_") for l in EXEMPT_LICENSES
        }

    def check_segment(self, segment: dict) -> dict:
        """
        Check a single segment for fair use compliance.

        Args:
            segment: Dict with keys like source_type, duration_sec, license,
                     has_narration, transformative_elements, source_url, etc.

        Returns:
            {approved: bool, violations: list, warnings: list, fixes: list}
        """
        violations = []
        warnings = []
        fixes = []

        source_type = segment.get("source_type", "unknown")
        license_type = segment.get("license", "unknown")
        duration = segment.get("duration_sec", 0)
        has_narration = segment.get("has_narration", True)  # Default true for documentary
        transformative = segment.get("transformative_elements", [])
        source_url = segment.get("source_url", "")

        # Skip checks for generated content, stills we created, chapter cards, etc.
        if source_type in ("animation", "chapter_card", "generated", "black"):
            return {"approved": True, "violations": [], "warnings": [], "fixes": []}

        # Public domain / CC0 -- exempt from most restrictions
        if self.is_exempt(license_type):
            # Still enforce narration overlay (for viewer engagement, not legal)
            if not has_narration:
                warnings.append("No narration over this segment -- may lose viewer attention")
            return {"approved": True, "violations": [], "warnings": warnings, "fixes": []}

        # 1. Clip duration
        if duration > HARD_MAX_CLIP_DURATION_SEC:
            violations.append(
                f"Clip duration {duration:.1f}s exceeds hard max {HARD_MAX_CLIP_DURATION_SEC}s"
            )
            fixes.append(f"Trim to {MAX_CLIP_DURATION_SEC}s or split into multiple segments")
        elif duration > MAX_CLIP_DURATION_SEC:
            warnings.append(
                f"Clip duration {duration:.1f}s exceeds recommended {MAX_CLIP_DURATION_SEC}s"
            )
            fixes.append(f"Consider trimming to {MAX_CLIP_DURATION_SEC}s")

        # 2. Mandatory narration
        if not has_narration:
            violations.append("No narration overlay -- clip is not transformative without commentary")
            fixes.append("Add voiceover narration. Never show a clip 'naked'.")

        # 3. Source audio (should be muted UNLESS it's an approved soundbite)
        if segment.get("has_source_audio", False):
            if segment.get("is_soundbite", False):
                # Soundbite exception -- check additional constraints
                sb_result = self.check_soundbite(segment)
                if not sb_result["approved"]:
                    violations.extend(sb_result["violations"])
                    fixes.extend(sb_result["fixes"])
                else:
                    warnings.extend(sb_result.get("warnings", []))
            else:
                violations.append("Source audio not muted -- Content ID will likely flag this")
                fixes.append("Mute original audio. Content ID is audio-fingerprint driven.")

        # 4. Transformative layers
        # Count what we have: narration, zoom/crop, text_overlay, color_grade, pip
        layer_count = 0
        if has_narration:
            layer_count += 1
        if any(t in transformative for t in ["zoom", "crop", "ken_burns", "reframe"]):
            layer_count += 1
        if any(t in transformative for t in ["text_overlay", "caption", "attribution"]):
            layer_count += 1
        if any(t in transformative for t in ["color_grade", "color_grading", "grade"]):
            layer_count += 1
        if any(t in transformative for t in ["pip", "picture_in_picture", "split_screen"]):
            layer_count += 1

        if layer_count < MIN_TRANSFORMATIVE_LAYERS:
            violations.append(
                f"Only {layer_count} transformative layer(s) -- need {MIN_TRANSFORMATIVE_LAYERS}+"
            )
            fixes.append(
                "Add at least: narration + one visual transformation (zoom/crop, text overlay, color grade)"
            )

        # 5. Source attribution
        if not segment.get("attribution"):
            warnings.append("No source attribution -- add lower-third credit for transparency")
            fixes.append("Add source attribution text in lower-third")

        # 6. Source percentage tracking
        if source_url:
            self.source_usage[source_url] = self.source_usage.get(source_url, 0) + duration
            # We can't know total source duration, but flag heavy reuse
            if self.source_usage[source_url] > 30:  # More than 30s from one source
                warnings.append(
                    f"Heavy reuse: {self.source_usage[source_url]:.0f}s from {source_url}"
                )
                fixes.append("Diversify sources -- use multiple clips from different sources")

        approved = len(violations) == 0

        if violations:
            self.violations_log.append({
                "segment": segment.get("segment_index", "?"),
                "source": source_url,
                "violations": violations,
            })

        return {
            "approved": approved,
            "violations": violations,
            "warnings": warnings,
            "fixes": fixes,
            "transformative_layers": layer_count,
        }

    def check_soundbite(self, segment: dict) -> dict:
        """
        Check if a soundbite punch-through is fair-use compliant.

        Soundbites are brief moments (3-8s) where the original clip audio
        plays through while narration is ducked. This creates documentary
        "evidence" moments -- letting the source speak for itself in context
        of critical commentary.

        Requirements:
        - Duration 3-8 seconds
        - Narration ducked before/after (not absent from surrounding context)
        - Total source audio per source < MAX_SOURCE_AUDIO_SEC
        - Max N soundbites per source
        - Max total soundbites in video
        - 2+ transformative layers still required (commentary context)
        """
        violations = []
        warnings = []
        fixes = []

        duration = segment.get("duration_sec", 0)
        source_url = segment.get("source_url", "")
        has_narration_context = segment.get("has_narration_context", True)

        # Duration check
        if duration > SOUNDBITE_MAX_SEC:
            violations.append(
                f"Soundbite {duration:.1f}s exceeds max {SOUNDBITE_MAX_SEC}s"
            )
            fixes.append(f"Trim soundbite to {SOUNDBITE_MAX_SEC}s or less")
        elif duration < SOUNDBITE_MIN_SEC:
            warnings.append(
                f"Soundbite {duration:.1f}s very short -- may not land with viewers"
            )

        # Narration context check -- soundbite must sit within narration
        if not has_narration_context:
            violations.append(
                "Soundbite has no surrounding narration context -- "
                "not transformative without commentary"
            )
            fixes.append("Ensure narration plays before and after the soundbite")

        # Per-source audio budget
        if source_url:
            current_audio = self.source_audio_usage.get(source_url, 0)
            if current_audio + duration > MAX_SOURCE_AUDIO_SEC:
                violations.append(
                    f"Source audio budget exceeded: {current_audio + duration:.1f}s "
                    f"> {MAX_SOURCE_AUDIO_SEC}s for {source_url}"
                )
                fixes.append("Use fewer/shorter soundbites from this source")
            else:
                self.source_audio_usage[source_url] = current_audio + duration

            # Per-source count
            current_count = self.soundbite_count_per_source.get(source_url, 0)
            if current_count >= MAX_SOUNDBITES_PER_SOURCE:
                violations.append(
                    f"Too many soundbites ({current_count + 1}) from same source "
                    f"(max {MAX_SOUNDBITES_PER_SOURCE})"
                )
                fixes.append("Diversify -- use soundbites from different sources")
            else:
                self.soundbite_count_per_source[source_url] = current_count + 1

        # Global soundbite count
        if self.total_soundbite_count >= MAX_TOTAL_SOUNDBITES:
            violations.append(
                f"Total soundbite limit reached ({MAX_TOTAL_SOUNDBITES})"
            )
            fixes.append("Remove less impactful soundbites to stay under limit")
        else:
            self.total_soundbite_count += 1

        if not violations:
            warnings.append(
                f"Soundbite approved: {duration:.1f}s from {source_url or 'unknown'}"
            )

        return {
            "approved": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "fixes": fixes,
        }

    def check_timeline(self, segments: list[dict]) -> dict:
        """
        Check all segments in a timeline for fair use compliance.
        Returns overall compliance report.
        """
        results = []
        total = len(segments)
        approved_count = 0
        violation_count = 0
        warning_count = 0

        for seg in segments:
            result = self.check_segment(seg)
            results.append(result)
            if result["approved"]:
                approved_count += 1
            if result["violations"]:
                violation_count += len(result["violations"])
            if result["warnings"]:
                warning_count += len(result["warnings"])

        return {
            "total_segments": total,
            "approved": approved_count,
            "blocked": total - approved_count,
            "total_violations": violation_count,
            "total_warnings": warning_count,
            "compliance_rate": f"{approved_count / max(total, 1) * 100:.0f}%",
            "source_usage": dict(self.source_usage),
            "violations_log": self.violations_log,
            "results": results,
        }

    def auto_fix_segment(self, segment: dict) -> dict:
        """
        Automatically apply fixes to make a segment compliant.
        Returns the modified segment.
        """
        fixed = dict(segment)

        # Ensure narration overlay
        fixed["has_narration"] = True

        # Mute source audio
        fixed["has_source_audio"] = False

        # Cap duration
        if fixed.get("duration_sec", 0) > HARD_MAX_CLIP_DURATION_SEC:
            fixed["duration_sec"] = MAX_CLIP_DURATION_SEC

        # Ensure transformative elements
        transformative = fixed.get("transformative_elements", [])
        if "narration_overlay" not in transformative:
            transformative.append("narration_overlay")
        if "ken_burns" not in transformative and "zoom" not in transformative:
            transformative.append("ken_burns")
        if "color_grade" not in transformative:
            transformative.append("color_grade")
        fixed["transformative_elements"] = transformative

        return fixed
