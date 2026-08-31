#!/usr/bin/env python3
"""Own-channel audience read (PIPELINE_OVERHAUL_PLAN §S11 / build step 3).

Discovers every PUBLIC upload on the owned channels listed in publish_ledger.json
via yt-dlp, fetches per-video metrics, then:
  - writes  reads/own_channel_read_<date>.json   (raw per-video metrics + days_live)
  - records the view count under each ledger entry's dated "views" map
  - auto-appends newly discovered uploads to the ledger (provenance "owner-direct
    (auto-discovered)") and flags ledger entries that have gone missing/private
  - appends a dated line to reads/READS_LEDGER.md and writes reads/summary_<date>.md

Public data only. CTR/retention require the owner present in Studio (TechJoint
pattern) and are NOT collected here. Below the minimum-signal floor (plan §S11)
these reads are note-only calibration data — never fail-close a lane on them.

Usage: python3 scripts/own_channel_read.py [--date YYYY-MM-DD] [--ledger PATH]
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import sys

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FIELDS = ["id", "title", "upload_date", "duration", "view_count", "like_count", "comment_count"]


def ytdlp(args):
    r = subprocess.run(["yt-dlp", "--no-update"] + args, capture_output=True, text=True, timeout=300)
    return r


def list_channel_ids(handle):
    ids = []
    for tab in ("videos", "shorts"):
        r = ytdlp(["--flat-playlist", "--print", "%(id)s", f"https://www.youtube.com/{handle}/{tab}"])
        if r.returncode == 0:
            ids += [l.strip() for l in r.stdout.splitlines() if l.strip()]
        elif "does not have a" not in r.stderr:
            print(f"WARN: listing {handle}/{tab} failed: {r.stderr.strip().splitlines()[-1] if r.stderr.strip() else '?'}")
    return ids


def fetch_meta(video_ids):
    if not video_ids:
        return {}
    sep = " ||| "
    r = ytdlp(["--print", sep.join(f"%({f})s" for f in FIELDS), "--"] + list(video_ids))
    out = {}
    for line in r.stdout.splitlines():
        parts = line.split(sep)
        if len(parts) != len(FIELDS):
            continue
        rec = dict(zip(FIELDS, parts))
        for k in ("duration", "view_count", "like_count", "comment_count"):
            rec[k] = None if rec[k] in ("NA", "None", "") else int(float(rec[k]))
        out[rec["id"]] = rec
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--ledger", default=os.path.join(REPO, "publish_ledger.json"))
    args = ap.parse_args()
    date = args.date

    ledger = json.load(open(args.ledger))
    by_id = {e["video_id"]: e for e in ledger["entries"]}

    live, meta = {}, {}
    for cname, ch in ledger["channels"].items():
        ids = list_channel_ids(ch["handle"])
        live[cname] = ids
        meta.update(fetch_meta(ids))

    discovered, missing = [], []
    for cname, ids in live.items():
        for vid in ids:
            if vid not in by_id:
                m = meta.get(vid, {})
                entry = {
                    "video_id": vid, "channel": cname,
                    "upload_date": (lambda u: f"{u[:4]}-{u[4:6]}-{u[6:]}" if u and len(u) == 8 else None)(m.get("upload_date")),
                    "duration_s": m.get("duration"), "title": m.get("title"),
                    "provenance": "owner-direct (auto-discovered)", "repo_artifact": None, "views": {},
                }
                ledger["entries"].append(entry)
                by_id[vid] = entry
                discovered.append(vid)
    for vid, e in by_id.items():
        if e["channel"] in live and vid not in live[e["channel"]]:
            missing.append(vid)

    read = {"date": date, "videos": []}
    for vid, e in by_id.items():
        m = meta.get(vid)
        if not m:
            continue
        e.setdefault("views", {})[date] = m["view_count"]
        days = None
        if e.get("upload_date"):
            days = (dt.date.fromisoformat(date) - dt.date.fromisoformat(e["upload_date"])).days
        read["videos"].append({**{k: m[k] for k in FIELDS}, "channel": e["channel"], "days_live": days})
    read["discovered_not_in_ledger"] = discovered
    read["ledger_entries_not_public"] = missing

    reads_dir = os.path.join(REPO, "reads")
    os.makedirs(reads_dir, exist_ok=True)
    read_path = os.path.join(reads_dir, f"own_channel_read_{date}.json")
    json.dump(read, open(read_path, "w"), indent=1)
    json.dump(ledger, open(args.ledger, "w"), indent=2)

    vids = sorted(read["videos"], key=lambda v: -(v["view_count"] or 0))
    lines = [f"# Own-channel read — {date}", "",
             "| views | likes | days live | dur | channel | title |", "|---|---|---|---|---|---|"]
    for v in vids:
        lines.append(f"| {v['view_count']} | {v['like_count']} | {v['days_live']} | {v['duration']}s "
                     f"| {v['channel']} | {(v['title'] or '')[:60]} |")
    lines.append("")
    if discovered:
        lines.append(f"**Auto-discovered (no repo record):** {', '.join(discovered)}")
    if missing:
        lines.append(f"**Ledger entries no longer public (deleted/private?):** {', '.join(missing)}")
    lines.append(f"\nRaw: `reads/own_channel_read_{date}.json`. Views also recorded in `publish_ledger.json`. "
                 "Public metrics only — no CTR/retention without the owner in Studio.")
    open(os.path.join(reads_dir, f"summary_{date}.md"), "w").write("\n".join(lines) + "\n")

    ledger_md = os.path.join(reads_dir, "READS_LEDGER.md")
    is_new = not os.path.exists(ledger_md)
    with open(ledger_md, "a") as f:
        if is_new:
            f.write("# Reads ledger — one dated line per own-channel read\n\n")
        top = vids[0] if vids else None
        f.write(f"- {date}: {len(vids)} videos read, {len(discovered)} discovered, {len(missing)} missing; "
                f"top = {top['view_count']} views ({(top['title'] or '')[:40]})\n" if top else f"- {date}: no videos read\n")

    print(f"OK: {len(vids)} videos -> {read_path}; ledger views updated; summary written.")
    if missing:
        print(f"WARN missing from public tabs: {missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
