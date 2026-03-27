# PLAYBOOK GAPS REPORT
## Analysis Data NOT Yet Captured in Playbook JSON Files
Generated: 2026-03-27

---

## METHODOLOGY

**Playbook files reviewed:**
- `playbook/editing.json`
- `playbook/intros.json`
- `playbook/scripting.json`
- `playbook/retention_delivery.json`
- `playbook/titles_thumbnails.json`
- `playbook/ideation.json`
- `playbook/sources.json`
- `playbook/index.json`

**Analysis files reviewed:**
- `analysis/fern/FERN_EDITORIAL_PLAYBOOK.json`
- `analysis/fern/FERN_FORMULA.json` / `FERN_MASTER_FORMULA.json`
- `analysis/fern/FERN_MOTION_FORMULA.json`
- `analysis/fern/FERN_SFX_FORMULA.json`
- `analysis/fern/FERN_TEXT_ANIMATION_FORMULA.json`
- `analysis/fern/FERN_STYLE_GROUND_TRUTH.json`
- `analysis/fern/FERN_CORRELATION_DATA.json`
- `analysis/fern/FERN_FORMULA_SOP.md`
- `analysis/fern/COLOR_GRADE_FORMULA.json`
- `analysis/fern/SOUND_DESIGN_FORMULA.json`
- `analysis/fern/SCRIPT_FORMULA.json` / `SCRIPT_STRUCTURE_FORMULA.json`
- `analysis/fern/THUMBNAIL_FORMULA.json`
- `analysis/fern/TITLE_ANGLE_FORMULA.json`
- `analysis/fern/VISUAL_FORMULA_HYBRID_qwen-vl.json`
- `analysis/fern/MUSIC_IDENTITY.json`
- `analysis/fern/aVA7aXOH1pk_audio_analysis.json` (+ 2 more per-video audio files)
- `watop_patterns.json`
- `analysis_videos_1_3.json`
- `analysis/watop/complete_analysis.json`
- `production_guide_secret_scores.md`

---

## GAP 1: SOUND DESIGN FORMULA (CRITICAL)

**Source:** `FERN_SFX_FORMULA.json`, `SOUND_DESIGN_FORMULA.json`

**What the playbook has:** Generic SFX type list (whoosh, highlight, riser, hit, drone) with qualitative descriptions. No quantitative data.

**What the analysis has that is MISSING from the playbook:**

| Metric | Value | Source |
|--------|-------|--------|
| % of cuts with SFX | 10.9% | FERN_SFX_FORMULA |
| Dominant SFX type | impact_thud (105 instances) | FERN_SFX_FORMULA |
| Secondary SFX type | broadband_whoosh (7 instances) | FERN_SFX_FORMULA |
| Avg SFX loudness ratio vs baseline | 2.26x | FERN_SFX_FORMULA |
| Avg SFX peak offset from cut | -8.2ms (slightly before cut) | FERN_SFX_FORMULA |
| SFX ratio threshold | 1.8x baseline = SFX present | FERN_SFX_FORMULA |
| Verdict | "minimal_sfx: cuts are mostly audio-free" | FERN_SFX_FORMULA |
| Assembler guidance | "No SFX layer needed -- cuts are clean audio transitions" | FERN_SFX_FORMULA |

**SOUND_DESIGN_FORMULA.json additional per-video data:**

| Video | Events/min | Avg gap (sec) | Types |
|-------|-----------|---------------|-------|
| Trump Assassination | 9.0 | 6.0 | sustain_mid (35), riser (10) |
| FBI KKK | 15.2 | 3.6 | sustain_mid (61), riser (9), sustain_low (4), impact_bright (1), whoosh (1) |
| Unabomber | 0.6 | 9.1 | impact_bright (2), sustain_mid (1) |

**Key insight NOT in playbook:** Sound design density varies MASSIVELY by video type. The longer, more narrative Unabomber video has 0.6 events/min, while the action-heavy FBI KKK video has 15.2 events/min. The playbook should encode this relationship between narrative intensity and SFX density.

### Rules to add to `editing.json`:
- SFX should appear on only ~11% of cuts (Fern benchmark)
- Dominant SFX type: impact_thud, not whoosh
- SFX peaks should land ~8ms BEFORE the visual cut, not on or after it
- SFX loudness: 2.26x the baseline audio level
- Sound design density should scale with narrative intensity:
  - Calm exposition: 0.6 events/min
  - Medium paced narrative: 9 events/min
  - High-intensity/action sequences: 15 events/min

