"""
FAST Video Test Generator using ffmpeg
Renders in seconds, not hours
"""

from pathlib import Path
import subprocess
import random


def create_test_video_fast(voiceover_path, output_name="test_output"):
    """Create video using ffmpeg - 100x faster than MoviePy"""

    print("\n🎬 CREATING TEST VIDEO (FFMPEG)")
    print("=" * 80)

    # Get NASA images
    nasa_dir = Path("assets/nasa_footage")
    images = list(nasa_dir.glob("*.jpg")) + list(nasa_dir.glob("*.png"))

    if not images:
        print("❌ No NASA images found!")
        return

    print(f"📸 Found {len(images)} NASA images")

    # Get audio duration
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', str(voiceover_path)],
        capture_output=True, text=True
    )
    duration = float(result.stdout.strip())
    print(f"🎵 Audio duration: {duration:.1f} seconds")

    # Calculate clips needed
    clip_duration = 5
    num_clips = int(duration / clip_duration) + 1
    selected_images = random.sample(images, min(num_clips, len(images)))

    print(f"🎞️  Will use {len(selected_images)} images")

    # Create concat file for ffmpeg
    concat_file = Path("temp/concat.txt")
    concat_file.parent.mkdir(exist_ok=True)

    with open(concat_file, 'w') as f:
        for img in selected_images:
            f.write(f"file '{img.absolute()}'\n")
            f.write(f"duration {clip_duration}\n")
        # Last image needs to be repeated for ffmpeg concat
        f.write(f"file '{selected_images[-1].absolute()}'\n")

    print(f"\n⚡ Rendering with ffmpeg (FAST!)...")

    # Output path
    output_path = Path("output") / f"{output_name}.mp4"
    output_path.parent.mkdir(exist_ok=True)

    # Create video with ffmpeg (single command - FAST!)
    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', str(concat_file),
        '-i', str(voiceover_path),
        '-t', str(duration),
        '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-c:a', 'aac',
        '-shortest',
        str(output_path)
    ]

    subprocess.run(cmd, check=True)

    print("\n✅ TEST VIDEO COMPLETE!")
    print("=" * 80)
    print(f"📹 Video saved: {output_path}")
    print(f"⏱️  Duration: {duration:.1f} seconds")
    print(f"\n💡 NEXT STEPS:")
    print(f"1. Watch the video: {output_path}")
    print(f"2. Verify quality is acceptable")
    print(f"3. Record full 18-minute voiceover")
    print(f"4. Run full pipeline\n")

    # Cleanup
    concat_file.unlink()

    return str(output_path)


def main():
    """CLI interface"""
    import sys

    if len(sys.argv) < 2:
        print("\nUsage: python src/test_video_generator_ffmpeg.py <voiceover_file>")
        print("\nExample:")
        print("  python src/test_video_generator_ffmpeg.py assets/voiceovers/betelgeuse_intro.mp3")
        return

    voiceover = sys.argv[1]
    output_name = Path(voiceover).stem if len(sys.argv) < 3 else sys.argv[2]

    create_test_video_fast(voiceover, output_name)


if __name__ == "__main__":
    main()
