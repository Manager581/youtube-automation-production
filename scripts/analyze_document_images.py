#!/usr/bin/env python3
"""
Analyze document images to find key visual regions (text blocks, stamps,
headers, signatures) and save focus maps.

Uses OpenCV only — no OCR libraries needed. Detects whether an image is
actually a document (high text density, low saturation, rectangular layout)
vs a photo, and skips non-documents.

Usage:
    venv/bin/python scripts/analyze_document_images.py
"""

import json
import os
import sys
from pathlib import Path

import cv2
import numpy as np

# ── Paths ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
STORYBOARD_PATH = ROOT / "storyboards" / "frank_olson_cia_scientist_lsd_murder_cover_up_directed.json"
IMAGES_DIR = ROOT / "footage" / "fern_clone" / "frank_olson_cia_scientist_lsd_murder_cover_up" / "images"
OUTPUT_PATH = ROOT / "footage" / "fern_clone" / "frank_olson_cia_scientist_lsd_murder_cover_up" / "document_focus_maps.json"

# ── Thresholds ─────────────────────────────────────────────────────────
# Document detection: an image is a document if it has high text density
# and low color saturation (mostly grayscale ink on paper).
MIN_TEXT_DENSITY = 0.04       # fraction of image area covered by text contours
MAX_MEAN_SATURATION = 80      # 0-255; documents are desaturated
MIN_RECT_RATIO = 0.30         # fraction of contours that are roughly rectangular


def is_document(img: np.ndarray) -> tuple[bool, str]:
    """Determine if an image is a document vs a photograph.

    Returns (is_doc, reason).
    """
    h, w = img.shape[:2]
    total_area = h * w

    # Check saturation — documents are low-saturation
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mean_sat = float(np.mean(hsv[:, :, 1]))

    # Find text-like contours via adaptive threshold
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 10
    )
    # Dilate to merge nearby text into blocks
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
    dilated = cv2.dilate(binary, kernel, iterations=2)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Text density = total contour area / image area
    contour_area = sum(cv2.contourArea(c) for c in contours)
    text_density = contour_area / total_area if total_area > 0 else 0

    # Rectangularity — how many contours are roughly rectangular
    rect_count = 0
    for c in contours:
        area = cv2.contourArea(c)
        if area < 100:
            continue
        x_, y_, w_, h_ = cv2.boundingRect(c)
        rect_area = w_ * h_
        if rect_area > 0 and area / rect_area > 0.5:
            rect_count += 1
    total_significant = sum(1 for c in contours if cv2.contourArea(c) >= 100)
    rect_ratio = rect_count / total_significant if total_significant > 0 else 0

    # Decision logic
    reasons = []
    score = 0

    if mean_sat < MAX_MEAN_SATURATION:
        score += 1
        reasons.append(f"low_sat({mean_sat:.0f})")
    else:
        reasons.append(f"high_sat({mean_sat:.0f})")

    if text_density > MIN_TEXT_DENSITY:
        score += 1
        reasons.append(f"text_dense({text_density:.3f})")
    else:
        reasons.append(f"low_text({text_density:.3f})")

    if rect_ratio > MIN_RECT_RATIO:
        score += 1
        reasons.append(f"rectangular({rect_ratio:.2f})")
    else:
        reasons.append(f"irregular({rect_ratio:.2f})")

    is_doc = score >= 2
    return is_doc, " | ".join(reasons)


