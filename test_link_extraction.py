#!/usr/bin/env python3
"""
Test script to verify Genius link extraction logic
"""

import re

# Same pattern as in the main script
GENIUS_LINK_PATTERN = re.compile(r'https?geni\.?us(\w+)', re.IGNORECASE)

def extract_genius_link(filename: str):
    """Extract and fix malformed Genius link from filename."""
    match = GENIUS_LINK_PATTERN.search(filename)
    if match:
        code = match.group(1)
        return f"https://geni.us/{code}"
    return None

# Test cases based on user's actual filenames
test_cases = [
    "2-in-1 Mixer httpsgeni.usxh2SUO.mp4",
    "3-in-1 Vacuum httpsgeni.usABC123.mp4",
    "3-Tier Pull-Down Spice httpsgeniusXYZ789.mp4",
    "Product Name httpsgeni.us123ABC.mov",
    "No Link Here.mp4",
    "Another File.mp4",
]

print("Testing Genius Link Extraction")
print("=" * 60)

for filename in test_cases:
    link = extract_genius_link(filename)
    status = "✓" if link else "✗"
    print(f"{status} {filename}")
    if link:
        print(f"  → {link}")
    else:
        print(f"  → No link found")
    print()

print("=" * 60)
print("Test complete!")
