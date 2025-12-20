"""
Quick Video Test Generator
Tests the workflow with intro audio + NASA footage
"""

from pathlib import Path
try:
    from moviepy.editor import *
except ImportError:
    # MoviePy 2.x uses different import structure
    from moviepy import AudioFileClip, ImageClip, concatenate_videoclips
import random


def create_test_video(voiceover_path, output_name="test_output"):
    """Create a quick test video from voiceover + NASA images"""

    print("\n🎬 CREATING TEST VIDEO")
    print("=" * 80)

    # Load voiceover
    print(f"📂 Loading voiceover: {voiceover_path}")
    audio = AudioFileClip(str(voiceover_path))
    duration = audio.duration
    print(f"   Duration: {duration:.1f} seconds")

    # Get NASA images
    nasa_dir = Path("assets/nasa_footage")
    images = list(nasa_dir.glob("*.jpg")) + list(nasa_dir.glob("*.png"))

    if not images:
        print("❌ No NASA images found!")
        return

    print(f"📸 Found {len(images)} NASA images")

    # Calculate how many images we need
    clip_duration = 5  # Each image shows for 5 seconds
    num_clips = int(duration / clip_duration) + 1

    print(f"🎞️  Creating {num_clips} clips...")

    # Create video clips with Ken Burns effect
    clips = []
    selected_images = random.sample(images, min(num_clips, len(images)))

    for i, img_path in enumerate(selected_images):
        print(f"   Processing image {i+1}/{len(selected_images)}: {img_path.name}")

        # Load image and resize to 1080p for consistent output
        img_clip = ImageClip(str(img_path)).with_duration(clip_duration)

        # Pre-resize to 1.2x size (this is faster than per-frame lambda)
        # Ken Burns effect: Start at normal size, zoom to 1.2x
        img_clip = img_clip.resized(1.2).with_duration(clip_duration)

        # Note: For now using static zoom. Full Ken Burns with pan
        # will be added in production pipeline with GPU acceleration
        clips.append(img_clip)

    # Concatenate all clips
    print(f"\n🔗 Combining {len(clips)} clips...")
    video = concatenate_videoclips(clips, method="compose")

    # Trim to match audio duration
    video = video.subclipped(0, min(video.duration, duration))

    # Add voiceover
    print("🎵 Adding voiceover...")
    final_video = video.with_audio(audio)

    # Export
    output_path = Path("output") / f"{output_name}.mp4"
    output_path.parent.mkdir(exist_ok=True)

    print(f"\n📤 Exporting video...")
    print(f"   Output: {output_path}")

    final_video.write_videofile(
        str(output_path),
        fps=30,
        codec='libx264',
        audio_codec='aac',
        temp_audiofile='temp-audio.m4a',
        remove_temp=True,
        preset='medium'
    )

    print("\n✅ TEST VIDEO COMPLETE!")
    print("=" * 80)
    print(f"📹 Video saved: {output_path}")
    print(f"⏱️  Duration: {duration:.1f} seconds")
    print(f"\n💡 NEXT STEPS:")
    print(f"1. Watch the video: {output_path}")
    print(f"2. Check if Ken Burns effect looks good on NASA images")
    print(f"3. Verify audio quality is acceptable")
    print(f"4. If satisfied, record full 18-minute voiceover")
    print(f"5. Run full pipeline for complete video\n")

    return str(output_path)


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 2:
        print("\nUsage: python src/test_video_generator.py <voiceover_file>")
        print("\nExample:")
        print("  python src/test_video_generator.py assets/voiceovers/betelgeuse_test.mp3")
        return

    voiceover = sys.argv[1]
    output_name = Path(voiceover).stem if len(sys.argv) < 3 else sys.argv[2]

    create_test_video(voiceover, output_name)


if __name__ == "__main__":
    main()
