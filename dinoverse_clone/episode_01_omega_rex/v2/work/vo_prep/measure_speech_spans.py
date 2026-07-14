#!/usr/bin/env python
"""
Measure, for every clip we intend to DUB, two numbers the assembler needs:
  clip_duration_s          - ffprobe duration of the clip actually in rough_cut_v6
  existing_speech_duration_s - last_word_end - first_word_start from faster-whisper
                               word timestamps (same model + method as drift_census.py:
                               'small', int8, CPU, word_timestamps=True, language='en')

The new TTS line has to FIT inside existing_speech_duration_s (ideally) or the shot has
to stretch. Nothing here is estimated - every number comes from the file on disk.

S46 carries two speakers (RANGER then LUKE). We dump its full word list so the
RANGER/LUKE boundary can be read off the transcript rather than guessed.
"""
import json
import subprocess

from faster_whisper import WhisperModel

ROOT = "/Users/jefflawrence/Documents/youtube-automation-production"
CLIPS = f"{ROOT}/dinoverse_clone/episode_01_omega_rex/v2/clips"
OUT = f"{ROOT}/dinoverse_clone/episode_01_omega_rex/v2/work/vo_prep/speech_spans.json"

# 26 dubbable LUKE-solo body shots (27 solo minus S37 = on-camera selfie blocker)
# + the 3 shouted ones are inside this list (S76, S78, S81)
LUKE_BODY = [
    "S17", "S19", "S21", "S22", "S26", "S28", "S29", "S32", "S33", "S35",
    "S40", "S43", "S48", "S50", "S52", "S54", "S56", "S59", "S61", "S63",
    "S67", "S71", "S74", "S76", "S78", "S81",
]
FLAGGED = ["S88"]          # LUKE VO climax line - off-camera, scope question
TWO_SPEAKER = ["S46"]      # RANGER turn + LUKE punchline
BLOCKED = ["S13", "S37"]   # on-camera - measured for the record only

model = WhisperModel("small", device="cpu", compute_type="int8")


def ffprobe_dur(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True, check=True)
    return round(float(r.stdout.strip()), 2)


def words_of(path):
    segs, _ = model.transcribe(path, word_timestamps=True, language="en")
    return [{"w": w.word.strip(), "s": round(w.start, 2), "e": round(w.end, 2)}
            for s in segs for w in (s.words or [])
            if any(c.isalnum() for c in w.word)]


out = {}
for group, shots in (("luke_body", LUKE_BODY), ("flagged", FLAGGED),
                     ("two_speaker", TWO_SPEAKER), ("blocked_on_camera", BLOCKED)):
    for shot in shots:
        p = f"{CLIPS}/{shot}.mp4"
        ws = words_of(p)
        rec = {
            "group": group,
            "clip_duration_s": ffprobe_dur(p),
            "n_words": len(ws),
            "transcript": " ".join(w["w"] for w in ws),
        }
        if ws:
            rec["speech_start_s"] = ws[0]["s"]
            rec["speech_end_s"] = ws[-1]["e"]
            rec["existing_speech_duration_s"] = round(ws[-1]["e"] - ws[0]["s"], 2)
        else:
            rec["existing_speech_duration_s"] = None
        if shot in TWO_SPEAKER:
            rec["words"] = ws          # need the turn boundary, not just the span
        out[shot] = rec
        print(shot, rec["clip_duration_s"], rec.get("existing_speech_duration_s"),
              "|", rec["transcript"][:70])

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
print("\nwrote", OUT)
