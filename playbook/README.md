# YouTube Strategy Playbook

A structured, queryable knowledge base of proven YouTube growth strategies extracted from top creators. Designed to sit **above** the production pipeline and inform every stage — from ideation to final edit.

## Architecture

```
playbook/
├── README.md                  # This file
├── index.json                 # Master index — maps pipeline stages to playbook modules
├── ideation.json              # Topic selection, audience research, outlier transfer
├── scripting.json             # Script structure, retention patterns, pacing
├── titles_thumbnails.json     # Click tactics, title formulas, thumbnail design
├── intros.json                # Hook strategies, expectation alignment, pacing
├── editing.json               # Visual variety, continuity, sound design, pacing
├── retention_delivery.json    # Camera presence, storytelling, communication, clarity
└── sources.json               # Attribution — which creator taught what
```

## How It Works

Each playbook module is a JSON file containing:
- **principles**: Core rules (always apply)
- **tactics**: Specific techniques with examples
- **checklists**: Scoring criteria for QA gates
- **anti_patterns**: What to avoid

## Pipeline Integration

Each pipeline module can query the playbook at runtime:
- `topic_radar.py` → `ideation.json` (is this idea broad enough? does it pass the 4 tests?)
- `script_enhancer.py` → `scripting.json` (green/purple structure, water tank pacing)
- `director.py` → `editing.json` (visual variety rules, sound design layers)
- `video_assembler.py` → `editing.json` (cut frequency, energy variation, continuity)
- `check_fern_script.py` → `scripting.json` + `intros.json` (score against playbook criteria)
- Title/thumbnail generation → `titles_thumbnails.json` (26-tactic checklist)

## Extensibility

Add more creators by:
1. Download their content (yt-dlp)
2. Extract transcripts
3. Analyze and merge insights into existing modules
4. Update `sources.json` with attribution

Currently sourced from: **LearnByLeo** (7 videos, March 2026)
