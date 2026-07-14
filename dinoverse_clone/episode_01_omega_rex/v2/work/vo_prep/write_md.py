#!/usr/bin/env python
"""Render VO_SCRIPT_LUKE_REVOICE.md FROM vo_manifest_v2.json.

The paste blocks are written from the manifest's paste_text, so the .md and the .json
cannot drift. verify_revoice.py then re-reads BOTH files off disk and re-hashes.
"""
import hashlib
import json

BASE = ("/Users/jefflawrence/Documents/youtube-automation-production/"
        "dinoverse_clone/episode_01_omega_rex/v2/work/vo_prep")
m = json.load(open(f"{BASE}/vo_manifest_v2.json", encoding="utf-8"))
P = {p["pass_id"]: p for p in m["generation_passes"]}
L = {(l["shot"], l["speaker"], l["slot"]): l for l in m["lines"]}
by_shot_spk = {}
for l in m["lines"]:
    by_shot_spk.setdefault((l["shot"], l["speaker"]), []).append(l)

o = []
w = o.append

w("# VO SCRIPT — LUKE RE-VOICE / LOCKED")
w("**Episode:** Dinoverse clone — episode_01 \"Omega Rex\"  ")
w("**Machine-readable twin:** `vo_manifest_v2.json` (same dir) — holds every SHA-256.  ")
w("**Extends:** `VO_SCRIPT_FINAL.md` / `vo_manifest.json` (cold open + S89). Those two passes are "
  "reproduced here **byte-identical**, same SHAs — they were rebuilt from the TSV by this "
  "build and asserted equal to the locked v1. Nothing about them changed.")
w("")
w("**Rule:** ONE generation per pass, **no re-rolls** (memory `elevenlabs-one-pass-rule`).  ")
w("**Model:** Eleven Multilingual v2 — honours `<break time=\"3.0s\" />`, so several lines "
  "ride in one generation and get split at the silences afterward.")
w("")
w("> LOCKED. The pre-Generate SHA check is the last chance to change anything.")
w("")
w("---")
w("")
w("## 0. The decision (settled — this doc implements it)")
w("")
w("Grok gave Luke **a different voice in nearly every clip** — F0 128–392 Hz across 27 clips, "
  "changing mid-scene (`voice_drift_census.json`). So:")
w("")
w("- **Luke is RE-VOICED** across his off-camera body dialogue. **26 body lines.**")
w("- **GF is NOT re-voiced in the body** — she is on camera in ~16 clips, dubbing would break "
  "lip-sync. She keeps **only her 3** cold-open/end-card lines.")
w("- Plus the **cold open + S89 end card** (the original Task B, unchanged).")
w("- Plus a clean **RANGER** VO for **S46** to restore the missing \"that's a Utahraptor\" payoff.")
w("")
w("### What is EXCLUDED, and why")
w("")
w("| Shot | Speaker | Why excluded |")
w("|---|---|---|")
for e in m["excluded_on_camera"]:
    w(f"| **{e['shot']}** | {e['speaker']} | **LUKE IS ON CAMERA** (selfie two-shot) — dubbing "
      f"breaks lip-sync. Verified: `{e['verified']}` |")
w("| **25 two-speaker rows** | LUKE / GF, GF / LUKE, CLERK / LUKE, RANGER / LUKE | See §9 — "
  "**all excluded by default**, one opted back in (S46). |")
w("")
w("---")
w("")
w("## 1. Typography normalizations (the ONLY changes from the TSV text)")
w("")
for n in m["typography_normalizations"]:
    w(f"- `{n}`")
w("")
w("Every line where a normalization fired:")
w("")
w("| Shot | Speaker | TSV | Locked text |")
w("|---|---|---|---|")
for l in m["lines"]:
    if l["normalizations_applied"]:
        w(f"| {l['shot']} | {l['speaker']} | `{l['tsv_verbatim']}` | `{l['exact_text']}` |")
w("")
w("**Nothing else changed.** No paraphrase, no \"improvement\", no bracketed stage directions "
  "(v2 reads those out loud). Apostrophes stay **ASCII** — a smart quote changes the bytes and "
  "breaks the SHA check.")
