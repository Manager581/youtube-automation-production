#!/usr/bin/env python
"""
Build the EXPANDED, LOCKED ElevenLabs VO script for the Luke re-voice.

EXTENDS the already-locked cold-open script (VO_SCRIPT_FINAL.md / vo_manifest.json).
Same conventions, same SHA method, same target-wav naming. Nothing is reinvented:
 - the cold-open LUKE pass and the GF pass are rebuilt from the TSV and their SHAs are
   ASSERTED equal to the ones already locked in vo_manifest.json. If they drift, the
   build fails loudly.

Text is pulled VERBATIM from STORYBOARD.tsv column 'Dialogue / VO' by regex on the
speaker tag. The ONLY edits are the declared typography normalizations, and every one
of them is recorded and printed.

Outputs (both under work/vo_prep/):
  VO_SCRIPT_LUKE_REVOICE.md   - human-readable, exact paste blocks
  vo_manifest_v2.json         - machine-readable, every SHA-256
"""
import csv
import hashlib
import json
import re

ROOT = "/Users/jefflawrence/Documents/youtube-automation-production"
EP = f"{ROOT}/dinoverse_clone/episode_01_omega_rex"
TSV = f"{EP}/STORYBOARD.tsv"
BASE = f"{EP}/v2/work/vo_prep"
SPANS = f"{BASE}/speech_spans.json"
OLD_MANIFEST = f"{BASE}/vo_manifest.json"
MD_OUT = f"{BASE}/VO_SCRIPT_LUKE_REVOICE.md"
JSON_OUT = f"{BASE}/vo_manifest_v2.json"

BREAK = '<break time="3.0s" />'
WPS = 2.6  # same conversational estimate the locked manifest uses

# ---------------------------------------------------------------- scope
# 27 LUKE-solo GEN/clip rows exist. S37 is an ON-CAMERA selfie two-shot (verified:
# feas/zoom_LUKE_S37.png shows Luke's face front and centre, mouth open mid-word) ->
# dubbing it would break lip-sync. S13 is also on-camera AND a two-speaker row.
LUKE_BODY_CALM = ["S17", "S19", "S21", "S22", "S26", "S28", "S29", "S32", "S33", "S35",
                  "S40", "S43", "S48", "S50", "S52", "S54", "S56", "S59", "S61", "S63",
                  "S67", "S71", "S74"]
LUKE_BODY_SHOUT = ["S76", "S78", "S81"]          # script-shouted -> own pass, own settings
LUKE_ONCAM_BLOCKED = ["S13", "S37"]
LUKE_EXTRA = ["S88", "S46"]                       # opt-in: LUKE VO climax + S46 punchline

COLDOPEN_LUKE = ["S01", "S03", "S12", "S89"]      # already locked - rebuilt + SHA-asserted
GF_LINES = ["S02", "S11", "S89"]

# ---------------------------------------------------------------- normalizations
NORMS = [
    ("...", "…", "N1  '...' -> single U+2026 ellipsis (existing convention)"),
    (" - ", " — ", "N2  spaced ASCII hyphen -> em dash (existing convention)"),
]
# N3 is positional (end-of-line cut-off), handled separately.


def normalize(s):
    """Apply the declared typography normalizations. Returns (text, [applied])."""
    applied = []
    out = s
    for src, dst, label in NORMS:
        if src in out:
            applied.append((label, src, dst, out.count(src)))
            out = out.replace(src, dst)
    # N3: a line that ENDS on a cut-off hyphen ("...get away from the-") -> em dash.
    if out.endswith("-") and not out.endswith("--"):
        applied.append(("N3  trailing cut-off hyphen -> em dash (NEW convention)",
                        "-", "—", 1))
        out = out[:-1] + "—"
    # apostrophes must stay ASCII U+0027 - a smart quote changes the bytes and breaks the SHA
    assert "’" not in out and "‘" not in out, f"curly apostrophe leaked in: {out!r}"
    assert "“" not in out and "”" not in out, f"curly double quote leaked in: {out!r}"
    return out, applied


