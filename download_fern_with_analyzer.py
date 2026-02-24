#!/usr/bin/env python3
"""Download Fern videos using the working CreatorAnalyzer"""
import sys
sys.path.insert(0, 'src')

from phase1_analyzer import CreatorAnalyzer

# Initialize analyzer
analyzer = CreatorAnalyzer(output_dir="analysis")

# Analyze Fern channel - downloads top 30 videos automatically
results = analyzer.analyze_channel_from_url(
    channel_url="https://www.youtube.com/@fern-tv",
    creator_name="fern",
    months_back=12,  # Last year of content
    max_videos=30,    # Top 30 videos
    auto_confirm=True  # Skip confirmation
)

print("\n✅ Download and analysis complete!")
print(f"Results: {results}")