w("")
w("Two verbatim quirks kept on purpose:")
w("")
w("- **S32** is `'Aquatic Life Enclosure.'` — Luke is reading a sign, the inner single quotes "
  "are in the TSV. TTS does not vocalise quote marks.")
w("- **S59** is `Okay, NOW food.` — the caps are the scripted emphasis; v2 honours caps.")
w("")
w("---")
w("")


def block(pid, title, extra=""):
    p = P[pid]
    w(f"## {title}")
    w("")
    w(f"**SHA-256 of the paste text:** `{p['sha256_paste_text']}`  ")
    w(f"**Save the download as:** `{p['source_mp3']}`  ")
    w(f"**{p['n_lines']} line(s), {p['char_count']} chars — expect "
      f"{p['expected_segments_after_silence_split'] - 1} silence(s) on the split.**")
    if p["note"]:
        w("")
        w(f"> {p['note']}")
    if extra:
        w("")
        w(extra)
    w("")
    w("```")
    w(p["paste_text"])
    w("```")
    w("")
    w("| # | Shot | Line | → WAV |")
    w("|---|---|---|---|")
    for i, wav in enumerate(p["segment_order"], 1):
        ln = next(l for l in m["lines"] if l["wav"] == wav and l["speaker"] == p["speaker"])
        w(f"| {i} | {ln['shot']} | {ln['exact_text']} | `{ln['target_wav']}` |")
    w("")
    w("---")
    w("")


block("PASS_LUKE_BODY", "2. PASS_LUKE_BODY — LUKE, 23 calm body lines",
      "This is the pass that fixes the episode.")
block("PASS_LUKE_SHOUT", "3. PASS_LUKE_SHOUT — LUKE, 3 shouted body lines",
      "⚠️ **Risk R1 — read this before generating.** These 3 lines are script-shouted. "
      "A single flat TTS pass will very likely deliver them **conversationally**, not urgently, "
      "and the no-re-rolls rule means you are stuck with what comes out. They are carved into "
      "their own pass **precisely so you can dial the voice settings for them** "
      "(lower Stability, higher Style) without touching the calm body pass. "
      "The caps in `RUN. RUN—` are the scripted emphasis and v2 does respond to caps — but "
      "**set expectations: this is the single most likely thing in the whole job to disappoint.** "
      "If the take is flat, the honest fallback is to keep Grok's original shouted audio for "
      "these 3 shots and accept a voice change on ~5s of a 8:45 episode.")
block("PASS_LUKE_COLDOPEN", "4. PASS_LUKE_COLDOPEN — LUKE, 4 lines (UNCHANGED from v1)")
block("PASS_GF", "5. PASS_GF — GF, 3 lines (UNCHANGED from v1)")
block("PASS_RANGER", "6. PASS_RANGER — RANGER, the S46 myth-bust",
      "See §8 — **S46 has a hard timing problem the owner must decide on before this ships.**")
block("PASS_LUKE_EXTRA", "7. PASS_LUKE_EXTRA — LUKE, 2 OPT-IN lines",
      "⚠️ **Neither of these matches the literal `Speaker == LUKE` filter, so they are NOT "
      "silently folded into the body pass.** Both are off-camera and both are **RECOMMENDED**. "
      "Isolated here so that approving or dropping them **does not touch any other SHA**.\n\n"
      "- **F1 — S88** — Speaker is `LUKE VO`, not `LUKE`. It is a pure VO over a wide showdown "
      "shot: **zero lip-sync risk, the safest line in the episode.** If you skip it, Luke's voice "
      "audibly changes *at the climax*, right after 26 dubbed lines. **Recommend YES.**\n"
      "- **F2 — S46 Luke punchline** — a two-speaker row, so it is excluded by the conservative "
      "default. BUT: the hosts are back-of-head/off-camera in S46, the RANGER half of that same "
      "clip is being dubbed anyway, and Luke's turn is at the END of the clip — cleanly separable "
      "in time. Grok never delivered this line at all (see §8). **Recommend YES.**")

w("## 8. ⚠️ S46 — the biggest finding. Read before generating.")
w("")
s46r = L[("S46", "RANGER", "S46 (1st)")]
w("The board gives S46 **13s**. **The clip actually in `rough_cut_v6` is 6.04s** — and Grok "
  "crushed the whole scripted exchange into it as word-salad. This is the measured transcript "
  "of what is in the cut today:")
