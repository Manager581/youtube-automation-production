# Mine Site Proposal Visuals

Concept visual package for Sarah's Source Atlantic RFP response (Sudbury mine
sites): turns her site-walk sketch into proposal-grade facility visuals.

## What's here

| Path | What it is |
|---|---|
| `build_page.py` | Generates both SVG sheets and the artifact page from the layout geometry |
| `dry-facility-visuals.html` | Published artifact page (SK-01 floor plan + SK-02 isometric + CI projects) |
| `floorplan.svg` / `isometric.svg` | Standalone copies of the two sheets |
| `exports/` | High-res PNGs of both sheets, ready to text/embed |
| `pipeline/generate_renders.py` | Photoreal render pipeline (Gemini or OpenAI image APIs) |
| `pipeline/site_config.json` | Per-site facility description — copy per site for the other 10 |
| `pipeline/inputs/` | Floor plan + reference photos that ground the renders |
| `renders/` | Output directory for photoreal shots |

## Regenerate the sheets

```
python3 build_page.py
```

Layout geometry (feet) lives at the top of `build_page.py`; it was scaled off
the 7-ft hallway dimension on Sarah's plan (footprint ≈ 48 × 42 ft).

## Photoreal renders

**No API key? Use ChatGPT directly** — generate the copy-paste kit:

```
cd pipeline
python3 generate_renders.py --chatgpt-kit   # writes chatgpt-prompts.md
```

For each shot in `chatgpt-prompts.md`, attach the listed images from
`pipeline/inputs/` in ChatGPT, paste the prompt, and iterate in the same chat.

With an API key the same prompts run automatically:

```
python3 generate_renders.py --dry-run     # preview prompts
GEMINI_API_KEY=... python3 generate_renders.py            # all 5 shots
GEMINI_API_KEY=... python3 generate_renders.py --shot entrance
```

Shots: `overview`, `entrance`, `hallway`, `innovation-hub`, `micro-market`.

## Scaling to the other 10 sites

Copy `site_config.json` per site, adjust the layout bullets and innovations
(2 CI projects per site), swap the inputs, and rerun. For new sheet drawings,
adjust the geometry block in `build_page.py`.
