# Per-video review brief (competitor teardown — chocolate chip cookie videos)

You are annotating ONE YouTube video at a time from its contact sheets + transcript + measured
forensics. The goal is a forensic, timestamped description of HOW the video is built — not a summary
of the recipe. Write what you can literally SEE / READ; tag anything inferred as `(inferred)`; write
`not visible` rather than guessing. Every claim about timing cites the timestamp label printed on the
sheet tiles (bottom-right of each tile, HH:MM:SS) or the forensics JSON.

## Inputs per video (all paths relative to repo root)
- `research/techjoint_cookies/competitors/sheets/<id>_grid*.jpg` — dense grid: 1 frame every
  `grid_step` s (1 s for ≤90 s videos, 2 s ≤240 s, 3 s longer), possibly split in pages grid1/grid2/grid3.
- `research/techjoint_cookies/competitors/sheets/<id>_hook.jpg` — first 6 s at 2 fps (12 tiles).
- `research/techjoint_cookies/competitors/sheets/<id>_cuts.jpg` — one frame 0.3 s after each detected
  HARD cut, labelled `<n> @<t>s` (t=0 first). Dissolves/soft transitions are NOT detected — estimate
  those from the grid.
- `research/techjoint_cookies/competitors/thumbs/<id>.jpg` (long set) or
  `footage/techjoint_competitors.nosync/short/<id>.jpg` (shorts) — the YouTube thumbnail.
- `research/techjoint_cookies/competitors/transcripts/<id>.txt` — whisperx transcript with
  [start-end] per segment (empty file = no speech detected).
- `research/techjoint_cookies/competitors/forensics/<id>.json` — `cuts` (s), `shots` (s,e,dur,text),
  `onsets` (audio transient times), `env` (0.5 s RMS grid: rms, rms_h harmonic≈music/voice tone,
  rms_p percussive≈transients/SFX).
- `research/techjoint_cookies/competitors/catalog.json` — metadata row (title, channel, subs, views,
  likes, upload, dur, tags, description head, desc signals, m_* = measured metrics).
- `footage/techjoint_competitors.nosync/<set>/<id>.info.json` — full yt-dlp metadata if you need more.
  You may also run `ffmpeg` to pull any extra frame you need (e.g. a full-res frame at a timestamp):
  `ffmpeg -y -loglevel error -ss <t> -i footage/techjoint_competitors.nosync/<set>/<id>.mp4 -frames:v 1 -q:v 3 /tmp/x.jpg`
  and Read it. Do this for the first frame and the money-shot/reveal at minimum.

## Output: write `research/techjoint_cookies/competitors/cards/<id>.md` with EXACTLY these sections

```
# <id> — <title>
**Channel** <channel> (<subs> subs) · **Views** <views> · **Uploaded** <yyyy-mm-dd> · **Length** <m:ss> · **Format** <landscape|vertical WxH> · **Type** <recipe walkthrough | experiment/"what if" | taste test/ranking | vlog-with-recipe | hack/tip | ad/brand>

## 1. Frame 1 + hook (0–3 s, then 3–10 s)
- t=0.0: <what is literally on screen: subject, framing (macro/CU/MS/overhead), text overlay verbatim, motion>
- first audio: <VO words verbatim (with t) | music only (genre/feel) | ASMR/sfx | silence> ; first spoken word at <t>
- when do the FINISHED cookies first appear? <t> (and how: pull-apart / stack / bite / tray)
- promise/curiosity device in the hook: <what makes you keep watching, stated plainly>
- 3–10 s: <what follows, shot by shot with t>

## 2. Person / voice / brand
- on camera? <face shown | hands only | never> ; who (inferred): <age/sex/energy>; hands visible? nails/rings/sleeves?
- voice: <none | VO | on-camera sync | TTS> ; delivery <instructional | banter | ASMR whisper | hype> ; coverage <m_talk_pct>% @ <m_wpm> wpm ; longest silence <m_max_pause> s
- captions/text: <style: font/colour/position/case; burned-in subtitles? ingredient callouts? step labels?> ; how many text events (count from grid) and when
- brand marks: <logo/watermark/channel name on screen? recurring props/colour palette/kitchen look/intro-outro card?>

## 3. Structure (beat timeline)
Table: | t_start | t_end | beat | what's on screen | audio | text |
Cover: hook → (ingredients?) → process steps → bake → reveal/money shot → payoff/taste → CTA/end.
Then: reveal/money shot timing = <t> (as % of runtime) and hold length; how many "goods" moments total.

## 4. Camera + look
- setups: <locked-off overhead | 45° tripod | handheld phone | slider/gimbal | mixed> ; number of distinct camera positions (count)
- framing mix: % macro/CU vs MS vs wide (estimate from grid) ; lighting <bright/natural/moody/studio> ; colour <warm/neutral/desaturated/high-contrast> ; iPhone-real vs produced look
- speed: slow-mo? time-lapse? speed ramps? (where, t)

## 5. Editing
- hard cuts <m_cuts> in <dur> s (median shot <m_median_shot> s; first cut <m_first_cut> s; longest hold <m_longest_hold> s) ; estimated soft/dissolve changes from the grid: <n>
- rhythm description: where it is fastest / slowest (t ranges) ; any pattern (cut-on-action, cut-on-word, jump cuts, whip pans, zoom punch-ins, match cuts)
- transitions: <hard | dissolve | speed-ramp | none>

## 6. Audio
- music: <none | bed: genre/tempo/feel> ; constant or ducked? ; lifts where?
- SFX/ASMR: <what sounds you can infer are foregrounded: sizzle, crack, whisk, paper…> ; measured onsets <m_onsets> (<m_onsets_per_min>/min) ; cuts landing on an onset <m_cuts_on_onset_pct>%
- narration-vs-visual relationship: <narration leads, visuals illustrate | visuals lead, text explains | pure ASMR>

## 7. Packaging
- title: <verbatim> → pattern <e.g. "The Best X", "X hack", question, claim, emoji>
- thumbnail: <what it shows: product fill %, face?, text verbatim, colours, style>
- description: <recipe in desc? links (count)? affiliate? socials? CTA?> ; tags <n>
- like rate <like_rate_pct>% ; comments/10k <comment_per_10k> (if present)

## 8. What's distinctive (3–6 bullets, each with a timestamp) — the tricks that make THIS video work
## 9. Implications for a hands-only, ultra-real, crispy-outside/gooey-inside cookie video (3 bullets)
```

Rules: ≤ 700 words per card. Timestamps everywhere. Quote on-screen text verbatim where legible. If a
sheet is unreadable at some spot, pull the full-res frame with ffmpeg before writing `not visible`.
Do not speculate about views/why-it-won — describe construction; the synthesis happens elsewhere.
