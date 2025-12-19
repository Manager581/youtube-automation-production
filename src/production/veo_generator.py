"""
Veo 3 Shot List Generator
Parses scripts and generates optimized Veo prompts for 8-second clips
"""

import re
import json
import yaml
from datetime import datetime
from pathlib import Path


class VeoShotListGenerator:
    """Converts scripts into Veo 3 shot lists"""

    VEO_STYLE_TEMPLATES = {
        "space_documentary": "cinematic space documentary style, 4K quality, NASA-inspired",
        "dramatic": "dramatic cinematic space footage, epic scale, volumetric lighting",
        "scientific": "scientific visualization, clean aesthetic, detailed",
        "mysterious": "mysterious cosmic phenomena, moody atmosphere, deep space",
        "epic": "epic space scene, grand scale, awe-inspiring",
    }

    VEO_PROMPT_BEST_PRACTICES = """
Best Veo 3 Prompts (8-second clips):

✅ GOOD PROMPTS:
- "Cinematic shot of a massive black hole warping spacetime, accretion disk glowing blue and orange, 4K NASA style"
- "Slow push into a colorful nebula with stars forming, volumetric god rays, deep space photography style"
- "Camera orbiting a ringed gas giant planet, dramatic lighting, photorealistic, 4K space documentary"
- "Time-lapse of Earth from ISS showing city lights at night, smooth motion, realistic"
- "Asteroid field slowly drifting through space, dramatic backlighting from distant sun, cinematic"

❌ AVOID:
- Too much action (Veo struggles with fast motion in 8s)
- Complex movements (keep camera moves simple)
- Text or UI elements (generate those in editing)
- Multiple subjects changing rapidly
- Abstract concepts without visual references

VELO STRENGTHS:
- Slow, cinematic camera movements
- Atmospheric effects (nebulas, gas clouds, lighting)
- Scale and grandeur (planets, stars, cosmic structures)
- Realistic space textures and materials
- Smooth orbital/dolly/push camera moves

TIPS FOR 8-SECOND CLIPS:
- Single clear subject per clip
- One camera movement (push, orbit, or static)
- Descriptive but concise (20-30 words)
- Include style keywords: "cinematic", "4K", "photorealistic"
- Specify lighting: "dramatic backlighting", "volumetric", "moody"
"""

    def __init__(self, config_path="config/config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.max_clip_length = self.config['veo']['max_clip_length']
        self.output_dir = Path("prompts/veo_shots")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def parse_script_for_visuals(self, script_file):
        """Extract visual cues from script - supports both tagged and narrative scripts"""

        with open(script_file, 'r') as f:
            script_content = f.read()

        # First, try to find explicit [SHOW: ...] cues
        show_cues = re.findall(r'\[SHOW:(.*?)\]', script_content, re.IGNORECASE)

        if show_cues:
            # Script has explicit visual tags
            timestamps = re.findall(r'\[(\d+:\d+)\]', script_content)
            segments = script_content.split('\n\n')

            visual_cues = []
            for i, cue in enumerate(show_cues):
                visual_cues.append({
                    "index": i,
                    "timestamp": timestamps[i] if i < len(timestamps) else f"~{i*10}s",
                    "description": cue.strip(),
                    "context": segments[min(i, len(segments)-1)][:200]
                })
            return visual_cues

        # No explicit tags - parse narrative script intelligently
        print("📖 No [SHOW:] tags found. Parsing narrative script...")
        return self._parse_narrative_script(script_content)

    def _parse_narrative_script(self, script_content):
        """Intelligently parse narrative scripts for visual concepts"""

        # Space documentary visual keywords and their Veo prompts
        visual_keywords = {
            # Stars and stellar objects
            'betelgeuse': "Cinematic close-up of Betelgeuse, massive red supergiant star, glowing orange-red surface with dark spots, slow camera push, 4K space documentary",
            'red supergiant': "Wide shot of massive red supergiant star, enormous scale, glowing red atmosphere, slow rotation, photorealistic space rendering",
            'star': "Dramatic shot of massive star with visible corona, solar flares, surface detail, cinematic lighting",
            'orion': "Wide shot of Orion constellation against starfield, Betelgeuse glowing red at shoulder position, constellat lines visible, night sky astronomy",
            'sun': "Cinematic shot of our Sun from space, surface detail visible, solar prominences, dramatic lighting",

            # Cosmic events
            'supernova': "Spectacular supernova explosion, expanding shockwave, bright core, debris cloud forming, epic scale, volumetric rendering",
            'explosion': "Massive stellar explosion, shockwave expanding through space, bright flash, debris field, dramatic cinematography",
            'surface mass ejection': "Enormous chunk of stellar material being ejected from star surface, glowing plasma, dramatic event, slow motion",
            'dust cloud': "Massive interstellar dust cloud drifting through space, backlit by stars, volumetric rendering, mysterious atmosphere",
            'dimming': "Time-lapse of Betelgeuse dimming, star fading from bright to dim, comparison over time, documentary style",

            # Companion star
            'companion star': "Distant view showing two stars in binary orbit, larger red giant with small blue companion nearby, orbital motion",
            'betelbuddy': "Close-up of small blue-white companion star near massive red supergiant, size comparison, dramatic scale difference",
            'binary system': "Wide shot of binary star system, two stars orbiting common center, orbital paths visible, cinematic",

            # Planets and solar system
            'earth': "Beautiful shot of Earth from space, blue marble, city lights visible on night side, realistic",
            'mars': "Orbital shot of Mars, red planet surface visible, polar ice caps, photorealistic planetary rendering",
            'jupiter': "Cinematic flyby of Jupiter, Great Red Spot visible, atmospheric bands, massive scale, 4K space documentary",
            'solar system': "Wide shot of entire solar system, Sun at center, planets in orbital paths, scale visualization",

            # Cosmic structures
            'nebula': "Colorful emission nebula with star formation, volumetric gas clouds, dramatic lighting, deep space photography style",
            'galaxy': "Spectacular spiral galaxy with billions of stars, galactic arms visible, slow rotation, epic cosmic scale",
            'milky way': "Edge-on view of Milky Way galaxy, spiral structure visible, billions of stars, cosmic perspective",
            'black hole': "Dramatic visualization of black hole with accretion disk, warped spacetime visible, glowing matter spiraling inward",

            # Space phenomena
            'neutrino detector': "Underground neutrino detector facility, massive water tank with photomultiplier tubes glowing, scientific facility interior",
            'telescope': "Ground-based observatory telescope at night, dome open, telescope tracking stars, time-lapse of sky rotation",
            'james webb': "James Webb Space Telescope in space, golden mirror panels visible, Earth in background, photorealistic spacecraft",
            'hubble': "Hubble Space Telescope orbiting Earth, solar panels extended, iconic spacecraft, documentary footage style",

            # Scale and comparison
            'scale': "Visual size comparison showing Betelgeuse compared to solar system, Sun at center with Mars orbit, massive star scale",
            'size comparison': "Split screen showing size difference between Sun and Betelgeuse, dramatic scale visualization",

            # Observational
            'night sky': "Beautiful starfield with Orion constellation prominent, Milky Way visible, mountain silhouette, astrophotography style",
            'observation': "Person using telescope at night, eye to eyepiece, stars reflected in optics, documentary style",
            'amateur astronomer': "Backyard astronomer with telescope looking at night sky, suburban setting, relatable perspective",
        }

        # Break script into paragraphs
        paragraphs = [p.strip() for p in script_content.split('\n\n') if p.strip() and not p.strip().startswith('#')]

        visual_cues = []
        clip_index = 0

        for para_index, paragraph in enumerate(paragraphs):
            para_lower = paragraph.lower()

            # Skip very short paragraphs or pure markdown
            if len(paragraph) < 100 or paragraph.startswith('##'):
                continue

            # Find all matching keywords in this paragraph
            matches = []
            for keyword, prompt in visual_keywords.items():
                if keyword in para_lower:
                    matches.append((keyword, prompt))

            # If matches found, use them
            if matches:
                for keyword, prompt in matches[:2]:  # Max 2 clips per paragraph
                    visual_cues.append({
                        "index": clip_index,
                        "timestamp": f"~{clip_index * 8}s",
                        "description": keyword.title(),
                        "veo_prompt": prompt,
                        "context": paragraph[:200]
                    })
                    clip_index += 1

            # If no matches, generate generic space visuals
            elif 'star' in para_lower or 'space' in para_lower or 'cosmic' in para_lower:
                # Generic space B-roll
                b_roll_prompts = [
                    "Deep space starfield with distant galaxies, slow camera movement, 4K astrophotography style",
                    "Cinematic shot of colorful nebula, volumetric clouds, star formation visible, epic space documentary",
                    "Wide shot of spiral galaxy, billions of stars, slow rotation, cosmic scale, photorealistic",
                ]
                import random
                prompt = random.choice(b_roll_prompts)

                visual_cues.append({
                    "index": clip_index,
                    "timestamp": f"~{clip_index * 8}s",
                    "description": "Space B-Roll",
                    "veo_prompt": prompt,
                    "context": paragraph[:200]
                })
                clip_index += 1

        return visual_cues

    def generate_veo_prompts(self, script_file):
        """Generate Veo 3 prompts from script"""

        visual_cues = self.parse_script_for_visuals(script_file)

        shot_list = []
        script_name = Path(script_file).stem

        print(f"\n🎬 GENERATING VEO SHOT LIST")
        print(f"{'='*60}")
        print(f"Script: {script_name}")
        print(f"Visual Cues Found: {len(visual_cues)}")
        print(f"Target Clips: {self.config['veo']['clips_per_video']}")

        for i, cue in enumerate(visual_cues):
            # Use pre-generated Veo prompt if available, otherwise optimize description
            if 'veo_prompt' in cue:
                veo_prompt = cue['veo_prompt']
            else:
                veo_prompt = self._optimize_for_veo(cue['description'])

            shot = {
                "shot_number": i + 1,
                "timestamp": cue['timestamp'],
                "duration": self.max_clip_length,
                "veo_prompt": veo_prompt,
                "original_cue": cue['description'],
                "style": self.VEO_STYLE_TEMPLATES['space_documentary'],
                "filename": f"veo_clip_{i+1:03d}.mp4",
                "status": "pending"
            }

            shot_list.append(shot)

        # If not enough clips, suggest creating more
        if len(shot_list) < self.config['veo']['clips_per_video']:
            print(f"\n⚠️  Only {len(shot_list)} visual cues found.")
            print(f"    Recommended: {self.config['veo']['clips_per_video']} clips for 20-min video")
            print(f"    Consider adding more [SHOW: ...] cues to script")

        # Save shot list
        output_file = self.output_dir / f"{script_name}_shotlist.json"
        with open(output_file, 'w') as f:
            json.dump({
                "script_file": str(script_file),
                "generated_at": datetime.now().isoformat(),
                "total_shots": len(shot_list),
                "target_duration": len(shot_list) * self.max_clip_length,
                "shots": shot_list,
                "veo_best_practices": self.VEO_PROMPT_BEST_PRACTICES
            }, f, indent=2)

        # Generate human-readable shot list
        readable_file = self.output_dir / f"{script_name}_shotlist.txt"
        with open(readable_file, 'w') as f:
            f.write(f"VEO 3 SHOT LIST - {script_name}\n")
            f.write(f"{'='*80}\n\n")
            f.write(f"Total Shots: {len(shot_list)}\n")
            f.write(f"Clip Duration: {self.max_clip_length} seconds each\n")
            f.write(f"Total Runtime: ~{len(shot_list) * self.max_clip_length} seconds\n\n")
            f.write(f"{self.VEO_PROMPT_BEST_PRACTICES}\n")
            f.write(f"\n{'='*80}\n")
            f.write(f"SHOT LIST:\n")
            f.write(f"{'='*80}\n\n")

            for shot in shot_list:
                f.write(f"Shot #{shot['shot_number']} [{shot['timestamp']}]\n")
                f.write(f"VEO PROMPT:\n")
                f.write(f"  {shot['veo_prompt']}\n")
                f.write(f"\nORIGINAL CUE: {shot['original_cue']}\n")
                f.write(f"SAVE AS: {shot['filename']}\n")
                f.write(f"\n{'-'*80}\n\n")

        print(f"\n✅ Shot list saved:")
        print(f"   JSON: {output_file}")
        print(f"   TXT:  {readable_file}")
        print(f"\n📋 NEXT STEPS:")
        print(f"1. Open: {readable_file}")
        print(f"2. Go to Veo 3 (Google AI Studio)")
        print(f"3. Generate each clip using the prompts")
        print(f"4. Download clips as: assets/veo_clips/{script_name}/veo_clip_XXX.mp4")
        print(f"5. Run: python src/production/video_assembler.py {script_file}")

        return output_file

    def _optimize_for_veo(self, description):
        """Convert script description to optimized Veo prompt"""

        # Clean up description
        desc = description.strip()

        # Add cinematic style if not present
        style_keywords = ['cinematic', 'documentary', '4K', 'photorealistic']
        if not any(kw in desc.lower() for kw in style_keywords):
            desc = f"Cinematic {desc}, 4K space documentary style"

        # Ensure it's not too long (Veo works best with concise prompts)
        words = desc.split()
        if len(words) > 40:
            desc = ' '.join(words[:40]) + "..."

        # Add common enhancements
        enhancements = {
            "black hole": "dramatic accretion disk, warped spacetime",
            "planet": "detailed surface, atmospheric effects",
            "nebula": "volumetric clouds, star formation",
            "galaxy": "spiral arms, billions of stars",
            "star": "corona, surface detail, dramatic lighting",
            "asteroid": "detailed cratered surface, slowly rotating",
        }

        for keyword, enhancement in enhancements.items():
            if keyword in desc.lower() and enhancement not in desc.lower():
                desc = f"{desc}, {enhancement}"

        return desc

    def create_batch_prompt_file(self, shot_list_file):
        """Create a single file for batch creating all Veo prompts"""

        with open(shot_list_file, 'r') as f:
            data = json.load(f)

        batch_file = Path(shot_list_file).with_suffix('.batch.txt')

        with open(batch_file, 'w') as f:
            f.write("COPY EACH PROMPT BELOW INTO VEO 3\n")
            f.write("="*80 + "\n\n")

            for shot in data['shots']:
                f.write(f"CLIP #{shot['shot_number']} - {shot['filename']}\n")
                f.write(f"{shot['veo_prompt']}\n")
                f.write("\n" + "-"*80 + "\n\n")

        print(f"✅ Batch prompt file: {batch_file}")
        return batch_file


def main():
    """CLI interface"""
    import sys

    generator = VeoShotListGenerator()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "generate":
            if len(sys.argv) < 3:
                print("❌ Usage: python src/production/veo_generator.py generate <script_file>")
                return
            shot_list = generator.generate_veo_prompts(sys.argv[2])
            generator.create_batch_prompt_file(shot_list)

        elif command == "batch":
            if len(sys.argv) < 3:
                print("❌ Usage: python src/production/veo_generator.py batch <shot_list_json>")
                return
            generator.create_batch_prompt_file(sys.argv[2])

        else:
            print("❌ Unknown command. Use: generate or batch")

    else:
        print("🎬 Veo 3 Shot List Generator")
        print("\nCommands:")
        print("  python src/production/veo_generator.py generate <script_file>")
        print("  python src/production/veo_generator.py batch <shot_list_json>")
        print("\nExample:")
        print("  python src/production/veo_generator.py generate scripts/drafts/black_holes.md")


if __name__ == "__main__":
    main()