def sha(t):
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- read TSV
rows = {r["Shot"]: r for r in csv.DictReader(open(TSV, newline="", encoding="utf-8"),
                                             delimiter="\t")}
spans = json.load(open(SPANS, encoding="utf-8"))
old = json.load(open(OLD_MANIFEST, encoding="utf-8"))

SPEAKER_RE = {
    "LUKE": re.compile(r'LUKE(?:\s+VO)?(?:\s*\([^)]*\))?:\s*"([^"]*)"'),
    "GF": re.compile(r'GF(?:\s+VO)?(?:\s*\([^)]*\))?:\s*"([^"]*)"'),
    "RANGER": re.compile(r'RANGER(?:\s+VO)?(?:\s*\([^)]*\))?:\s*"([^"]*)"'),
}


def pull(shot, speaker):
    cell = rows[shot]["Dialogue / VO"]
    m = SPEAKER_RE[speaker].findall(cell)
    assert len(m) == 1, f"{shot}/{speaker}: expected 1 quoted turn, got {len(m)}: {m}"
    return m[0]


def dur_board(shot):
    d = (rows[shot]["Dur"] or "").strip().rstrip("s")
    try:
        return float(d)
    except ValueError:
        return None


def mkline(shot, speaker, slot, role, wav, tsv_override=None):
    raw = tsv_override if tsv_override is not None else pull(shot, speaker)
    exact, applied = normalize(raw)
    sp = spans.get(shot, {})
    wc = len(exact.split())
    return {
        "shot": shot,
        "slot": slot,
        "speaker": speaker,
        "role": role,
        "tsv_verbatim": raw,
        "exact_text": exact,
        "normalizations_applied": [a[0] for a in applied],
        "sha256": sha(exact),
        "wav": wav,
        "target_wav": f"audio/dinoverse_omega/{wav}",
        "word_count": wc,
        "est_tts_speech_seconds": round(wc / WPS, 2),
        "boarded_dur_seconds": dur_board(shot),
        "clip_duration_s": sp.get("clip_duration_s"),
        "existing_speech_duration_s": sp.get("existing_speech_duration_s"),
    }


lines = []

# --- LUKE body (calm)
for s in LUKE_BODY_CALM:
    lines.append(mkline(s, "LUKE", s, f"body dialogue - scene {rows[s]['Scene']}",
                        f"luke_{s.lower()}.wav"))
# --- LUKE body (shouted)
for s in LUKE_BODY_SHOUT:
    ln = mkline(s, "LUKE", s, f"body dialogue (SHOUTED) - scene {rows[s]['Scene']}",
                f"luke_{s.lower()}.wav")
    ln["delivery"] = "SHOUTED / urgent - see risk R1"
    lines.append(ln)
# --- LUKE cold open (already locked; SHAs asserted below)
lines.append(mkline("S01", "LUKE", "S01", "cold open - card VO", "luke_s01.wav"))
lines.append(mkline("S03", "LUKE", "S03-S10", "cold open - one continuous line over 8 flashes",
                    "luke_s03_montage.wav"))
lines.append(mkline("S12", "LUKE", "S12", "cold open - hook / showdown tease", "luke_s12.wav"))
lines.append(mkline("S89", "LUKE", "S89 (2nd)", "end-card CTA", "luke_s89_cta.wav"))
# --- GF (unchanged)
lines.append(mkline("S02", "GF", "S02", "cold open - host selfie at the gate", "gf_s02.wav"))
lines.append(mkline("S11", "GF", "S11", "cold open - flash: teens at the door", "gf_s11.wav"))
lines.append(mkline("S89", "GF", "S89 (1st)", "end-card closer (lands BEFORE Luke's CTA)",
                    "gf_s89_closer.wav"))
# --- RANGER (S46 myth-bust)
lines.append(mkline("S46", "RANGER", "S46 (1st)", "S46 myth-bust - the Utahraptor payoff",
                    "ranger_s46.wav"))
