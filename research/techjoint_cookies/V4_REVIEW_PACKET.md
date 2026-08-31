# Cookies v4 — Ear-Check Packet (build step 2, delivered 2026-08-31)

**Watch copy:** `~/Movies/TechJoint_Cookies_v4_preview_watch.mp4` (3:15, 540p preview)
**One question:** does the generated foley survive your ear at mix level? Verdicts below close the oldest open loop (v4 delivered 2026-08-20).

## What v4 is (commit 224ec8b)
Generated-foley rebuild after you rejected v3's SFX: two backwards clips fixed (C33 money shot, C29 tray-out), the hand-placed library-SFX layer retired entirely, and MMAudio video-to-foley generated per exact shot window instead. Mix rebuilt to the measured spec of 5 viral hands-only references: foley foreground ~5–10dB under VO, 42 contact onsets/min (refs: 30–50; v3 was ~8), zero stingers, music muted in hook + reveal, room-tone floor. VO verified whisper-intact; reveal line lands AFTER the tear.

## Gate summary (`venv/bin/python run_gates.py foley`, fail-closed)
**15 OK · 26 HISSY · 5 UNSYNCED** of 46 tracks. HISSY/UNSYNCED are now hard-fails (S7 rev), so v4 CANNOT ship without a per-defect verdict from you — that is this packet. Context that matters: HISSY = the isolated track's spectral flatness is high at low peak (mostly quiet room-tone beds); the mix used capped-gain leveling precisely so these never get loudnormed into audible hiss. UNSYNCED = no generated onset lands within the motion window. **So listen for: (a) audible hiss/noise-floor swell at normal volume, (b) sounds that miss or contradict the on-screen action.**

## Pre-declared waiver candidates — 31 tracks, in watch order

| Timecode | Track | Flag | Machine data | On screen |
|---|---|---|---|---|
| 0:00–0:02 | H1 | HISSY | flat 0.69, peak −35dB | pulling apart gooey cookie |
| 0:02–0:04 | H2 | UNSYNCED | 0/1 onsets synced | turning broken cookie wedge |
| 0:06–0:08 | H4 | HISSY | flat 0.48, peak −39dB | tilting chocolate chunk cookie |
| 0:08–0:11 | H5 | HISSY | flat 0.54, peak −23dB | beauty hold on stack |
| 0:11–0:13 | H6 | HISSY | flat 0.62, peak −34dB | sprinkling sea salt |
| 0:23–0:28 | C03 | HISSY | flat 0.78, peak −22dB | butter cubes set down |
| 0:33–0:38 | C05 | HISSY | flat 0.78, peak −24dB | butter melting/foaming in pan |
| 0:38–0:44 | C06 | HISSY | flat 0.55, peak −24dB | brown sugar + butter close-up |
| 0:44–0:49 | C07 | HISSY | flat 0.74, peak −21dB | brown butter pouring |
| 0:54–0:56 | G1 | UNSYNCED | 0/2 onsets synced | cookie pull-apart (gfx) |
| 0:56–1:01 | C09 | UNSYNCED | 0/5 onsets synced | brown butter stream |
| 1:06–1:10 | C11 | UNSYNCED | 0/1 onsets synced | eggshell splitting |
| 1:13–1:19 | C13 | HISSY | flat 0.76, peak −26dB | batter ribboning off whisk |
| 1:19–1:23 | C14 | HISSY | flat 0.66, peak −34dB | flour poured |
| 1:23–1:27 | C15 | HISSY | flat 0.46, peak −19dB | spoon of baking soda |
| 1:33–1:37 | C17 | HISSY | flat 0.62, peak −28dB | spatula smearing |
| 1:42–1:46 | C19 | HISSY | flat 0.71, peak −27dB | chocolate chips pouring |
| 1:46–1:51 | C20 | HISSY | flat 0.59, peak −27dB | dough folded |
| 1:51–1:55 | C21 | HISSY | flat 0.72, peak −26dB | dough mound settling |
| 1:55–1:57 | G2 | HISSY | flat 0.67, peak −22dB | beauty hold (gfx) |
| 1:57–2:02 | C22 | HISSY | flat 0.65, peak −35dB | cookie scoop pressing |
| 2:02–2:07 | C23 | HISSY | flat 0.59, peak −32dB | chunk pressed into dough |
| 2:11–2:14 | C25 | HISSY | flat 0.62, peak −49dB | still overhead, fingertips |
| 2:14–2:18 | C26 | UNSYNCED | 0/1 onsets synced | oven knob turned |
| 2:22–2:29 | C28 | HISSY | flat 0.50, peak −18dB | cookies baking in oven |
| 2:36–2:39 | C31 | HISSY | flat 0.71, peak −27dB | sea salt sprinkle |
| 2:39–2:43 | C32 | HISSY | flat 0.52, peak −44dB | still tray of cookies |
| 2:46–2:49 | C38 | HISSY | flat 0.55, peak −25dB | cookie rotated to camera |
| 2:55–2:59 | C34 | HISSY | flat 0.73, peak −33dB | broken wedge turned |
| 2:59–3:03 | C35 | HISSY | flat 0.68, peak −26dB | beauty hold on stack |
| 3:03–3:15 | C36 | HISSY | flat 0.57, peak −19dB | cookies cooling on rack |

## Recording your verdict
Per defect (or per group — "all HISSY beds inaudible → WAIVE" is a valid one-liner):
- **WAIVE** — inaudible/acceptable at mix level; ships with a logged waiver (lane, id, reason, date) that resurfaces at review + post-publish read.
- **REGEN** — goes on the v5 list (MMAudio re-roll of that shot window).
- **MUTE** — drop the track; room-tone floor covers it.

Verdicts land in `research/techjoint_cookies/v4_verdict_ledger.json` (31 PENDING slots waiting) — tell any session your calls and it records them; SHIP requires zero PENDING. Overall call is also recorded there: **SHIP (1080p master next) or v5 list**.
