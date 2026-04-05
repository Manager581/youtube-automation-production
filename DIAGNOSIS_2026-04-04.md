# Root Cause Diagnosis — Session 2026-04-04

## Problem Summary
The assembled video has: visuals that don't match narration, repeated images throughout, weak/generic visuals instead of specific supporting footage, and the intro lacks key visuals (stock chart rising, Zuckerberg wealth).

## ROOT CAUSE 1: Director picks ONE visual per segment, doesn't sub-edit

**What happens:** The director assigns one `visual_file` per narration segment. Segment 0 is 77 words (33 seconds). The director picks `Facebook_to_pay_5_billion_fine.mp4` for ALL 33 seconds. But during those 33 seconds, the narration covers:
- "Facebook was fined $5 billion" (needs: news footage ✅)
- "Facebook's stock went up" (needs: stock chart — MISSING)
- "Zuckerberg gained $1.1 billion" (needs: Zuckerberg wealth visual — MISSING)
- "The punishment made them richer" (needs: contrast visual — MISSING)

**Why:** The director was designed to pick ONE visual per narrative segment. It doesn't sub-divide segments into visual beats. ColdFusion/HMW cut every 5-7 seconds with a new visual supporting the current sentence. Our director cuts every 15-40 seconds.

**Fix:** The director needs to produce MULTIPLE visual picks per segment — one per sentence or narrative beat. Each 5-7s should get its own visual choice based on what the VO is saying at THAT moment.

## ROOT CAUSE 2: 18 images used 3+ times each = visual repetition

**What happens:** The director reuses the same images throughout. `corporate_boardroom_meeting_stock.mp4` appears at 207s, 303s, and 1306s. `data_center_servers.mp4` at 327s, 366s, and 657s. 18 files are used 3+ times.

**Why:** The director picks from a pool of 23 video clips and ~80 images (per segment directories). When multiple segments cover similar topics (corporate fines, data centers, courts), the director picks the same "best match" clip every time. There's no deduplication constraint — the director doesn't know what it already picked.

**Fix:** Add a `used_visuals` accumulator to the director. Each visual gets a usage cap (max 2 per video). After the cap, the director must pick an alternative or flag for gap-fill sourcing.

## ROOT CAUSE 3: 41 visual-narration mismatches (24% generic stock footage)

**What happens:** When the VO says "Ford kept selling cars" the visual shows `Department_of_Justice_building.mp4`. When the VO says "Facebook's stock went up" the visual shows `Wall_Street_trading_floor.mp4` (generic stock floor, not Facebook stock chart).

**Why:** The director's vision analysis describes each clip/image in general terms. `Wall_Street_trading_floor.mp4` is described as "stock trading" which fuzzy-matches "stock went up." But it's not SPECIFICALLY the Facebook stock chart on the day of the fine. The director doesn't distinguish between "generic stock footage" and "specific supporting evidence."

**Fix:** The director needs a specificity check: when the narration mentions a named entity (Facebook, Ford, Zuckerberg), the visual MUST contain that entity. Generic footage is only acceptable for abstract/philosophical narration ("The formula evolved").

## ROOT CAUSE 4: Supporting visuals exist but aren't being used

**What happens:** We HAVE `wiki_1_Facebook_stock_marke.jpg`, `pexels_5668473_Facebook_stock_market_trading_.jpg`, and `pexels_5668473_worried_investor_stock_market_.jpg` in the gap_fills directory. These are exactly the visuals needed for "Facebook's stock went up." But the director never picks them.

**Why:** The director was fed vision descriptions of footage in `footage/breaking_law/images/seg_NNN/` directories, but gap_fill images (`footage/breaking_law/gap_fills/images/`) may not have been included in its prompt. The gap resolver sourced these images AFTER the director ran, so the director never saw them.

**Fix:** Run the director AFTER gap-fill sourcing, not before. Or re-run the director with the full image pool including gap-fills.

## ROOT CAUSE 5: FCPXML builder splits long images with RANDOM alternatives

**What happens:** When a segment holds one image for 30+ seconds, the builder splits it into 5-6s sub-clips. But it fills the extra slots by rotating through ALL images in the media cache, regardless of relevance. This produces "multiple repeated pictures throughout" that have nothing to do with the narration.

**Why:** My image rotation code (`img_rot_idx % len(avail_images)`) picks from the entire pool without semantic filtering. It's the same random gap-fill problem I already fixed on V1 but reintroduced in the splitting code.

**Fix:** When splitting a long image segment, the sub-images should come from the SAME topic. Use the segment's narration text to filter available images by keyword match.

## ROOT CAUSE 6: Executive producer doesn't check visual-narration sync

**What happens:** The exec producer checks structural things (track alignment, clip counts, source diversity) but never asks "does the image at 20s match what the VO says at 20s?"

**Why:** The exec producer was designed as a post-build structural check, not a content review. It doesn't have access to narration text + visual descriptions together.

**Fix:** Add a content sync check: for each segment, verify the visual file's vision description contains at least one keyword from the narration. Flag mismatches for director review.

## Impact Assessment

| Root Cause | Severity | Fix Complexity | Fix Location |
|-----------|----------|---------------|-------------|
| 1. One visual per segment | HIGH | MEDIUM | director.py — sub-edit segments |
| 2. Image reuse (no cap) | MEDIUM | LOW | director.py — usage accumulator |
| 3. Generic vs specific | HIGH | MEDIUM | director.py — entity matching |
| 4. Gap-fills not in director pool | HIGH | LOW | pipeline ordering — director after gap-fill |
| 5. Random split images | MEDIUM | LOW | fcpxml_builder_v2.py — keyword filter |
| 6. No content sync in exec producer | MEDIUM | MEDIUM | executive_producer.py — add check |

## Recommended Fix Order (next session)

1. **Fix #5** (random split images → keyword-filtered) — 20 min, biggest bang for buck
2. **Fix #2** (image reuse cap) — 15 min, reduces repetition
3. **Fix #4** (gap-fills in director pool) — 10 min, unlocks 250+ unused images
4. **Fix #1** (sub-edit segments) — 2-3 hours, fundamental improvement
5. **Fix #3** (entity matching) — 1 hour, requires director re-run
6. **Fix #6** (exec producer content sync) — 1 hour, catches future issues