# --- OPT-IN extras
ln = mkline("S88", "LUKE", "S88", "climax VO over the three-way showdown", "luke_s88_vo.wav")
ln["scope"] = "OPT-IN - Speaker is 'LUKE VO', not 'LUKE'; see flag F1"
lines.append(ln)
ln = mkline("S46", "LUKE", "S46 (2nd)", "S46 punchline (after the RANGER turn)",
            "luke_s46_punchline.wav")
ln["scope"] = "OPT-IN - two-speaker row; see flag F2"
lines.append(ln)

by_key = {(l["shot"], l["speaker"], l["slot"]): l for l in lines}


# ---------------------------------------------------------------- passes
def mkpass(pass_id, speaker, keys, mp3, note=""):
    ls = [by_key[k] for k in keys]
    paste = f"\n\n{BREAK}\n\n".join(l["exact_text"] for l in ls)
    return {
        "pass_id": pass_id,
        "speaker": speaker,
        "n_lines": len(ls),
        "segment_order": [l["wav"] for l in ls],
        "paste_text": paste,
        "sha256_paste_text": sha(paste),
        "char_count": len(paste),
        "source_mp3": f"audio/dinoverse_omega/source_chunks/{mp3}",
        "expected_segments_after_silence_split": len(ls),
        "note": note,
    }


# split the body at a natural SCENE boundary if > 5000 chars
body_keys = [(s, "LUKE", s) for s in LUKE_BODY_CALM]
body_all = mkpass("PASS_LUKE_BODY", "LUKE", body_keys, "luke_body_pass.mp3")

passes = []
if body_all["char_count"] > 5000:
    # scenes: 2 Carno / 3 Quetzal / 4 Aquatic | 5 Utahraptor / 6 Herb / 7 Lunch / 8 T-Rex / 9 Hybrid
    a = [s for s in LUKE_BODY_CALM if rows[s]["Scene"] in
         ("2 Carnotaurus", "3 Quetzalcoatlus", "4 Aquatic")]
    b = [s for s in LUKE_BODY_CALM if s not in a]
    passes.append(mkpass("PASS_LUKE_BODY_1", "LUKE", [(s, "LUKE", s) for s in a],
                         "luke_body_pass_1.mp3",
                         "scenes 2-4 (Carnotaurus / Quetzalcoatlus / Aquatic)"))
    passes.append(mkpass("PASS_LUKE_BODY_2", "LUKE", [(s, "LUKE", s) for s in b],
                         "luke_body_pass_2.mp3",
                         "scenes 5-9 (Utahraptor / Herbivores / Lunch / T-Rex / Hybrid)"))
else:
    body_all["note"] = ("1812 chars - under the 5000-char split threshold, so this stays as "
                        "ONE generation. No scene-boundary split needed.")
    passes.append(body_all)

passes.append(mkpass("PASS_LUKE_SHOUT", "LUKE", [(s, "LUKE", s) for s in LUKE_BODY_SHOUT],
                     "luke_shout_pass.mp3",
                     "SHOUTED lines - generate with LOWER stability / HIGHER style than the "
                     "body pass. Kept out of the body pass because ElevenLabs voice settings "
                     "are per-generation and one flat setting cannot serve both."))
passes.append(mkpass("PASS_LUKE_COLDOPEN", "LUKE",
                     [("S01", "LUKE", "S01"), ("S03", "LUKE", "S03-S10"),
                      ("S12", "LUKE", "S12"), ("S89", "LUKE", "S89 (2nd)")],
                     "luke_pass.mp3",
                     "UNCHANGED from the locked vo_manifest.json PASS_1_LUKE"))
passes.append(mkpass("PASS_GF", "GF",
                     [("S02", "GF", "S02"), ("S11", "GF", "S11"),
                      ("S89", "GF", "S89 (1st)")],
                     "gf_pass.mp3",
                     "UNCHANGED from the locked vo_manifest.json PASS_2_GF. GF is NOT "
                     "re-voiced in the body - she is on camera in ~16 clips."))