w("")
w("> *\"Here's what the movies got wrong. The famous velociraptors, real as raptors the size of "
  "a turkey **will how actually drew was ever feared. That's easy like this guy with a "
  "rebrand.**\"*")
w("")
w("The \"**that's a Utahraptor**\" payoff — the entire point of the scene — **is not in the "
  "episode.** Luke's punchline got slurred into the ranger's voice. The clip is junk audio end "
  "to end.")
w("")
w("**The timing does not work and cannot be made to work by generating alone:**")
w("")
w("| | words | est. speech @2.6 wps | clip today |")
w("|---|---|---|---|")
w(f"| RANGER turn | {s46r['word_count']} | **{s46r['est_tts_speech_seconds']}s** | 6.04s |")
lp = L[("S46", "LUKE", "S46 (2nd)")]
w(f"| LUKE punchline | {lp['word_count']} | {lp['est_tts_speech_seconds']}s | (same clip) |")
w(f"| **total + a beat** | | **≈19s** | **6.04s** |")
w("")
w("**S46 must stretch from 6.04s to ≈19s** (hold on the raptor / the size-comparison board / "
  "cutaways while the VO plays), **or** the ranger line has to be cut down — which is a *script* "
  "change and therefore **the owner's call, not mine.** I did not paraphrase the line to make it "
  "fit. The text above is verbatim.")
w("")
w("---")
w("")
w("## 9. Two-speaker rows — analysed, and ALL excluded by default")
w("")
w("A two-speaker clip can only be half-dubbed if Luke is **off-camera** in it **AND** his speech "
  "is **separable in time**. GF is on camera in most of them and her lip-sync is the thing we are "
  "protecting. Per the brief: conservative, flag rather than include.")
w("")
w("| Shot | Speaker | Luke's words | Verdict |")
w("|---|---|---|---|")
TWO = [
    ("S13", "LUKE / GF", "Okay - we're back at Dino Zoo.",
     "**BLOCKED** — Luke ON CAMERA (selfie two-shot)."),
    ("S13b", "LUKE / GF (off-cam)", "It's got the best dinos on earth-",
     "Both off-camera; but Luke's half is a **set-up whose punchline is GF's overlapping "
     "interruption** — splitting it re-times her line. **Excluded.**"),
    ("S14", "CLERK / LUKE", "Any chance of a discount for repeat trauma?",
     "Luke off-camera (POV), but his line sits **between two CLERK turns** — dubbing it alone "
     "leaves the clerk in Grok's voice mid-exchange. **Excluded.**"),
    ("S15", "GF / LUKE", "Everyone's here for the new exhibit. The one they've been hyping.",
     "GF on camera a step ahead; Luke's turn is second and separable. **Excluded — borderline, "
     "flag for owner.**"),
    ("S16", "LUKE / GF", "...'Hybrid Enclosure - Staff Only.' ... / I'm just reading.",
     "**Three turns, Luke on both ends around GF's \"Luke. No.\"** Not cleanly separable. "
     "**Excluded.**"),
    ("S24", "LUKE / GF", "Okay THAT is huge. / ...oh no.",
     "Luke brackets GF's turn. **Excluded.**"),
    ("S30", "GF / LUKE", "Twenty, thirty years, they think. What do you think?",
     "Separable (Luke second). **Excluded — borderline, flag for owner.**"),
    ("S31", "GF / LUKE", "Later. Water first.", "Separable but tiny. **Excluded.**"),
    ("S38", "RANGER / LUKE", "No thank you.",
     "3 words after the ranger's PA line + a crowd gasp. **Excluded.**"),
    ("S41", "GF / LUKE", "...hey. Look.", "Separable. **Excluded — borderline.**"),
    ("S42", "LUKE / GF", "Those kids have been by that door twice now.",
     "Luke first, GF second. Separable. **Excluded — borderline, flag for owner.**"),
    ("S46", "RANGER / LUKE", "So every raptor you've ever feared... was basically this guy...",
     "**PASS_LUKE_EXTRA (opt-in)** — hosts off-camera, Luke's turn is last, and the RANGER half "
     "is being dubbed anyway. See F2."),
    ("S49", "GF / LUKE", "It's definitely looking at you.", "Separable. **Excluded — borderline.**"),
    ("S55", "GF / LUKE", "Biggest animal to ever walk the earth. Ate 150 kilos of plants a day.",
     "Separable (Luke second, long). **Excluded — borderline, flag for owner.**"),
    ("S57", "GF / LUKE", "To grind food in their stomach. No teeth needed.",
     "Separable. **Excluded — borderline.**"),
    ("S58", "GF / LUKE", "Yeah. Toward the door.", "Separable. **Excluded — borderline.**"),
    ("S59b", "GF / LUKE", "— (none)", "**Luke has NO words in this cell.** Nothing to dub."),
    ("S59c", "GF / LUKE", "...they have a McDonald's?", "Luke first, GF second. **Excluded.**"),
    ("S60", "GF / LUKE", "...you don't think those kids actually got in, do you?",
     "Luke's turn is **between two GF turns**. **Excluded.**"),
    ("S62", "RANGER / LUKE", "...is that safe?",
     "Luke's turn is **between two RANGER turns**. **Excluded.**"),
    ("S65", "LUKE / GF", "Whoa. (BOTH)",
     "**BOTH speak the same word simultaneously.** Not separable. **Excluded.**"),
    ("S68", "GF / LUKE", "...the hybrid zone.", "Separable. **Excluded — borderline.**"),
    ("S69", "GF / LUKE", "...we have to tell someone.", "Separable. **Excluded — borderline.**"),
    ("S73", "LUKE / GF", "It can camouflage. One second it's there-",
     "GF **completes Luke's sentence** (\"-and then it's not.\"). Splitting breaks the joke's "
     "timing. **Excluded.**"),
    ("S75", "GF / LUKE", "People think he's a monster. But is he?",
     "Separable (Luke second). **Excluded — borderline, flag for owner.**"),
]
for s, spk, lw, v in TWO:
    w(f"| {s} | {spk} | {lw} | {v} |")