---

## GAP 2: EDITING RHYTHM -- EXACT QUANTITATIVE BENCHMARKS (CRITICAL)

**Source:** `FERN_MOTION_FORMULA.json`, `FERN_EDITORIAL_PLAYBOOK.json`

**What the playbook has:** "documentary: 5-7 seconds per cut" -- a single generic range.

**What the analysis has that is MISSING:**

| Metric | Value | Source |
|--------|-------|--------|
| Cuts/min (3-video avg) | 11.3 cuts/min | FERN_MOTION_FORMULA |
| Avg segment duration | 5.33 sec | FERN_MOTION_FORMULA |
| Segment duration <1s | ~49% of segments | FERN_MOTION_FORMULA |
| Segment duration 1-3s | ~35% of segments | FERN_MOTION_FORMULA |
| Segment duration 3-6s | ~1.3% of segments | FERN_MOTION_FORMULA |
| Segment duration >6s | ~14.5% of segments | FERN_MOTION_FORMULA |
| Narrative-motivated cuts | 44% | FERN_EDITORIAL_PLAYBOOK |
| Visual freshness cuts | 56% | FERN_EDITORIAL_PLAYBOOK |
| Max same-image duration | 20 sec | FERN_EDITORIAL_PLAYBOOK |
| Typical image refresh | 8-12 sec | FERN_EDITORIAL_PLAYBOOK |
| Cut rate (editorial video) | 13.2 cuts/min | FERN_EDITORIAL_PLAYBOOK |

**Rhythm pattern NOT in playbook:**
- Long hold (8-20 sec) on document_photo with slow_zoom_in -> rapid burst (2-4 sec) of archival/news clips -> repeat
- Cycle: "10-20s hold -> 2-4s burst -> 10-20s hold -> 2-4s burst"

**WaTop comparison data NOT in playbook:**
- WaTop avg cut frequency: 6.5 sec/shot (from `analysis_videos_1_3.json`)
- WaTop cuts/min: 17.7 (from `complete_analysis.json`, highest performing)
- WaTop intro pacing: 5 sec/shot
- WaTop explanation pacing: 7.5 sec/shot
- WaTop reveal pacing: 5.5 sec/shot

### Rules to add:
- The bimodal segment distribution: ~49% under 1s + ~14.5% over 6s = Fern uses rapid-fire montage bursts interleaved with long holds
- Two types of cuts: narrative-motivated (44%) vs. visual freshness (56%)
- Never hold the same image for more than 20 seconds
- Refresh visual every 8-12 seconds during same narrative beat

---

## GAP 3: MOTION / KEN BURNS -- EXACT RATES AND NARRATIVE MAPPING (HIGH)

**Source:** `FERN_MOTION_FORMULA.json`, `FERN_EDITORIAL_PLAYBOOK.json`

**What the playbook has:** "Slowly change scale (Ken Burns zoom)" -- no numbers.

**What the analysis has that is MISSING:**

| Metric | Value |
|--------|-------|
| Zoom in % of all motion | 36.5% |
| Zoom out % | 23.7% |
| Static % | 20.0% |
| Pan % (up/down/left/right) | ~15% |
| Avg zoom-in rate | 5.46 %/sec |
| Avg zoom-out rate | 5.02 %/sec |
| Overall avg zoom rate | 5.36 %/sec |
| Interpretation | "aggressive_motion (5-10%/s -- high energy)" |
| Beat sync % | 39.1% of cuts sync to music beat |
| Avg beat offset | 126.8ms |

**Zoom speed by narrative intensity (from EDITORIAL_PLAYBOOK):**

| Narrative Moment | Zoom Rate (%/sec) |
|-----------------|-------------------|
| Normal context (exposition) | 1.0-3.0 |
| Building tension | 3.0-5.0 |
| Emotional peak / reveal | 5.0-9.0 |
| Extreme revelation (1-2 per video) | 15.0-25.0 |
| Zoom out: scope reveal | 1.0-3.0 |
| Zoom out: emotional exhale | 3.0-8.0 |
| Zoom out: scale shock | 5.0-10.0 |

**Pan types (from EDITORIAL_PLAYBOOK):**

