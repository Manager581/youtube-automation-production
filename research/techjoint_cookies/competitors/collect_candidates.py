#!/usr/bin/env python3
"""Collect chocolate-chip-cookie video candidates from YouTube search (view-sorted, filtered),
then fetch per-video metadata (upload_date, w/h, views, subs) and rank:

  long  = < 10 min, uploaded within the last 365 days, landscape  -> top 10
  short = Shorts (vertical, <= 180 s), uploaded within the last 730 days -> top 20

Stage 1: yt-dlp --flat-playlist over search URLs with sp= filters (sort=views).
Stage 2: yt-dlp --skip-download metadata for the union of candidates (cached in candidates_meta.jsonl).
Outputs: candidates_flat.jsonl, candidates_meta.jsonl, ranked_long.tsv, ranked_short.tsv
"""
import json, os, re, subprocess, sys, datetime as dt
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
YTDLP = os.path.join(HERE, "..", "..", "..", "venv", "bin", "yt-dlp")
TODAY = dt.date(2026, 8, 19)

QUERIES = [
    "chocolate chip cookies", "chocolate chip cookie recipe", "best chocolate chip cookies",
    "chewy chocolate chip cookies", "brown butter chocolate chip cookies",
    "crispy chocolate chip cookies", "gooey chocolate chip cookies", "soft chocolate chip cookies",
    "bakery style chocolate chip cookies", "perfect chocolate chip cookies",
    "easy chocolate chip cookies", "chocolate chip cookies asmr", "thick chocolate chip cookies",
    "levain chocolate chip cookies", "nyc chocolate chip cookies", "chocolate chip cookie hack",
]
# sp params (base64 of protobuf): CAM = sort by view count; SBAgF = upload this year;
# GAE = duration <4 min; GAM = duration 4-20 min
SP = {
    "views_year_under4": "CAMSBAgFGAE%253D",
    "views_year_4to20": "CAMSBAgFGAM%253D",
    "views_under4_alltime": "CAMSAhgB",
}
TOPIC = re.compile(r"(choc(olate)?[\s\-]*chip|chocolate chunk|cookie)", re.I)


def flat_search(query, sp, n=60):
    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}&sp={sp}"
    r = subprocess.run([YTDLP, "--flat-playlist", "--playlist-end", str(n), "-J", url],
                       capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
    except Exception:
        return []
    out = []
    for e in d.get("entries") or []:
        if not e or not e.get("id"):
            continue
        out.append(dict(id=e["id"], title=e.get("title"), channel=e.get("channel") or e.get("uploader"),
                        view_count=e.get("view_count"), duration=e.get("duration"),
                        url=e.get("url"), q=query, sp=sp))
    return out


def fetch_meta(vid):
    fields = ["id", "title", "channel", "channel_id", "channel_follower_count", "upload_date",
              "duration", "view_count", "like_count", "comment_count", "width", "height",
              "webpage_url", "categories", "tags", "description", "chapters", "thumbnail", "language",
              "availability", "age_limit", "live_status", "was_live", "aspect_ratio"]
    r = subprocess.run([YTDLP, "--skip-download", "--no-playlist", "-J",
                        f"https://www.youtube.com/watch?v={vid}"], capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
    except Exception:
        d = None
    if not isinstance(d, dict):
        return dict(id=vid, error=(r.stderr or "")[-300:])
    m = {k: d.get(k) for k in fields}
    m["description"] = (m.get("description") or "")[:1500]
    m["tags"] = (m.get("tags") or [])[:30]
    return m


def main():
    flat_path = os.path.join(HERE, "candidates_flat.jsonl")
    meta_path = os.path.join(HERE, "candidates_meta.jsonl")
    # ---- stage 1
    if not os.path.exists(flat_path):
        jobs = [(q, sp) for q in QUERIES for sp in SP.values()]
        jobs += [(q + " #shorts", SP["views_under4_alltime"]) for q in QUERIES[:8]]
        rows = []
        with ThreadPoolExecutor(max_workers=6) as ex:
            for res in ex.map(lambda j: flat_search(*j), jobs):
                rows.extend(res)
        with open(flat_path, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        print(f"stage1: {len(rows)} rows, {len({r['id'] for r in rows})} unique ids")
    rows = [json.loads(l) for l in open(flat_path)]
    # topic filter on title + de-dup, keep best-known view count
    byid = {}
    for r in rows:
        if not TOPIC.search(r.get("title") or ""):
            continue
        cur = byid.get(r["id"])
        if cur is None or (r.get("view_count") or 0) > (cur.get("view_count") or 0):
            byid[r["id"]] = r
    # candidate set: long = dur<600 & views>=100k ; short = dur<=180 & views>=300k (generous; verify in stage 2)
    cand = [r for r in byid.values() if r.get("duration") and (
        (r["duration"] < 600 and (r.get("view_count") or 0) >= 100_000)
    )]
    cand.sort(key=lambda r: -(r.get("view_count") or 0))
    print(f"topic-filtered unique: {len(byid)}, candidates for meta fetch: {len(cand)}")
    # ---- stage 2
    have = {}
    if os.path.exists(meta_path):
        for l in open(meta_path):
            m = json.loads(l); have[m["id"]] = m
    todo = [r["id"] for r in cand if r["id"] not in have]
    print(f"meta: cached {len(have)}, fetching {len(todo)}")
    with ThreadPoolExecutor(max_workers=8) as ex, open(meta_path, "a") as f:
        for m in ex.map(fetch_meta, todo):
            f.write(json.dumps(m) + "\n"); f.flush(); have[m["id"]] = m
    # ---- rank
    def d(s):
        return dt.date(int(s[:4]), int(s[4:6]), int(s[6:8])) if s else None
    longs, shorts = [], []
    for m in have.values():
        if m.get("error") or not m.get("upload_date") or not m.get("duration"):
            continue
        if not TOPIC.search(m.get("title") or ""):
            continue
        age = (TODAY - d(m["upload_date"])).days
        vertical = (m.get("height") or 0) > (m.get("width") or 0)
        if vertical and m["duration"] <= 180 and age <= 730:
            shorts.append(m)
        elif (not vertical) and m["duration"] < 600 and age <= 365:
            longs.append(m)
    longs.sort(key=lambda m: -(m.get("view_count") or 0))
    shorts.sort(key=lambda m: -(m.get("view_count") or 0))
    for name, lst in (("ranked_long.tsv", longs), ("ranked_short.tsv", shorts)):
        with open(os.path.join(HERE, name), "w") as f:
            f.write("rank\tid\tviews\tdur_s\tupload\tw\th\tsubs\tchannel\ttitle\n")
            for i, m in enumerate(lst, 1):
                f.write("\t".join(str(x) for x in [i, m["id"], m.get("view_count"), m["duration"],
                        m["upload_date"], m.get("width"), m.get("height"), m.get("channel_follower_count"),
                        m.get("channel"), (m.get("title") or "").replace("\t", " ")]) + "\n")
        print(f"{name}: {len(lst)} rows")
        for i, m in enumerate(lst[:25], 1):
            print(f"  {i:2d} {m['id']} {m.get('view_count'):>10} {m['duration']:>4}s {m['upload_date']} "
                  f"{(m.get('channel') or '')[:22]:22} | {(m.get('title') or '')[:70]}")


if __name__ == "__main__":
    main()