def detect_colored_stamps(img: np.ndarray, h: int, w: int) -> list[dict]:
    """Find high-contrast colored regions (stamps, seals) using HSV filtering."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    regions = []

    # Red stamps (two ranges because red wraps around 0/180 in HSV)
    lower_red1 = np.array([0, 80, 80])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 80, 80])
    upper_red2 = np.array([180, 255, 255])
    mask_red = cv2.inRange(hsv, lower_red1, upper_red1) | cv2.inRange(hsv, lower_red2, upper_red2)

    # Blue stamps
    lower_blue = np.array([100, 80, 80])
    upper_blue = np.array([130, 255, 255])
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

    for mask, label in [(mask_red, "stamp_red"), (mask_blue, "stamp_blue")]:
        # Clean up noise
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in contours:
            area = cv2.contourArea(c)
            # Stamps are usually at least 0.1% of image area
            if area < (h * w * 0.001):
                continue
            x_, y_, w_, h_ = cv2.boundingRect(c)
            regions.append({
                "type": "stamp",
                "subtype": label,
                "y": round((y_ + h_ / 2) / h, 3),
                "x": round((x_ + w_ / 2) / w, 3),
                "w": round(w_ / w, 3),
                "h": round(h_ / h, 3),
                "area": area,
            })

    return regions


def detect_text_blocks(img: np.ndarray, h: int, w: int) -> list[dict]:
    """Find text block regions using adaptive thresholding + contour detection."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Adaptive threshold to find dark-on-light text
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 10
    )

    # Dilate aggressively to merge text lines into blocks
    kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 3))
    dilated = cv2.dilate(binary, kernel_h, iterations=3)
    kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 8))
    dilated = cv2.dilate(dilated, kernel_v, iterations=2)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    blocks = []
    min_block_area = h * w * 0.005  # at least 0.5% of image

    for c in contours:
        area = cv2.contourArea(c)
        if area < min_block_area:
            continue
        x_, y_, w_, h_ = cv2.boundingRect(c)
        # Filter out very thin or very small bounding boxes
        if w_ < w * 0.05 or h_ < h * 0.02:
            continue

        # Classify: header if in top 20%, otherwise text_block
        center_y = y_ + h_ / 2
        block_type = "header" if center_y < h * 0.20 else "text_block"

        blocks.append({
            "type": block_type,
            "y": round((y_ + h_ / 2) / h, 3),
            "x": round((x_ + w_ / 2) / w, 3),
            "w": round(w_ / w, 3),
            "h": round(h_ / h, 3),
            "area": area,
        })

    # Sort by area descending (largest blocks first)
    blocks.sort(key=lambda b: b["area"], reverse=True)
    return blocks