w("")
w("**Owner decision point:** the ~10 rows marked *borderline* are all \"Luke's turn is second and "
  "cleanly separable\". They could be dubbed in a later pass. I have **not** included them — the "
  "brief said be conservative, and each one carries a real risk of a seam between Grok-Luke and "
  "TTS-Luke **inside a single clip**, which is more jarring than a seam between clips.")
w("")
w("---")
w("")
w("## 10. Timing — what the assembler must handle")
w("")
w("`est_tts_speech_seconds` = words ÷ 2.6 (the same conservative rate the v1 manifest uses). "
  "Measured reality: **Grok's Luke speaks at 3.29 wps** (`speaking_rate_FINAL.json`), so 2.6 "
  "over-predicts the length of every line. Both numbers are given.")
w("")
w("These are **off-camera** dubs, so the new line does not have to match the old speech window — "
  "it only has to fit inside the **clip**.")
w("")
w("| Shot | words | est @2.6 | est @3.29 | old speech | clip | headroom @2.6 |")
w("|---|---|---|---|---|---|---|")
for l in m["lines"]:
    if l["clip_duration_s"] is None or l["speaker"] != "LUKE":
        continue
    if l["shot"] == "S46":
        continue
    e26 = l["est_tts_speech_seconds"]
    e33 = round(l["word_count"] / 3.29, 2)
    cd = l["clip_duration_s"]
    head = round(cd - e26, 2)
    mark = " **⚠️**" if head < 0.5 else ""
    w(f"| {l['shot']} | {l['word_count']} | {e26}s | {e33}s | "
      f"{l['existing_speech_duration_s']}s | {cd}s | {head}s{mark} |")
w("")
w("**⚠️ Risk R3 — three lines overflow their clip at the conservative 2.6 wps:** "
  "**S21** (−0.50s), **S22** (−0.88s), **S29** (+0.27s, inside the margin). "
  "At the measured 3.29 wps **all three fit comfortably.** So this is most likely an artifact of "
  "the conservative estimate — but if the take does come back long, the fixes are free and in "
  "this order: (1) ElevenLabs' per-generation **speed** control, (2) hold the last frame of the "
  "6.04s clip for ~1s. **Do not paraphrase the line to make it fit.**")
