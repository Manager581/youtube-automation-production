"""
Video Assembler
Combines Veo clips, NASA footage, voiceover, music, and SFX into final video
"""

import json
import yaml
import random
from pathlib import Path
from datetime import datetime
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip,
    concatenate_videoclips, CompositeAudioClip, TextClip
)
from moviepy.video.fx import resize, fadein, fadeout


class VideoAssembler:
    """Assembles final video from all components"""

    def __init__(self, config_path="config/config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.output_dir = Path("output/videos")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.fps = self.config['video']['fps']
        self.resolution = tuple(map(int, self.config['video']['resolution'].split('x')))

    def load_shot_list(self, shot_list_file):
        """Load Veo shot list JSON"""
        with open(shot_list_file, 'r') as f:
            return json.load(f)

    def load_assets(self, script_name):
        """Discover all available video assets"""

        assets = {
            "veo_clips": [],
            "nasa_footage": [],
            "voiceover": None,
            "music": [],
            "sfx": []
        }

        # Find Veo clips
        veo_dir = Path("assets/veo_clips") / script_name
        if veo_dir.exists():
            assets["veo_clips"] = sorted(veo_dir.glob("*.mp4"))

        # Find NASA footage
        nasa_dir = Path("assets/nasa_footage")
        if nasa_dir.exists():
            assets["nasa_footage"] = list(nasa_dir.glob("*.mp4"))

        # Find voiceover
        vo_dir = Path("assets/voiceovers")
        if vo_dir.exists():
            voiceovers = list(vo_dir.glob(f"{script_name}*.mp3")) + list(vo_dir.glob(f"{script_name}*.wav"))
            assets["voiceover"] = voiceovers[0] if voiceovers else None

        # Find music
        music_dir = Path("assets/music")
        if music_dir.exists():
            assets["music"] = list(music_dir.glob("*.mp3")) + list(music_dir.glob("*.wav"))

        # Find SFX
        sfx_dir = Path("assets/sfx")
        if sfx_dir.exists():
            assets["sfx"] = list(sfx_dir.glob("*.mp3")) + list(sfx_dir.glob("*.wav"))

        print(f"\n📦 ASSETS DISCOVERED:")
        print(f"   Veo clips: {len(assets['veo_clips'])}")
        print(f"   NASA footage: {len(assets['nasa_footage'])}")
        print(f"   Voiceover: {'✅' if assets['voiceover'] else '❌ MISSING'}")
        print(f"   Music tracks: {len(assets['music'])}")
        print(f"   SFX: {len(assets['sfx'])}")

        return assets

    def create_video_sequence(self, shot_list, assets):
        """Create video sequence from shot list and assets"""

        clips = []
        all_footage = assets['veo_clips'] + assets['nasa_footage']

        print(f"\n🎬 ASSEMBLING VIDEO SEQUENCE")
        print(f"{'='*60}")

        for i, shot in enumerate(shot_list['shots']):
            print(f"Processing shot {i+1}/{len(shot_list['shots'])}: {shot['filename']}")

            # Try to find matching Veo clip
            veo_clip_path = Path("assets/veo_clips") / Path(shot_list['script_file']).stem / shot['filename']

            if veo_clip_path.exists():
                # Use Veo clip
                clip = VideoFileClip(str(veo_clip_path))
                print(f"   ✅ Using Veo clip: {shot['filename']}")

            elif all_footage:
                # Fallback to NASA or other footage
                random_footage = random.choice(all_footage)
                clip = VideoFileClip(str(random_footage))

                # Trim to max 8 seconds
                if clip.duration > shot['duration']:
                    start_time = random.uniform(0, clip.duration - shot['duration'])
                    clip = clip.subclip(start_time, start_time + shot['duration'])

                print(f"   ⚠️  Using fallback: {random_footage.name}")

            else:
                # No footage available - create placeholder
                print(f"   ❌ No footage available - creating placeholder")
                clip = TextClip(
                    "Footage Needed",
                    fontsize=70,
                    color='white',
                    bg_color='black',
                    size=self.resolution
                ).set_duration(shot['duration'])

            # Resize to target resolution
            clip = clip.resize(self.resolution)

            # Add fade in/out
            clip = clip.fx(fadein, 0.3).fx(fadeout, 0.3)

            clips.append(clip)

        print(f"✅ Sequence complete: {len(clips)} clips")
        return clips

    def assemble_video(self, script_name, shot_list_file, voiceover_file=None):
        """Main assembly function"""

        print(f"\n🎥 VIDEO ASSEMBLY STARTED")
        print(f"{'='*60}")
        print(f"Script: {script_name}")
        print(f"Shot List: {shot_list_file}")

        # Load shot list
        shot_list = self.load_shot_list(shot_list_file)

        # Load assets
        assets = self.load_assets(script_name)

        # Override voiceover if provided
        if voiceover_file:
            assets['voiceover'] = Path(voiceover_file)

        if not assets['voiceover']:
            print("\n❌ ERROR: No voiceover file found!")
            print(f"   Please add voiceover to: assets/voiceovers/{script_name}.mp3")
            return None

        # Load voiceover audio
        voiceover = AudioFileClip(str(assets['voiceover']))
        video_duration = voiceover.duration

        print(f"\n📊 VIDEO SPECS:")
        print(f"   Duration: {video_duration:.1f} seconds ({video_duration/60:.1f} minutes)")
        print(f"   Resolution: {self.resolution[0]}x{self.resolution[1]}")
        print(f"   FPS: {self.fps}")

        # Create video sequence
        video_clips = self.create_video_sequence(shot_list, assets)

        # Concatenate all clips
        print(f"\n🔗 Concatenating {len(video_clips)} clips...")
        final_video = concatenate_videoclips(video_clips, method="compose")

        # Adjust video duration to match voiceover
        if final_video.duration < video_duration:
            # Loop video if too short
            print(f"   ⚠️  Video too short, looping to match voiceover")
            loops_needed = int(video_duration / final_video.duration) + 1
            final_video = concatenate_videoclips([final_video] * loops_needed)

        # Trim to exact voiceover length
        final_video = final_video.subclip(0, video_duration)

        # Add background music if available
        audio_tracks = [voiceover]

        if assets['music']:
            music_track = random.choice(assets['music'])
            print(f"\n🎵 Adding background music: {music_track.name}")

            music = AudioFileClip(str(music_track))

            # Loop music if too short
            if music.duration < video_duration:
                loops = int(video_duration / music.duration) + 1
                from moviepy.audio.AudioClip import concatenate_audioclips
                music = concatenate_audioclips([music] * loops)

            music = music.subclip(0, video_duration)

            # Reduce volume
            music = music.volumex(self.config['audio']['background_music_volume'])
            audio_tracks.append(music)

        # Composite audio
        final_audio = CompositeAudioClip(audio_tracks)
        final_video = final_video.set_audio(final_audio)

        # Export final video
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{script_name}_{timestamp}.mp4"
        output_path = self.output_dir / output_filename

        print(f"\n📤 EXPORTING FINAL VIDEO...")
        print(f"   Output: {output_path}")
        print(f"   This may take a while...")

        final_video.write_videofile(
            str(output_path),
            fps=self.fps,
            codec=self.config['video']['codec'],
            audio_bitrate=self.config['audio']['audio_bitrate'],
            bitrate=self.config['video']['video_bitrate'],
            threads=4,
            preset='medium'
        )

        # Close clips
        for clip in video_clips:
            clip.close()
        final_video.close()
        voiceover.close()

        print(f"\n{'='*60}")
        print(f"✅ VIDEO ASSEMBLY COMPLETE!")
        print(f"{'='*60}")
        print(f"Output: {output_path}")
        print(f"Duration: {video_duration/60:.1f} minutes")
        print(f"Size: {output_path.stat().st_size / (1024*1024):.1f} MB")
        print(f"\n📋 NEXT STEPS:")
        print(f"1. Review video: {output_path}")
        print(f"2. Generate thumbnail: python src/distribution/thumbnail_generator.py {script_name}")
        print(f"3. Upload to YouTube: python src/distribution/youtube_uploader.py {output_path}")

        return str(output_path)


def main():
    """CLI interface"""
    import sys

    assembler = VideoAssembler()

    if len(sys.argv) < 3:
        print("🎥 Video Assembler")
        print("\nUsage:")
        print("  python src/production/video_assembler.py <script_name> <shot_list_json> [voiceover_file]")
        print("\nExample:")
        print("  python src/production/video_assembler.py black_holes prompts/veo_shots/black_holes_shotlist.json assets/voiceovers/black_holes.mp3")
        return

    script_name = sys.argv[1]
    shot_list_file = sys.argv[2]
    voiceover_file = sys.argv[3] if len(sys.argv) > 3 else None

    assembler.assemble_video(script_name, shot_list_file, voiceover_file)


if __name__ == "__main__":
    main()