| Pan Direction | % of Motion | When |
|--------------|-------------|------|
| pan_right | 1.8% | Scanning/reading document left-to-right |
| pan_left | 1.8% | Going back in time |
| pan_up | 4.8% | Reading down a document |
| pan_down | 4.3% | Scrolling protest signs, newspaper columns |

### Rules to add to `editing.json`:
- Default Ken Burns zoom rate: 5.4%/sec (NOT the gentle 1-2%/sec that feels "safe")
- Zoom speed is an emotional signal -- map to narrative intensity
- ~39% of cuts should align to music beats (within ~127ms)
- Pan direction communicates temporal direction (right = forward, left = backward)

---

## GAP 4: TEXT/CAPTION PATTERNS -- ANIMATION, ZONE, HOLD DURATION (HIGH)

**Source:** `FERN_TEXT_ANIMATION_FORMULA.json`, `FERN_STYLE_GROUND_TRUTH.json`, `FERN_EDITORIAL_PLAYBOOK.json`

**What the playbook has:** "Only for emphasis, 3 words or less at a time" -- generic.

**What the analysis has that is MISSING:**

| Metric | Value |
|--------|-------|
| Dominant text appear animation | slide_reveal (76% of events) |
| Secondary: already_visible | 12% |
| Secondary: fade_in | 12% |
| Avg fade-in duration | 511ms |
| Dominant text zone | upper (48%) |
| Center zone | 28% |
| Lower zone | 24% |
| Avg text hold duration | 8.36 sec |
| Min hold | 0.5 sec |
| Max hold | 159.64 sec |
| Text color | White dominant (~85%), Yellow (~10%), Red (<1%) |
| Font weight | extra_bold (avg stroke width 9-10px) |
| Text on solid dark background | Only 1.7% of text frames -- almost never |

**Text overlay types from EDITORIAL_PLAYBOOK:**

| Type | Format | When |
|------|--------|------|
| Source citation | [number] | Every 30-60s during evidence-heavy sections |
| Person identification | FULL NAME in caps | First mention of a person |
| Entity label | Name in caps | Introducing organization/concept |
| Location label | Place name | Setting a scene geographically |
| Quote | Typewriter effect | Reading subject's own words |
| In-frame text | Natural | Text in source material matches narration |

### Rules to add:
- Use slide_reveal animation (not instant pop-in) at ~500ms
- Place text primarily in upper zone (48%), then center (28%), then lower (24%)
- Hold text on screen for ~8 seconds average
- Text is ALWAYS overlaid on photos, not on solid dark backgrounds
- Font: extra_bold condensed sans-serif, white
- Different text types have specific formats and triggers (source citation, person ID, entity label, location, quote)

---

## GAP 5: COLOR GRADING FORMULA (HIGH)

**Source:** `COLOR_GRADE_FORMULA.json`, `FERN_MOTION_FORMULA.json`, `FERN_STYLE_GROUND_TRUTH.json`

**What the playbook has:** "Color grading consistent with mood" -- no specifics.

**What the analysis has that is MISSING:**

**Grand average color values (across 3 Fern videos):**

| Metric | Value |
|--------|-------|
| R mean | 97.07 |
| G mean | 93.07 |
| B mean | 90.22 |
| Luminance mean | 93.72 |
| Saturation | 0.38 |
| Contrast (std dev) | 42.63 |
| Shadow mean | 36.76 |
| Highlight mean | 169.96 |

**FFmpeg filter for Fern look:**
```
eq=contrast=0.78:brightness=-0.064:saturation=1.09
b_channel_shift: -0.011
r_channel_shift: 0.016
```

**Production-spec color grade (from MOTION_FORMULA):**

| Metric | Value |
|--------|-------|
| Saturation | 0.244 |
| Brightness | 0.368 |
| Contrast | 0.188 |
| Black crush % | 24.7% |
| Highlight clip % | 5.2% |

**Key insight:** Fern's look is DARK (avg luminance 93.72 out of 255), slightly warm (R > G > B), moderately desaturated, with heavy black crush (24.7% of image is crushed shadows) and minimal highlight clipping.

### Rules to add:
- Target luminance: ~94/255 (dark)
- Slight warm shift: R +0.016, B -0.011
- Black crush: 24.7% of image in deep shadows
- Highlight clip: only 5.2%
- Saturation: 0.244 (desaturated)
- FFmpeg formula for automated grading

