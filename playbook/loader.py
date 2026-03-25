"""
Playbook Loader — query the YouTube strategy playbook from any pipeline module.

Usage:
    from playbook.loader import Playbook

    pb = Playbook()

    # Get all principles for a pipeline stage
    principles = pb.for_stage("director")

    # Get specific module
    editing = pb.module("editing")

    # Get checklist criteria
    checklist = pb.checklist("editing", "editing_quality")

    # Get anti-patterns to avoid
    anti_patterns = pb.anti_patterns("scripting")

    # Score against a checklist
    scores = {"cut_frequency": 0.8, "b_roll_ratio": 0.9, ...}
    result = pb.score_checklist("editing", "editing_quality", scores)

    # Get all tactics for a module
    tactics = pb.tactics("titles_thumbnails")

    # Get the 26 click tactics
    click_tactics = pb.click_tactics()
"""

import json
import os
from pathlib import Path
from typing import Any, Optional


PLAYBOOK_DIR = Path(__file__).parent


class Playbook:
    """Query interface for the YouTube strategy playbook."""

    def __init__(self, playbook_dir: Optional[str] = None):
        self.dir = Path(playbook_dir) if playbook_dir else PLAYBOOK_DIR
        self._cache: dict[str, dict] = {}
        self._index: Optional[dict] = None

    def _load(self, module_name: str) -> dict:
        """Load and cache a playbook module."""
        if module_name not in self._cache:
            path = self.dir / f"{module_name}.json"
            if not path.exists():
                raise FileNotFoundError(f"Playbook module not found: {path}")
            with open(path) as f:
                self._cache[module_name] = json.load(f)
        return self._cache[module_name]

    @property
    def index(self) -> dict:
        """Load the master index."""
        if self._index is None:
            self._index = self._load("index")
        return self._index

    def module(self, name: str) -> dict:
        """Get a full playbook module by name."""
        return self._load(name)

    def for_stage(self, pipeline_stage: str) -> dict:
        """Get all playbook content relevant to a pipeline stage.

        Returns a merged dict with principles, tactics, checklists,
        and anti_patterns from all modules mapped to this stage.
        """
        mapping = self.index.get("pipeline_mapping", {})
        if pipeline_stage not in mapping:
            return {"error": f"Unknown pipeline stage: {pipeline_stage}",
                    "available": list(mapping.keys())}

        stage_info = mapping[pipeline_stage]
        module_names = stage_info.get("modules", [])

        result = {
            "stage": pipeline_stage,
            "usage": stage_info.get("usage", ""),
            "principles": [],
            "tactics": {},
            "checklists": {},
            "anti_patterns": [],
        }

        for mod_name in module_names:
            mod = self._load(mod_name)
            result["principles"].extend(mod.get("principles", []))
            result["tactics"].update(mod.get("tactics", {}))
            result["checklists"].update(mod.get("checklists", {}))
            result["anti_patterns"].extend(mod.get("anti_patterns", []))

        return result

    def principles(self, module_name: str) -> list[dict]:
        """Get principles from a specific module."""
        return self._load(module_name).get("principles", [])

    def tactics(self, module_name: str) -> dict:
        """Get all tactics from a specific module."""
        return self._load(module_name).get("tactics", {})

    def checklist(self, module_name: str, checklist_name: str) -> dict:
        """Get a specific checklist from a module."""
        checklists = self._load(module_name).get("checklists", {})
        return checklists.get(checklist_name, {})

    def anti_patterns(self, module_name: str) -> list[dict]:
        """Get anti-patterns from a specific module."""
        return self._load(module_name).get("anti_patterns", [])

    def click_tactics(self) -> list[dict]:
        """Get the 26 click tactics from titles_thumbnails module."""
        tactics = self.tactics("titles_thumbnails")
        return tactics.get("twenty_six_click_tactics", [])

    def score_checklist(self, module_name: str, checklist_name: str,
                        scores: dict[str, float]) -> dict:
        """Score against a checklist. Returns weighted score and breakdown.

        Args:
            module_name: Which playbook module contains the checklist
            checklist_name: Name of the checklist within the module
            scores: Dict mapping criterion name to score (0.0-1.0)

        Returns:
            Dict with total_score, breakdown, and missing criteria
        """
        cl = self.checklist(module_name, checklist_name)
        criteria = cl.get("criteria", [])

        if not criteria:
            return {"error": f"Checklist not found: {module_name}/{checklist_name}"}

        breakdown = []
        total_weight = 0
        weighted_sum = 0
        missing = []

        for c in criteria:
            name = c["name"]
            weight = c.get("weight", 1.0 / len(criteria))

            if name in scores:
                score = max(0.0, min(1.0, scores[name]))
                weighted_sum += score * weight
                total_weight += weight
                breakdown.append({
                    "criterion": name,
                    "score": score,
                    "weight": weight,
                    "weighted": round(score * weight, 4),
                    "description": c.get("description", ""),
                })
            else:
                missing.append(name)

        total = round(weighted_sum / total_weight, 4) if total_weight > 0 else 0.0

        return {
            "total_score": total,
            "total_percent": f"{total * 100:.1f}%",
            "breakdown": breakdown,
            "missing_criteria": missing,
            "checklist_description": cl.get("description", ""),
        }

    def all_modules(self) -> list[str]:
        """List all available playbook modules."""
        modules = []
        for f in sorted(self.dir.glob("*.json")):
            name = f.stem
            if name not in ("index", "sources"):
                modules.append(name)
        return modules

    def sources(self) -> dict:
        """Get source attribution data."""
        return self._load("sources")

    def summary(self) -> str:
        """Print a human-readable summary of the playbook."""
        lines = ["YouTube Strategy Playbook", "=" * 40, ""]
        for mod_name in self.all_modules():
            mod = self._load(mod_name)
            desc = mod.get("description", "")
            n_principles = len(mod.get("principles", []))
            n_tactics = len(mod.get("tactics", {}))
            n_checklists = len(mod.get("checklists", {}))
            n_anti = len(mod.get("anti_patterns", []))
            lines.append(f"  {mod_name}")
            lines.append(f"    {desc}")
            lines.append(f"    {n_principles} principles, {n_tactics} tactics, "
                        f"{n_checklists} checklists, {n_anti} anti-patterns")
            lines.append("")

        src = self._load("sources")
        creators = src.get("creators", [])
        lines.append(f"Sources: {len(creators)} creator(s)")
        for c in creators:
            lines.append(f"  - {c['name']}: {c['videos_analyzed']} videos analyzed")

        return "\n".join(lines)


# Quick test
if __name__ == "__main__":
    pb = Playbook()
    print(pb.summary())
    print()

    # Example: score a script
    print("Example checklist scoring:")
    result = pb.score_checklist("scripting", "script_quality", {
        "green_purple_ratio": 0.85,
        "water_tank_pacing": 0.70,
        "but_therefore_flow": 0.60,
        "conversational_tone": 0.90,
        "trim_test": 0.75,
        "energy_variation": 0.80,
        "clarity": 0.95,
    })
    print(f"  Total: {result['total_percent']}")
    for b in result["breakdown"]:
        print(f"  {b['criterion']}: {b['score']:.0%} (weight: {b['weight']:.0%})")