passes.append(mkpass("PASS_RANGER", "RANGER", [("S46", "RANGER", "S46 (1st)")],
                     "ranger_s46_pass.mp3",
                     "single line - no break tags needed"))
passes.append(mkpass("PASS_LUKE_EXTRA", "LUKE",
                     [("S88", "LUKE", "S88"), ("S46", "LUKE", "S46 (2nd)")],
                     "luke_extra_pass.mp3",
                     "OPT-IN. Both are off-camera and both are RECOMMENDED, but neither "
                     "matches the literal 'Speaker == LUKE' filter, so they are isolated "
                     "here: approving or dropping them does not touch any other SHA."))

# ---------------------------------------------------------------- SHA assertions vs locked v1
old_pass = {p["pass_id"]: p for p in old["generation_passes"]}
new_pass = {p["pass_id"]: p for p in passes}
assert new_pass["PASS_LUKE_COLDOPEN"]["sha256_paste_text"] == \
    old_pass["PASS_1_LUKE"]["sha256_paste_text"], "cold-open pass drifted from the locked v1!"
assert new_pass["PASS_GF"]["sha256_paste_text"] == \
    old_pass["PASS_2_GF"]["sha256_paste_text"], "GF pass drifted from the locked v1!"
print("OK  cold-open + GF passes rebuilt from the TSV and SHA-match the locked v1 manifest")

manifest = {
    "project": "dinoverse_clone/episode_01_omega_rex",
    "episode": "Omega Rex (episode_01)",
    "version": "v2 - LUKE RE-VOICE",
    "status": "LOCKED_PENDING_OWNER_SIGNOFF",
    "supersedes": "vo_manifest.json (cold open + S89 only). The cold-open and GF passes here "
                  "are byte-identical to v1 and carry the same SHAs.",
    "rule": "ONE generation per pass, no re-rolls (memory: elevenlabs-one-pass-rule)",
    "decision": "RE-VOICE LUKE across his off-camera body dialogue (Grok gave him a different "
                "voice in nearly every clip: F0 128-392 Hz across 27 clips). GF is NOT "
                "re-voiced in the body - she is on camera in ~16 clips and dubbing would "
                "break lip-sync; she keeps only her 3 cold-open/end-card lines.",
    "source_of_truth": TSV,
    "source_column": "Dialogue / VO",
    "measurements": "speech_spans.json (ffprobe + faster-whisper 'small' word timestamps)",
    "model": "Eleven Multilingual v2 (honours <break time=\"x\" />)",
    "break_tag": BREAK,
    "words_per_second_estimate": WPS,
    "wav_output_dir": "audio/dinoverse_omega/",
    "split_recipe": "ffmpeg -i <pass>.mp3 -af silencedetect=noise=-40dB:d=1.2 -f null -  ->  "
                    "expect n_lines-1 silences; cut at silence midpoints, keep 0.3s handles",
    "typography_normalizations": [
        "N1  '...' -> U+2026 ellipsis (existing convention)",
        "N2  ' - ' -> ' — ' em dash (existing convention)",
        "N3  trailing cut-off hyphen -> U+2014 em dash (NEW - S76, S78 only)",
        "N4  apostrophes stay ASCII U+0027 - never smart-quote",
    ],
    "excluded_on_camera": [
        {"shot": s, "speaker": rows[s]["Speaker"], "on_screen": rows[s]["On-screen"],
         "why": "LUKE is ON CAMERA (selfie two-shot) - dubbing breaks lip-sync",
         "verified": f"feas/zoom_LUKE_{s}.png",
         "clip_duration_s": spans[s]["clip_duration_s"],
         "existing_speech_duration_s": spans[s]["existing_speech_duration_s"]}
        for s in LUKE_ONCAM_BLOCKED],
    "lines": lines,
    "generation_passes": passes,
}
with open(JSON_OUT, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

print(f"\nwrote {JSON_OUT}")
for p in passes:
    print(f"  {p['pass_id']:22s} {p['n_lines']:2d} lines {p['char_count']:5d} chars  "
          f"{p['sha256_paste_text']}")
