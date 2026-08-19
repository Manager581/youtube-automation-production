#!/usr/bin/env python3
"""Per-video forensic pass for the chocolate-chip-cookie competitor set.

Reuses research/wildbirdsurvival_teardown/extract_forensics.py (cuts via ffmpeg scene score,
librosa audio envelopes/onsets, cut<->word alignment). Adds: whisper word-level transcript,
contact sheets (dense grid / one-frame-per-cut / hook zone @2fps), derived metrics table.

Usage:
  venv/bin/python research/techjoint_cookies/competitors/analyze_competitors.py --set long
  venv/bin/python research/techjoint_cookies/competitors/analyze_competitors.py --set short
Outputs under research/techjoint_cookies/competitors/:
  forensics/<id>.json   transcripts/<id>.json + .txt   sheets/<id>_{grid,cuts,hook}.jpg   metrics_<set>.tsv
"""
import argparse, json, os, re, statistics, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "research", "wildbirdsurvival_teardown"))
import extract_forensics as EF  # noqa: E402

VID_DIR = {"long": os.path.join(ROOT, "footage", "techjoint_competitors.nosync", "long"),
           "short": os.path.join(ROOT, "footage", "techjoint_competitors.nosync", "short")}
WHISPERX = os.path.join(ROOT, "venv", "bin", "whisperx")
LANG = {"PLIOTjj_gmY": "ar"}


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def probe(path):
    r = sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
            "stream=width,height,r_frame_rate:format=duration", "-of", "json", path])
    d = json.loads(r.stdout)
    st = d["streams"][0]
    num, den = st["r_frame_rate"].split("/")
    return dict(w=st["width"], h=st["height"], fps=round(int(num) / int(den), 2), dur=float(d["format"]["duration"]))


def whisper_words(vid, video, outdir):
    """whisperx (faster-whisper int8 + VAD + wav2vec2 word alignment). Same segments[].words[] shape
    as openai-whisper, so extract_forensics.load_words() reads it unchanged."""
    js = os.path.join(outdir, f"{vid}.json")
    if os.path.exists(js):
        return js
    wav = os.path.join(outdir, f"_{vid}.wav")
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-ac", "1", "-ar", "16000", wav])
    lang = LANG.get(vid, "en")
    r = sh([WHISPERX, wav, "--model", "base", "--language", lang, "--output_format", "json",
            "--output_dir", outdir, "--compute_type", "int8", "--device", "cpu"])
    produced = os.path.join(outdir, f"_{vid}.json")
    if os.path.exists(produced):
        os.rename(produced, js)
    else:
        sys.stderr.write(f"whisperx failed for {vid}: {r.stderr[-400:]}\n")
        json.dump({"segments": [], "text": ""}, open(js, "w"))
    os.remove(wav)
    d = json.load(open(js))
    with open(os.path.join(outdir, f"{vid}.txt"), "w") as f:
        for seg in d.get("segments", []):
            f.write(f"[{seg.get('start',0):6.2f}-{seg.get('end',0):6.2f}] {seg.get('text','').strip()}\n")
    return js