def detect_handwritten(img: np.ndarray, h: int, w: int) -> list[dict]:
    """Detect handwritten annotations by looking for irregular (non-rectangular)
    ink regions that differ from typeset text.

    Handwritten marks tend to be more irregularly shaped with lower solidity
    (contour area / convex hull area).
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 8
    )

    # Mild dilation — less than text blocks to preserve shape irregularity
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated = cv2.dilate(binary, kernel, iterations=1)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    annotations = []
    min_area = h * w * 0.002
    max_area = h * w * 0.15  # very large = probably a text block, not handwriting

    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area or area > max_area:
            continue

        hull = cv2.convexHull(c)
        hull_area = cv2.contourArea(hull)
        if hull_area == 0:
            continue

        solidity = area / hull_area
        x_, y_, w_, h_ = cv2.boundingRect(c)
        rect_area = w_ * h_
        extent = area / rect_area if rect_area > 0 else 0

        # Handwriting: lower solidity and extent than typeset text
        # Typeset text blocks tend to be high solidity (>0.7) and high extent (>0.6)
        if solidity < 0.55 and extent < 0.45:
            annotations.append({
                "type": "handwritten",
                "y": round((y_ + h_ / 2) / h, 3),
                "x": round((x_ + w_ / 2) / w, 3),
                "w": round(w_ / w, 3),
                "h": round(h_ / h, 3),
                "area": area,
                "solidity": round(solidity, 3),
            })

    annotations.sort(key=lambda a: a["area"], reverse=True)
    return annotations[:5]  # limit to top 5


def analyze_document(img_path: str) -> dict | None:
    """Analyze a single document image and return focus map data."""
    img = cv2.imread(img_path)
    if img is None:
        print(f"  SKIP: could not read {img_path}")
        return None

    h, w = img.shape[:2]
    filename = os.path.basename(img_path)

    # Check if it's actually a document
    is_doc, reason = is_document(img)
    if not is_doc:
        print(f"  SKIP (not a document): {filename} — {reason}")
        return None

    print(f"  ANALYZING: {filename} ({w}x{h}) — {reason}")

    # Detect regions
    stamps = detect_colored_stamps(img, h, w)
    text_blocks = detect_text_blocks(img, h, w)
    handwritten = detect_handwritten(img, h, w)

    # Assign priorities: stamps > headers > handwritten > text_blocks
    all_regions = []
    priority = 1

    for s in stamps:
        s["priority"] = priority
        del s["area"]
        if "subtype" in s:
            del s["subtype"]
        all_regions.append(s)
        priority += 1

    headers = [b for b in text_blocks if b["type"] == "header"]
    for hdr in headers:
        hdr["priority"] = priority
        del hdr["area"]
        all_regions.append(hdr)
        priority += 1

    for ann in handwritten:
        ann["priority"] = priority
        if "solidity" in ann:
            del ann["solidity"]
        del ann["area"]
        all_regions.append(ann)
        priority += 1

    body_blocks = [b for b in text_blocks if b["type"] == "text_block"]
    for block in body_blocks[:5]:  # top 5 largest
        block["priority"] = priority
        del block["area"]
        all_regions.append(block)
        priority += 1

    # Determine recommended focus y
    # Priority: stamp > header > handwritten > largest text block
    if stamps:
        focus_y = stamps[0]["y"]
    elif headers:
        focus_y = headers[0]["y"]
    elif handwritten:
        focus_y = handwritten[0]["y"]
    elif body_blocks:
        focus_y = body_blocks[0]["y"]
    else:
        focus_y = 0.5

    # Build scan path — unique sorted y positions for smooth pan
    scan_ys = set()
    scan_ys.add(0.0)  # start at top
    for r in all_regions:
        scan_ys.add(round(r["y"], 2))
    scan_ys.add(round(min(1.0, max(r["y"] for r in all_regions) + 0.1), 2) if all_regions else 0.5)
    scan_path = sorted(scan_ys)

    # Deduplicate scan path (remove points too close together)
    filtered_path = [scan_path[0]]
    for y in scan_path[1:]:
        if y - filtered_path[-1] >= 0.08:
            filtered_path.append(y)
    scan_path = filtered_path

    result = {
        "image": filename,
        "dimensions": {"width": w, "height": h},
        "regions": all_regions,
        "recommended_focus_y": round(focus_y, 3),
        "scan_path": scan_path,
        "region_counts": {
            "stamps": len(stamps),
            "headers": len(headers),
            "handwritten": len(handwritten),
            "text_blocks": len(body_blocks),
        },
    }

    print(f"    Regions: {len(stamps)} stamps, {len(headers)} headers, "
          f"{len(handwritten)} handwritten, {len(body_blocks)} text blocks")
    print(f"    Focus Y: {focus_y:.3f}  |  Scan path: {scan_path}")

    return result


def main():
    print("=" * 60)
    print("Document Image Analyzer — Focus Map Generator")
    print("=" * 60)

    # Load storyboard
    if not STORYBOARD_PATH.exists():
        print(f"ERROR: Storyboard not found at {STORYBOARD_PATH}")
        sys.exit(1)

    with open(STORYBOARD_PATH) as f:
        storyboard = json.load(f)

    # Find all document segments and their unique images
    doc_images = set()
    doc_segments = []  # (scene_idx, seg_idx, image_path)

    for si, scene in enumerate(storyboard["scenes"]):
        for sj, seg in enumerate(scene["segments"]):
            cp = seg.get("composition_plan", {})
            if cp.get("content_type") == "document":
                img_rel = cp.get("primary_image", "")
                if img_rel:
                    # primary_image is like "images/wiki_foo.jpg" — strip prefix
                    img_name = os.path.basename(img_rel)
                    img_path = str(IMAGES_DIR / img_name)
                    doc_images.add((img_name, img_path))
                    doc_segments.append((si, sj, img_name))

    print(f"\nFound {len(doc_segments)} document segments using {len(doc_images)} unique images.\n")

    # Analyze each unique document image
    focus_maps = {}
    for img_name, img_path in sorted(doc_images):
        if not os.path.exists(img_path):
            print(f"  SKIP: file not found — {img_name}")
            continue
        result = analyze_document(img_path)
        if result is not None:
            focus_maps[img_name] = result

    print(f"\n{'=' * 60}")
    print(f"Analyzed {len(focus_maps)} documents out of {len(doc_images)} unique images.")

    # Save focus maps
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    focus_list = list(focus_maps.values())
    with open(OUTPUT_PATH, "w") as f:
        json.dump(focus_list, f, indent=2)
    print(f"Saved focus maps to: {OUTPUT_PATH}")

    # Update storyboard with focus data
    updates = 0
    for si, sj, img_name in doc_segments:
        if img_name in focus_maps:
            fm = focus_maps[img_name]
            seg = storyboard["scenes"][si]["segments"][sj]
            seg["composition_plan"]["document_focus_y"] = fm["recommended_focus_y"]
            seg["composition_plan"]["document_scan_path"] = fm["scan_path"]
            updates += 1

    with open(STORYBOARD_PATH, "w") as f:
        json.dump(storyboard, f, indent=2)
    print(f"Updated {updates} storyboard segments with focus data.")
    print("Done.")


if __name__ == "__main__":
    main()