---

## GAP 6: CHAPTER TRANSITION FORMULA (HIGH)

**Source:** `FERN_EDITORIAL_PLAYBOOK.json`

**What the playbook has:** "full_screen_transitions" with types listed. No structure.

**What the analysis has -- a precise 5-step transition formula:**

1. **Concluding punch** (2-4 sec): Last sentence is punchy, emotionally loaded
2. **Dramatic silence** (2-5 sec): Narration stops, music continues/swells
3. **Music bridge** (10-30 sec): Music fills gap, signals "new chapter coming"
   - Major transitions: 20-40 sec music breaks
   - Minor transitions: 5-10 sec
4. **Chapter card** (2-4 sec): White serif text on dark background
5. **New hook**: Fresh compelling line/image that resets audience attention

**Transition type distribution (from STYLE_GROUND_TRUTH):**

| Type | Count |
|------|-------|
| hard_cut | 105 (dominant) |
| fade_to_black | 12 |
| fade_to_white | 3 |

### Rules to add:
- The 5-step chapter transition sequence
- Music bridge duration varies by transition importance
- Chapter card style: white serif typewriter text on dark background
- Hard cut for within-chapter transitions (90%+)
- Fade to black only for chapter boundaries

---

## GAP 7: MUSIC STRATEGY -- BPM, ROLE, SWELL/DROP TIMING (HIGH)

**Source:** `FERN_EDITORIAL_PLAYBOOK.json`, `FERN_FORMULA_SOP.md`, per-video audio analyses

**What the playbook has:** Generic mood-matching, segment assignment, abrupt pause. No specific parameters.

**What the analysis has that is MISSING:**

| Metric | Value |
|--------|-------|
| Music BPM (Fern) | 123 BPM |
| Music style | "dark cinematic, piano + strings" |
| Music role | Continuous underscore, louder during silence/transitions, ducked under narration |
| Music swells | At chapter transitions and before dramatic pauses |
| Music drops | Near-silence for most intimate/shocking revelations |
| Dramatic pause frequency | 3-5 per chapter (every 2-3 min) |
| Dramatic pause duration | 1-3 sec |
| WaTop BPM | ~112 BPM |

**Dramatic pause triggers:**
- After delivering a shocking fact
- Before introducing a new character or era
- At end of a rhetorical question
- Before a chapter transition

### Rules to add:
- Target BPM: 123 (dark cinematic)
- Music is ALWAYS playing (continuous underscore)
- Duck music under narration, raise during transitions/silence
- 3-5 dramatic pauses per chapter, each 1-3 sec
- Specific triggers for when music should swell vs drop

---

## GAP 8: INTRO FORMULA -- FERN-SPECIFIC OPENING HOOK (MEDIUM)

**Source:** `FERN_EDITORIAL_PLAYBOOK.json`, `FERN_FORMULA_SOP.md`, `SCRIPT_STRUCTURE_FORMULA.json`

**What the playbook has:** Generic intro windows (0-3s, 3-5s, 5-10s, 10-15s) from LearnByLeo. No Fern-specific formula.

**What the analysis has that is MISSING:**

**Fern's opening hook formula:**
- Technique: Subject's own words displayed as typewriter text on dark background, read by narrator in ominous tone
- Motion: slow_zoom_in at 3-5%/sec
- Duration: 8-15 sec
- Tone: ominous

**Fern's hook types (from 30 videos):**
- Superlative Opener: 5 uses
- Mystery Opener: 4 uses
- Direct Address: 2 uses
- Year Anchor: 1 use

**Hook opening styles:**
- Opens with quote: 2 of 3 analyzed videos
- Opens with location: 1 of 3
- Opens with date: 0 of 3

**WaTop hook types:**
- aerial_location (best: 1.1M views)
- macro_shock
- aerial_scale

### Rules to add to `intros.json`:
- Fern-specific opening: typewriter quote on dark background with 3-5%/s zoom-in, 8-15 sec
- Top hook type: subject's own words (quote opening)
- WaTop-specific: aerial location establishing shot

---

## GAP 9: NARRATIVE FUNCTION -> VISUAL MAPPING (MEDIUM)

**Source:** `FERN_EDITORIAL_PLAYBOOK.json`, `FERN_CORRELATION_DATA.json`

