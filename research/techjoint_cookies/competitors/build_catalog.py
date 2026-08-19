#!/usr/bin/env python3
"""Build catalog.tsv / catalog.json for the downloaded competitor sets from yt-dlp info.json files
(+ metrics_*.tsv from analyze_competitors.py when present)."""
import csv, glob, json, os, re, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SETS = {"long": os.path.join(ROOT, "footage", "techjoint_competitors.nosync", "long"),
        "short": os.path.join(ROOT, "footage", "techjoint_competitors.nosync", "short")}
TODAY = dt.date(2026, 8, 19)


def load_metrics(name):
    p = os.path.join(HERE, f"metrics_{name}.tsv")
    out = {}
    if os.path.exists(p):
        for r in csv.DictReader(open(p), delimiter="\t"):
            out[r["id"]] = r
    return out


def desc_signals(desc):
    d = desc or ""
    return dict(
        desc_len=len(d),
        recipe_in_desc=bool(re.search(r"(ingredients?|cups?|tbsp|tsp|grams?|\bg\b|°f|°c|oven|bake)", d, re.I)),
        affiliate=bool(re.search(r"amzn\.to|amazon\.com|affiliate|shopmy|ltk|liketk", d, re.I)),
        links=len(re.findall(r"https?://", d)),
        hashtags=len(re.findall(r"#\w+", d)),
        socials=bool(re.search(r"instagram|tiktok|facebook|@", d, re.I)),
        cta=bool(re.search(r"subscribe|like|comment|follow", d, re.I)),
    )


def main():
    rows = []
    for name, vdir in SETS.items():
        ids = [l.strip() for l in open(os.path.join(vdir, "ids.txt")) if l.strip()] if os.path.exists(os.path.join(vdir, "ids.txt")) else []
        met = load_metrics(name)
        for rank, vid in enumerate(ids, 1):
            ij = os.path.join(vdir, f"{vid}.info.json")
            if not os.path.exists(ij):
                rows.append(dict(set=name, rank=rank, id=vid, missing=True)); continue
            m = json.load(open(ij))
            up = m.get("upload_date") or ""
            age = (TODAY - dt.date(int(up[:4]), int(up[4:6]), int(up[6:8]))).days if up else None
            views = m.get("view_count") or 0
            r = dict(set=name, rank=rank, id=vid, title=m.get("title"), channel=m.get("channel"),
                     subs=m.get("channel_follower_count"), views=views, likes=m.get("like_count"),
                     comments=m.get("comment_count"), upload=up, age_days=age,
                     views_per_day=round(views / age) if age else None,
                     like_rate_pct=round(100 * (m.get("like_count") or 0) / views, 2) if views else None,
                     comment_per_10k=round(1e4 * (m.get("comment_count") or 0) / views, 1) if views else None,
                     dur=m.get("duration"), w=m.get("width"), h=m.get("height"), fps=m.get("fps"),
                     lang=m.get("language"), categories=",".join(m.get("categories") or []),
                     n_tags=len(m.get("tags") or []), tags=" | ".join((m.get("tags") or [])[:12]),
                     chapters=len(m.get("chapters") or []),
                     has_subs=bool(m.get("subtitles")), url=m.get("webpage_url"),
                     desc_head=(m.get("description") or "")[:400].replace("\n", " ⏎ "))
            r.update(desc_signals(m.get("description")))
            r.update({f"m_{k}": v for k, v in met.get(vid, {}).items() if k != "id"})
            rows.append(r)
    json.dump(rows, open(os.path.join(HERE, "catalog.json"), "w"), indent=1)
    cols = sorted({k for r in rows for k in r}, key=lambda k: (k not in ("set", "rank", "id", "title", "channel", "subs", "views", "upload", "dur"), k))
    with open(os.path.join(HERE, "catalog.tsv"), "w") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t", extrasaction="ignore")
        w.writeheader(); [w.writerow(r) for r in rows]
    for r in rows:
        if r.get("missing"): print(r["set"], r["rank"], r["id"], "MISSING"); continue
        print(f"{r['set']:5} #{r['rank']:2d} {r['id']} {r['views']:>10} v | {r['dur']:>4}s | subs {str(r['subs']):>8} | like {r['like_rate_pct']}% | {r['upload']} | {(r['channel'] or '')[:18]:18} | {(r['title'] or '')[:60]}")


if __name__ == "__main__":
    main()
