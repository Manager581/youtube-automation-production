#!/usr/bin/env python3
"""script_to_lines.py — turn a tagged SCRIPT_v*.md into the VO_LINES_MANIFEST.json the rest of the pipeline consumes
(vo_prep chunk, spend_gate, build_edit_from_alignment, watch_gate line_off_speaker / host_halo).

This supersedes research/mrbeast_teardown/shrinking_planet/check_script.py, which hard-codes SCRIPT_v1.md and cannot be
pointed at another draft. Same beat/line grammar story_gate.py parses, so a script that passes the story gate converts here.

  script_to_lines.py --script SCRIPT_v4.md --out DIR/VO_LINES_MANIFEST.json [--takes DIR ...] [--lane lane.json]

REUSE: every --takes directory is scanned for <ID>.txt next to an <ID>.mp3. A line whose text matches an existing take
EXACTLY gets reuse_audio_from = that take id, so spend_gate does not charge for it. Matching is exact on purpose — a
one-word edit is a different performance and must be bought.

ON CAMERA: watch_gate's line_off_speaker exempts ORB unless the line says otherwise, so an ORB line MUST declare
`(on)` or `(vo)` in its attribute block. Without it the host is invisible to the gate, which is how the v3 first minute
shipped with the host's lines laid over shots the host was not in.
"""
import argparse, glob, hashlib, json, os, re, sys

BEAT = re.compile(r"^##\s+(B\d{2})\s+\[(\d+:\d{2})-(\d+:\d{2})\]")
LINE = re.compile(r"^\*\*(\w+)\*\*\s*\(([^)]*)\):\s*(.+)$")


def tc(s):
    m, sec = s.split(":")
    return int(m) * 60 + int(sec)


def takes(dirs):
    """id -> text for every take that actually has audio on disk."""
    out = {}
    for d in dirs:
        for t in sorted(glob.glob(os.path.join(d, "*.txt"))):
            stem = os.path.splitext(t)[0]
            if not (os.path.exists(stem + ".mp3") or os.path.exists(stem + ".wav")):
                continue
            out.setdefault(open(t, encoding="utf-8").read().strip(), os.path.basename(stem))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--takes", action="append", default=[], help="directory of existing <ID>.txt/<ID>.mp3 takes; repeatable")
    ap.add_argument("--lane")
    ap.add_argument("--schema", default="")
    a = ap.parse_args()

    have = takes(a.takes)
    lines, fails = [], []
    beat = None
    span = {}
    per_beat = {}
    for raw in open(a.script, encoding="utf-8"):
        s = raw.strip()
        m = BEAT.match(s)
        if m:
            beat = m.group(1)
            span[beat] = (tc(m.group(2)), tc(m.group(3)))
            per_beat.setdefault(beat, [])
            continue
        m = LINE.match(s)
        if not m or beat is None:
            continue
        spk, attr, text = m.group(1).upper(), m.group(2), m.group(3).strip()
        mouth = None
        mm = re.search(r"mouth:\s*(ON|OFF)", attr, re.I)
        if mm:
            mouth = mm.group(1).upper()
        on_camera = None
        mc = re.search(r"on_camera:\s*(true|false)", attr, re.I)
        if mc:
            on_camera = mc.group(1).lower() == "true"
        elif re.search(r"\bon\b|\bon-camera\b", attr, re.I):
            on_camera = True
        elif re.search(r"\bvo\b|\bv\.o\.\b|\boff-camera\b", attr, re.I):
            on_camera = False
        if spk == "ORB" and on_camera is None:
            fails.append(f"{beat}: ORB line has no (on)/(vo) marker — watch_gate exempts ORB unless the line declares it: {text[:48]!r}")
        if spk != "ORB" and on_camera is None:
            on_camera = True   # a contestant who speaks is in frame unless the script says otherwise
        # **emphasis** is an instruction to the edit builder, not something the voice says: strip it from the spoken text
        # (it is characters ElevenLabs would otherwise be charged for) and keep the words for build_edit_from_alignment.
        emphasis = re.findall(r"\*\*(.+?)\*\*", text)
        spoken = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        per_beat[beat].append({"speaker": spk, "mouth": mouth, "text": spoken, "emphasis": emphasis, "on_camera": on_camera})

    if fails:
        print("script_to_lines REFUSED:")
        for f in fails:
            print("  " + f)
        return 1

    n = 0
    for beat, rows in per_beat.items():
        t0, t1 = span[beat]
        for k, r in enumerate(rows):
            n += 1
            t = t0 + (t1 - t0) * (k + 0.5) / max(len(rows), 1)
            reuse = have.get(r["text"])
            lines.append({
                "id": f"L{n:02d}_{r['speaker']}",
                "beat": beat,
                "t": "%02d:%02d" % (t // 60, t % 60),
                "speaker": r["speaker"],
                "mouth": r["mouth"],
                "chars": len(r["text"]),
                "sha256": hashlib.sha256(r["text"].encode()).hexdigest()[:16],
                "text": r["text"],
                "emphasis": r["emphasis"],
                "on_camera": r["on_camera"],
                "reuse_audio_from": reuse,
            })

    new_chars = sum(l["chars"] for l in lines if not l["reuse_audio_from"])
    man = {
        "_schema": a.schema or f"lines built from {os.path.basename(a.script)} by script_to_lines.py; reuse_audio_from = an existing take with EXACTLY this text",
        "source_script": a.script,
        "source_sha256": hashlib.sha256(open(a.script, "rb").read()).hexdigest(),
        "lines": lines,
        "total_chars": sum(l["chars"] for l in lines),
        "revoice_lines": sum(1 for l in lines if not l["reuse_audio_from"]),
        "revoice_chars": new_chars,
    }
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(man, open(a.out, "w"), indent=1)
    print(f"script_to_lines: {len(lines)} lines, {man['total_chars']} chars total, "
          f"{man['revoice_lines']} to voice ({new_chars} chars), {len(lines) - man['revoice_lines']} reused -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