**Not in playbook at all.** The analysis maps every narrative function to specific visual choices:

| Narrative Function | % of Video | Visual Type | Motion | Cut Pattern |
|-------------------|-----------|-------------|--------|-------------|
| Establishing context | 59.6-63.7% | document_photo | slow zoom-in 1-3%/s | Every 8-12s |
| Tension build | 8.5-12.6% | document_photo | faster zoom-in 5-9%/s | 2-4s segments |
| Evidence | 10.4-14.5% | document_photo (88.7%) | zoom-in 1.5-5%/s | Cut TO evidence on reference |
| Character intro | 2.7-11.7% | documentary_photo (56.5%) | zoom-in to face 2-5%/s | Cut when name spoken |
| Hook | 3.4-3.8% | document_photo/title_card | slow zoom-in 3-5%/s | HOLD -- do not cut |
| Revelation | 0.2-0.3% | news_screenshot/document | extreme zoom 15-25%/s | Cut at exact narration moment |
| Transition | 1.4-2.0% | black_screen (86.1%) | none/slow zoom-out | Fade to black |

**Emotional tone distribution per narrative function (from CORRELATION_DATA):**
- Establishing context: neutral (33.6%), tense (29.9%), ominous (11.7%)
- Tension build: tense (88.8%), ominous (10.3%)
- Evidence: tense (47.8%), ominous (31.2%)
- Hook: ominous (45.9%), mysterious (21.3%)

### Rules to add:
- A complete narrative-function-to-visual-choice mapping table
- Emotional tone targets per narrative function
- This should be a new section in `editing.json` or a standalone file

---

## GAP 10: THUMBNAIL FORMULA -- COMPLETE FERN THUMBNAIL SYSTEM (MEDIUM)

**Source:** `THUMBNAIL_FORMULA.json`

**What the playbook has:** 26 generic clickbait tactics. No channel-specific thumbnail rules.

**What the analysis has that is MISSING:**

**Background:** Pure black or dark desaturated grey -- ALWAYS
**Text overlay:** 1-3 words MAX, the most extreme single fact, NOT a repeat of the title
**Font:** Heavy condensed bold sans-serif (Impact or equivalent)
**Color:** RED accent in 9/11 analyzed thumbnails, secondary: YELLOW for positive labels

**Text styles:**
1. White text in red filled rectangle (~60%)
2. White bold text with black outline (archival/CCTV)
3. Yellow bold text with black outline (positive reveals)

**Subject types:**
- person_face_closeup: desaturated + red tint, eye contact at viewer
- cgi_3d_object: photorealistic but synthetic, red color treatment
- composite_scene: multiple cutouts on dark background showing the twist
- archival_footage: heavy grain, scanlines, "leaked footage" feel

**Arrow/callout:** ~50% of thumbnails, bold red arrow pointing to key subject

**Composition:** Never more than 2 elements competing. Subject slightly left of center. Low angle or straight-on.

**Text word bank:**
- Status: DEAD, CAPTURED, EXPOSED, DISAPPEARED, ARRESTED
- Roles: FBI, CIA, KKK, MOLE, SPY, TRAITOR
- Quality: GENIUS, EVIL, INSANE, DUMB, BRILLIANT
- Action: HACKED, STOLEN, KILLED, LEAKED, BANNED
- Mystery: SECRET, HIDDEN, CLASSIFIED, CENSORED, UNKNOWN
- Fragments: "IT'S THEM.", "NO WINDOWS.", "WORSE THAN HITLER?"

### Rules to add to `titles_thumbnails.json`:
- Complete Fern thumbnail system with background, color, composition rules
- The text word bank for automated thumbnail text generation
- Arrow/callout frequency and style
- Subject type classification with treatments

---

## GAP 11: TITLE ANGLE FORMULA -- VIEW-RANKED ANGLE TAXONOMY (MEDIUM)

**Source:** `TITLE_ANGLE_FORMULA.json`, `FERN_FORMULA.json`

**What the playbook has:** Generic title optimization rules. No angle taxonomy.

**What the analysis has that is MISSING:**

**Angle rankings by avg views:**