w("")
w("---")
w("")
w("## 11. Bonus: the re-voice also fixes 4 Grok script deviations")
w("")
w("Dubbing restores the *scripted* line, which silently repairs these:")
w("")
w("| Shot | Grok actually said | Scripted line (what the dub restores) |")
w("|---|---|---|")
w("| **S50** | \"Comment **you to Raptor** if you learned something… What do you think?\" | "
  "\"Comment 'Utahraptor' if you learned something. Let's give the internet a quiz.\" |")
w("| **S52** | \"**Starchosaurus**… Yeah, looks like it.\" | "
  "\"Styracosaurus — all those spikes are just for show. Mostly.\" (this is the owner's "
  "flagged S52 ad-lib) |")
w("| **S28** | \"…seeing that. **They're so close.**\" | \"Imagine looking up and seeing that.\" |")
w("| **S59** | \"Okay, now food. **Come on!**\" | \"Okay, NOW food.\" |")
w("")
w("S50 and S52 are real content bugs — Grok **mispronounced the dinosaur names the scene is "
  "about**. The dub fixes both for free.")
w("")
w("---")
w("")
w("## 12. Pre-Generate checklist (per pass — this is the whole point)")
w("")
w("1. Voice + model selected. Model **must be Eleven Multilingual v2**.")
w("2. **Paste** the block — never type it.")
w("3. Read the textarea back out of the DOM and SHA-256 it:")
w("   ```js")
w("   const t = document.querySelector('textarea').value;")
w("   crypto.subtle.digest('SHA-256', new TextEncoder().encode(t))")
w("     .then(b => console.log([...new Uint8Array(b)].map(x=>x.toString(16)"
  ".padStart(2,'0')).join('')));")
w("   ```")
w("4. It must equal the SHA for that pass **exactly**. If not: clear, re-paste, re-check. "
  "Usual culprits — a smart-quoted apostrophe, a trailing newline, the editor eating the blank "
  "lines around a break tag.")
w("5. Only then click **Generate**. Once.")
w("")
w("> **Clipboard warning** (memory, learned the hard way): pasting collides with the owner's live "
  "clipboard. **Re-set the clipboard immediately before every Cmd+V.**")
w("")
w("---")
w("")
w("## 13. Splitting + dubbing recipe (free, repeat as needed)")
w("")
w("```bash")
w("# 1. split a pass at its 3.0s silences")
w("ffmpeg -i audio/dinoverse_omega/source_chunks/luke_body_pass.mp3 \\")
w("  -af silencedetect=noise=-40dB:d=1.2 -f null -")
w("# expect n_lines-1 silences. If the count is off, loosen to -45dB:d=0.9 and re-run.")
w("# Cut at the MIDPOINT of each silence, keep ~0.3s handles, export 48k WAV.")
w("")
w("# 2. dub a clip: strip Grok's speech, keep the ambience, lay the new line on top.")
w("#    (demucs is already proven in this dir - see sep/htdemucs/)")
w("demucs --two-stems=vocals -n htdemucs -d cpu v2/clips/S17.mp4")
w("#    -> no_vocals.wav = ambience/SFX with the speech removed. Mix luke_s17.wav over it.")
w("```")
w("")
w("A mis-split is free to redo. A bad take is not. That asymmetry is why the passes are batched.")
w("")
w("---")
w("")
w("## 14. Output convention")
w("")
w("```")
w("audio/dinoverse_omega/")
for l in m["lines"]:
    w(f"├── {l['wav']}")
w("└── source_chunks/")
seen = []
for p in m["generation_passes"]:
    if p["source_mp3"] not in seen:
        seen.append(p["source_mp3"])
for i, s in enumerate(seen):
    w(f"    {'└──' if i == len(seen) - 1 else '├──'} {s.split('/')[-1]}")
w("```")
w("")
w("Audio is gitignored — **keep the source chunks.** They cannot be regenerated for free.")

md = "\n".join(o) + "\n"
with open(f"{BASE}/VO_SCRIPT_LUKE_REVOICE.md", "w", encoding="utf-8") as f:
    f.write(md)
print(f"wrote {BASE}/VO_SCRIPT_LUKE_REVOICE.md  ({len(md)} chars, "
      f"sha256={hashlib.sha256(md.encode()).hexdigest()[:16]}...)")