def contact_sheets(vid, video, info, outdir, vertical):
    dur = info["dur"]
    base = os.path.join(outdir, vid)
    # tile geometry: landscape tiles 320x180, vertical tiles 144x256
    tw, th = (144, 256) if vertical else (320, 180)
    cols = 10 if vertical else 6
    made = {}
    # dense grid (split into <=12-row pages so long videos stay legible)
    step = 1.0 if dur <= 90 else (2.0 if dur <= 240 else 3.0)
    per_page = cols * 12
    n = int(dur / step) + 1
    pages = max(1, -(-n // per_page))
    made["grid"] = dict(paths=[], step=step)
    for pg in range(pages):
        t0 = pg * per_page * step
        span = per_page * step
        out = f"{base}_grid.jpg" if pages == 1 else f"{base}_grid{pg + 1}.jpg"
        if not os.path.exists(out):
            cnt = min(per_page, n - pg * per_page)
            rows = max(1, -(-cnt // cols))
            sh(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t0:.2f}", "-t", f"{span:.2f}", "-i", video, "-vf",
                f"fps=1/{step},scale={tw}:{th}:force_original_aspect_ratio=decrease,pad={tw}:{th}:(ow-iw)/2:(oh-ih)/2,"
                f"drawtext=text='%{{pts\\:hms\\:{t0:.2f}}}':x=w-tw-4:y=h-th-4:fontsize=13:fontcolor=white:box=1:boxcolor=black@0.5,"
                f"tile={cols}x{rows}", "-frames:v", "1", "-q:v", "4", out])
        made["grid"]["paths"].append(out)
    # hook zone: first 6 s at 2 fps
    out = f"{base}_hook.jpg"
    if not os.path.exists(out):
        sh(["ffmpeg", "-y", "-loglevel", "error", "-t", "6", "-i", video, "-vf",
            f"fps=2,scale={tw}:{th}:force_original_aspect_ratio=decrease,pad={tw}:{th}:(ow-iw)/2:(oh-ih)/2,"
            f"drawtext=text='%{{pts\\:hms}}':x=w-tw-4:y=h-th-4:fontsize=13:fontcolor=white:box=1:boxcolor=black@0.5,"
            f"tile={cols}x2", "-frames:v", "1", "-q:v", "4", out])
    made["hook"] = out
    return made


def cut_sheet(vid, video, cuts, outdir, vertical):
    """One frame 0.3 s after every cut (plus t=0)."""
    tw, th = (144, 256) if vertical else (320, 180)
    cols = 10 if vertical else 6
    out = os.path.join(outdir, f"{vid}_cuts.jpg")
    if os.path.exists(out):
        return out
    times = [0.0] + [c + 0.3 for c in cuts]
    times = times[:120]
    tmp = os.path.join(outdir, f"_{vid}_cut_%03d.jpg")
    for i, t in enumerate(times):
        sh(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1", "-vf",
            f"scale={tw}:{th}:force_original_aspect_ratio=decrease,pad={tw}:{th}:(ow-iw)/2:(oh-ih)/2,"
            f"drawtext=text='{i} @{t:.1f}s':x=w-tw-4:y=h-th-4:fontsize=13:fontcolor=white:box=1:boxcolor=black@0.5",
            "-q:v", "4", tmp % i])
    rows = max(1, -(-len(times) // cols))
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-vf", f"tile={cols}x{rows}", "-frames:v", "1", "-q:v", "4", out])
    for i in range(len(times)):
        try: os.remove(tmp % i)
        except FileNotFoundError: pass
    return out


def derive_metrics(fx, words, dur):
    shots = fx["shots"]
    lens = [s["dur"] for s in shots]
    cuts = fx["cuts"]
    m = dict(dur=round(dur, 1), cuts=len(cuts), cuts_per_min=round(len(cuts) / (dur / 60), 1) if dur else 0,
             median_shot=round(statistics.median(lens), 2) if lens else dur,
             first_cut=round(cuts[0], 2) if cuts else None,
             pct_shots_under2s=round(100 * sum(1 for x in lens if x < 2) / len(lens)) if lens else 0,
             longest_hold=round(max(lens), 1) if lens else dur,
             cuts_first10s=sum(1 for c in cuts if c <= 10))
    # speech
    if words:
        spoken = 0.0
        for w in words:
            if w.get("e") is not None:
                spoken += max(0.0, w["e"] - w["s"])
        # merge into talk spans (gap<=0.6)
        spans = []
        for w in words:
            if spans and w["s"] - spans[-1][1] <= 0.6:
                spans[-1][1] = max(spans[-1][1], w.get("e") or w["s"])
            else:
                spans.append([w["s"], w.get("e") or w["s"]])
        talk = sum(e - s for s, e in spans)
        m.update(words=len(words), talk_pct=round(100 * talk / dur) if dur else 0,
                 wpm=round(len(words) / (talk / 60)) if talk > 5 else None,
                 first_word=round(words[0]["s"], 2),
                 max_pause=round(max([spans[0][0]] + [spans[i + 1][0] - spans[i][1] for i in range(len(spans) - 1)] + [dur - spans[-1][1]]), 1))
    else:
        m.update(words=0, talk_pct=0, wpm=None, first_word=None, max_pause=round(dur, 1))
    # cut-word alignment
    al = [a for a in fx["aligns"] if "d_word" in a]
    if al:
        m["cuts_on_word_pct"] = round(100 * sum(1 for a in al if abs(a["d_word"]) <= 0.4) / len(al))
        m["median_cut_to_word"] = round(statistics.median(abs(a["d_word"]) for a in al), 2)
    ons = fx["onsets"]
    m["onsets"] = len(ons)
    m["onsets_per_min"] = round(len(ons) / (dur / 60), 1) if dur else 0
    if cuts and ons:
        m["cuts_on_onset_pct"] = round(100 * sum(1 for c in cuts if min(abs(o - c) for o in ons) <= 0.15) / len(cuts))
    # music/energy: fraction of 0.5 s frames where harmonic rms > 20% of its max (proxy for a constant bed)
    env = fx["env"]
    rh = env["rms_h"]; rp = env["rms_p"]; r = env["rms"]
    if r:
        mx = max(r) or 1
        m["silent_pct"] = round(100 * sum(1 for x in r if x < 0.02 * mx) / len(r))
        m["harm_over_perc"] = round(sum(rh) / (sum(rp) or 1e-9), 2)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", required=True, choices=["long", "short"])
    ap.add_argument("--ids", help="comma list to restrict")
    ap.add_argument("--skip-whisper", action="store_true")
    a = ap.parse_args()
    vdir = VID_DIR[a.set]
    fdir = os.path.join(HERE, "forensics"); tdir = os.path.join(HERE, "transcripts"); sdir = os.path.join(HERE, "sheets")
    for d in (fdir, tdir, sdir): os.makedirs(d, exist_ok=True)
    ids = [f[:-4] for f in sorted(os.listdir(vdir)) if f.endswith(".mp4")]
    if a.ids: ids = [i for i in ids if i in a.ids.split(",")]
    rows = []
    for vid in ids:
        video = os.path.join(vdir, f"{vid}.mp4")
        info = probe(video)
        vertical = info["h"] > info["w"]
        wj = None if a.skip_whisper else whisper_words(vid, video, tdir)
        if wj and not EF.load_words(wj):
            wj = None  # no speech -> extract_forensics must not try word alignment
        fj = os.path.join(fdir, f"{vid}.json")
        if os.path.exists(fj):
            fx = json.load(open(fj))
        else:
            fx = EF.analyze(vid, video, wj)
            json.dump(fx, open(fj, "w"), indent=1)
        sheets = contact_sheets(vid, video, info, sdir, vertical)
        cut_sheet(vid, video, fx["cuts"], sdir, vertical)
        words = EF.load_words(wj) if wj else None
        m = derive_metrics(fx, words, info["dur"])
        m.update(id=vid, w=info["w"], h=info["h"], fps=info["fps"], grid_step=sheets["grid"]["step"])
        rows.append(m)
        print(f"{vid}: dur={m['dur']} cuts={m['cuts']} med={m['median_shot']} talk={m['talk_pct']}% wpm={m['wpm']} "
              f"onsets={m['onsets']} first_cut={m['first_cut']} first_word={m['first_word']}", flush=True)
    cols = ["id", "w", "h", "fps", "dur", "cuts", "cuts_per_min", "median_shot", "first_cut", "cuts_first10s",
            "pct_shots_under2s", "longest_hold", "words", "talk_pct", "wpm", "first_word", "max_pause",
            "cuts_on_word_pct", "median_cut_to_word", "onsets", "onsets_per_min", "cuts_on_onset_pct",
            "silent_pct", "harm_over_perc", "grid_step"]
    with open(os.path.join(HERE, f"metrics_{a.set}.tsv"), "w") as f:
        f.write("\t".join(cols) + "\n")
        for m in rows:
            f.write("\t".join("" if m.get(c) is None else str(m.get(c)) for c in cols) + "\n")
    print("wrote", os.path.join(HERE, f"metrics_{a.set}.tsv"))


if __name__ == "__main__":
    main()