| Angle | Avg Views | Count |
|-------|-----------|-------|
| INSTITUTION_HOW | 11,223,342 | 1 |
| PERSON_GENIUS_TRAGEDY | 4,155,154 | 4 |
| THREAT_WHY | 3,294,900 | 3 |
| PLACE_HORROR | 3,164,850 | 6 |
| OTHER | 2,920,803 | 4 |
| VILLAIN_EXPOSED | 2,884,348 | 4 |
| POWER_MONEY | 2,662,005 | 2 |
| PROCESS_HOW | 2,555,597 | 5 |
| SECRET_REVEALED | 1,362,691 | 1 |

**Title pattern performance (from FERN_FORMULA):**

| Pattern | Avg Views | % of Videos |
|---------|-----------|-------------|
| person_reference | 7,020,854 | 10% |
| country_reference | 5,592,304 | 20% |
| colon_structure | 4,512,181 | 3% |
| the_most | 3,819,641 | 10% |
| superlative | 3,571,700 | 17% |
| negative | 3,546,013 | 13% |
| how_x | 3,462,360 | 27% |
| number | 3,241,337 | 13% |
| why_x | 3,208,223 | 13% |
| mystery_word | 3,047,905 | 13% |

**Optimal title specs:**
- Target: 6 words, 37 characters
- Range: 3-11 words

### Rules to add:
- The angle taxonomy with performance rankings
- Title pattern performance table
- High-performing title words (korea, north, the, most, how, why, secret)

---

## GAP 12: SCRIPT PACING -- QUANTITATIVE WPM AND STRUCTURE DATA (MEDIUM)

**Source:** `FERN_FORMULA.json`, `SCRIPT_STRUCTURE_FORMULA.json`, `FERN_FORMULA_SOP.md`

**What the playbook has:** Generic scripting principles. No quantitative benchmarks.

**What the analysis has that is MISSING:**

| Metric | Value |
|--------|-------|
| Avg WPM | 161 (range: 126-187) |
| Top 30% avg WPM | 168 |
| Bottom 30% avg WPM | 154 |
| Avg sentence length | 13 words |
| Short sentences (<=5 words) | 11-19% |
| Re-engagement hook frequency | 0.12/min (1 every ~8 min) |
| Top re-engagement type | sudden_change (31 uses) |
| Curiosity gap frequency | 0.43/min (12 per video) |
| Avg curiosity gap duration | 39.8 sec |
| Emotional density | 0.54% of all words |
| Dominant emotions | mystery (194), fear (137), power (100), tragedy (98) |
| Second-person density | 0.83% |
| Questions per 1000 words | 1.83 |
| Vocabulary richness | 0.381 |

**Top vs bottom performer differences:**
- Top 30% curiosity gaps: 0.49/min
- Bottom 30% curiosity gaps: 0.35/min
- (Curiosity gap density is the strongest differentiator)

**Video duration sweet spot:**
- Median: 24.5 min
- Average: 26.5 min
- Top performers avg: 26.7 min (+3.1 min vs bottom performers)

### Rules to add to `scripting.json`:
- Target WPM: 161 (top performers: 168)
- Sentence rhythm: avg 13 words, 11-19% short punchy sentences
- Curiosity gap density: 0.43/min target (top performers: 0.49/min)
- Re-engagement hooks: every ~8 minutes
- Emotional density: 0.54%
- Optimal duration: 24-27 minutes

---

## GAP 13: VISUAL CATEGORY SYSTEM WITH DURATIONS (MEDIUM)

**Source:** `FERN_EDITORIAL_PLAYBOOK.json`

**Not in playbook.** Complete visual category system with usage percentages and durations:

| Category | % of Video | Avg Duration | Sourcing |
|----------|-----------|-------------|----------|
| document_photo | 32.9% | 10.4 sec | Gov archives, Wikimedia, Internet Archive |
| archival_footage | 3.6% | 4.6 sec | AP Archive, Reuters, Internet Archive |
| news_screenshot | 1.3% | 4.7 sec | Newspaper archives, web screenshots |
| documentary_footage | 0.8% | 6.3 sec | Public domain documentaries |
| reconstructed_footage | 1.7% | 4.0 sec | Stock footage matching era/setting |
| title_card | 0.8% | 2.8 sec | White serif typewriter on dark |
| screen_recording | -- | 8.5 sec | Digital evidence, website content |

**WaTop visual composition (from watop_patterns.json):**

| Category | % |
|----------|---|
| aerial | 32.2% |
| documentary | 30.2% |
| cgi | 17.5% |
| graphics | 11.7% |
| macro | 10.2% |

### Rules to add:
- Complete visual category taxonomy with target percentages
- Duration guidelines per category
- Sourcing guidelines per category

---

## GAP 14: CAMERA ANGLE DISTRIBUTION (LOW)

**Source:** `VISUAL_FORMULA_HYBRID_qwen-vl.json`

| Camera Angle | Count |
|-------------|-------|
| close_up | 663 |
| wide | 370 |
| medium | 252 |
| eye_level | 95 |
| extreme_close_up | 90 |
| not_applicable | 69 |
| overhead | 47 |
| aerial | 39 |
| POV | 13 |
| static | 12 |
| dutch_angle | 4 |

### Rules to add:
- Close-up dominant (41%), then wide (23%), then medium (16%)

---

## GAP 15: ENGAGEMENT / RETENTION BENCHMARKS (LOW)

**Source:** `FERN_MASTER_FORMULA.json`

| Metric | Value |
|--------|-------|
| Like ratio | 2.95% |
| Comment ratio | 0.190% |
| Total engagement rate | 3.14% |
| Intro engagement | 0.25 |
| Mid engagement | 0.19 |
| End engagement | 0.11 |
| Mid-to-intro retention | 75% |
| End-to-intro retention | 43% |
| Upload frequency | Every 7 days |
| Best upload day | Sunday (47% of uploads) |
| Description avg length | 1,681 chars |
| Sponsor in description | 100% |
| Credits/sources | 100% |

---

## GAP 16: WATOP-SPECIFIC PATTERNS (LOW)

**Source:** `watop_patterns.json`, `analysis_videos_1_3.json`, `analysis/watop/complete_analysis.json`

Entirely absent from playbooks:

| Metric | Value |
|--------|-------|
| WaTop avg cut frequency | 6.5 sec/shot |
| WaTop cuts/min (top videos) | 17.7 |
| WaTop visual mix | 34.5% aerial, 20.5% CGI, 30.5% documentary |
| WaTop hook type (best) | aerial_location (1.1M views) |
| WaTop BPM | ~112 |
| WaTop focus (best) | engineering_technical |
| WaTop uses satellite imagery | 6.5% in top performer |
| CGI correlation | Higher CGI % correlates with higher views |

---

## GAP 17: PRODUCTION GUIDE PATTERNS (LOW)

**Source:** `production_guide_secret_scores.md`

This file contains a complete scene-by-scene production guide for a specific video that demonstrates applied rules. While not generalizable rules per se, it contains concrete energy-level-per-scene sequencing that could inform a new "energy pacing template":

- Scene 1 (cold open): Energy LOW, music drone, SFX subtle tension hit
- Scene 2 (escalation): Energy LOW to MEDIUM, impact hit on key phrase
- Scene 3 (silent threat): Quick cuts 2-3s each matching domains

This demonstrates the applied version of the energy variation principle that the playbook describes only abstractly.

---

## PRIORITY SUMMARY

### CRITICAL (should be added immediately)
1. **Sound design formula** -- exact SFX density, types, loudness ratios, timing offset
2. **Editing rhythm benchmarks** -- bimodal cut distribution, narrative vs. freshness cuts, hold/burst cycle

### HIGH (significant production impact)
3. **Motion/Ken Burns rates** -- exact zoom %/sec values mapped to narrative intensity
4. **Text/caption system** -- animation type, zone placement, hold duration, font spec
5. **Color grading formula** -- exact RGB values, FFmpeg filter, black crush %, saturation
6. **Chapter transition formula** -- 5-step sequence with timing
7. **Music strategy parameters** -- BPM, swell/drop triggers, dramatic pause frequency

### MEDIUM (improves specificity)
8. **Fern-specific intro formula** -- typewriter quote hook, 8-15 sec, 3-5%/s zoom
9. **Narrative function to visual mapping** -- complete lookup table
10. **Thumbnail formula** -- Fern's specific dark/red/minimal system
11. **Title angle taxonomy** -- angle rankings with avg views
12. **Script pacing benchmarks** -- WPM, sentence rhythm, curiosity gap density, emotional density
13. **Visual category system** -- percentages, durations, sourcing

### LOW (nice to have)
14. Camera angle distribution
15. Engagement/retention benchmarks
16. WaTop-specific patterns
17. Production guide energy templates
