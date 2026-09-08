import re, json, collections
OUT="/Users/jefflawrence/Documents/youtube-automation-production/research/mrbeast_teardown/shrinking_planet"
man=json.load(open(OUT+"/shot_manifest_v1.json"))
LADDER=man["ladder"]; shots=man["shots"]
src=open(OUT+"/SCRIPT_v1.md").read().split("\n")
def sec(t): m,s=t.split(":"); return int(m)*60+int(s)
def tc(x): return f"{x//60:02d}:{x%60:02d}"
beats=[]; cur=None; lines=[]; errs=[]
hdr=re.compile(r"^## (B\d{2}) \[(\d\d:\d\d)-(\d\d:\d\d)\] (.+)$")
tag=re.compile(r"^\[(DAY|PLANET|COUNT|LOOP|TEXT|MUSIC|SFX|FLASHFWD|TIMER)\b(.*)\]$")
dlg=re.compile(r"^\*\*(PIP|GRUFF|ORB)\*\* \(([^)]*)\): (.+)$")
for ln in src:
    m=hdr.match(ln)
    if m:
        cur={"beat":m.group(1),"t_in":m.group(2),"t_out":m.group(3),"title":m.group(4),"tags":[],"lines":[]}; beats.append(cur); continue
    if cur is None: continue
    m=tag.match(ln.strip())
    if m: cur["tags"].append((m.group(1),m.group(2).strip())); continue
    m=dlg.match(ln.strip())
    if m:
        spk,attrs,text=m.groups()
        mouth=None
        if spk=="PIP":
            mm=re.search(r"mouth:(ON|OFF)",attrs); 
            if not mm: errs.append(f"{cur['beat']} PIP line without mouth field: {text[:30]}")
            else: mouth=mm.group(1)
        else:
            if "mouth" in attrs: errs.append(f"{cur['beat']} {spk} line has mouth field")
            if not re.match(r"^(vo|on),",attrs): errs.append(f"{cur['beat']} {spk} attrs bad: {attrs}")
        cur["lines"].append({"speaker":spk,"mouth":mouth,"text":text})
# validations
prev_day=0
mshots=collections.defaultdict(list)
for s in shots: mshots[s["beat"]].append(s)
man_beats={s["beat"] for s in shots}
if [b["beat"] for b in beats]!=[f"B{i:02d}" for i in range(1,37)]: errs.append("beat sequence not B01..B31")
for b in beats:
    d=dict(b["tags"]); tags=collections.defaultdict(list)
    for k,v in b["tags"]: tags[k].append(v)
    for k in ("DAY","PLANET","COUNT"):
        if len(tags[k])!=1: errs.append(f"{b['beat']} needs exactly one [{k}]")
    day=int(tags["DAY"][0]); pl=int(tags["PLANET"][0]); ct=int(tags["COUNT"][0])
    if day<prev_day: errs.append(f"{b['beat']} day regresses"); 
    prev_day=day
    if not(pl==ct==LADDER[str(day)]): errs.append(f"{b['beat']} PLANET/COUNT/ladder mismatch {pl} {ct} {LADDER.get(str(day))}")
    ms=mshots[b["beat"]]
    if not ms: errs.append(f"{b['beat']} no shots")
    for s in ms:
        if s["day"]!=day or s["planet_m"]!=pl: errs.append(f"{s['id']} manifest day/planet differs from script {s['day']}/{s['planet_m']} vs {day}/{pl}")
        if (s["t_in"],)!=(s["t_in"],): pass
    if ms and (ms[0]["t_in"]!=b["t_in"] or ms[-1]["t_out"]!=b["t_out"]): errs.append(f"{b['beat']} manifest span {ms[0]['t_in']}-{ms[-1]['t_out']} vs script {b['t_in']}-{b['t_out']}")
    for v in tags["LOOP"]:
        if not re.match(r"^\w+ (OPEN|FEED|PAY)$",v): errs.append(f"{b['beat']} bad LOOP tag {v}")
    on=[l for l in b["lines"] if l["mouth"]=="ON"]
    mv=[s for s in ms if "PIP" in s["mouth_visible"]]
    if len(on)>len(mv): errs.append(f"{b['beat']} {len(on)} PIP mouth:ON lines but only {len(mv)} mouth-visible shots")
    if mv and not on: errs.append(f"{b['beat']} mouth-visible shot(s) {[s['id'] for s in mv]} but no PIP mouth:ON line")
# loop lifecycle
loops=collections.defaultdict(list)
for b in beats:
    for k,v in b["tags"]:
        if k=="LOOP": i,st=v.split(); loops[i].append((b["beat"],st))
for i,seq in loops.items():
    sts=[s for _,s in seq]
    if sts[0]!="OPEN": errs.append(f"loop {i} does not start OPEN")
    if sts[-1]!="PAY": errs.append(f"loop {i} never PAYs")
# script lines json with interpolated t
out=[]
for b in beats:
    n=len(b["lines"]); T0,T1=sec(b["t_in"]),sec(b["t_out"])
    for k,l in enumerate(b["lines"]):
        t=T0+int((T1-T0)*k/max(n,1))
        out.append({"beat":b["beat"],"t":tc(t),"speaker":l["speaker"],"mouth":l["mouth"],"words":len(l["text"].split()),"text":l["text"]})
json.dump(out,open(OUT+"/script_lines_v1.json","w"),indent=1,ensure_ascii=False)
tot=collections.Counter(); wc=collections.Counter()
for l in out: tot[l["speaker"]]+=1; wc[l["speaker"]]+=l["words"]
pip_on=sum(1 for l in out if l["mouth"]=="ON")
print("lines",len(out),"PIP ON",pip_on,"per speaker",dict(tot),"words",dict(wc),sum(wc.values()))
print("loops",{k:[f'{b}:{s}' for b,s in v] for k,v in loops.items()})
print("ERRORS",len(errs)); [print(" ",e) for e in errs]

# ---------- SEED_PROMPTS_v1.md ----------
M=man["seed_masters"]
L=[]; w=L.append
w("# SHRINKING PLANET — Seed Prompt Pack v1 (23 masters)\n")
w("Gate 1 deliverable: image-gen prompts for the 23 approved masters. Every prompt carries the locked art-style paragraph verbatim, the fixed identity anchors, and the negative constraints. One seed per character is chosen from these; files are frozen with hashes; every later composite derives from them. Source: `SHRINKING_PLANET_bible_v2.html`.\n")
w("## Locked art style (verbatim in every prompt)\n"); w("> "+man["art_style"]+"\n")
w("## Identity anchors (fixed, never vary across the 30 days)\n")
for k,v in man["identity_anchors"].items(): w(f"- **{k}** — {v}")
w("\n## Negative constraints (verbatim in every prompt)\n"); w("> "+man["negative_constraints"]+"\n")
w("## Master index\n")
w("| # | id | kind | notes |\n|---|---|---|---|")
for i,m in enumerate(M,1): w(f"| {i} | `{m['id']}` | {m['kind']} | {m['notes'].replace('|','/')} |")
w("\n*Planet classes: 1000 / 500 / 300 / 25 / 12 / 4 / 2 m. The 20 m (Day 25) and 7 m (Day 27) planets are re-crops of the 25 m and 12 m masters — no separate generation.*\n")
sections=[("character","Characters (4 masters × 3 views)"),("planet","Planet-size masters (7)"),("set","Set masters (6)"),("archive","Archive band stills (6)")]
for kind,title in sections:
    w(f"\n---\n\n# {title}\n")
    for m in M:
        if m["kind"]!=kind: continue
        w(f"\n## {m['id']}\n")
        w(f"*{m['notes']}*\n")
        if kind=="character":
            for v in m["views"]:
                w(f"\n### {v['id']} ({v['view']})\n"); w("```text\n"+v["prompt"]+"\n```")
        else:
            w("```text\n"+m["prompt"]+"\n```")
# usage table
use=collections.Counter()
for s in shots:
    for sm in s["seed_masters"]: use[sm]+=1
w("\n---\n\n# Master usage across the shot manifest\n")
w("| master / view | shots referencing |\n|---|---|")
for k,v in sorted(use.items(), key=lambda x:-x[1]): w(f"| `{k}` | {v} |")
open(OUT+"/SEED_PROMPTS_v1.md","w").write("\n".join(L)+"\n")

# ---------- CONTINUITY_LEDGER_v1.md ----------
C=[]; c=C.append
c("# SHRINKING PLANET — Continuity Ledger v1\n")
c("Deterministic facts every shot must agree with. Generated from `shot_manifest_v1.json` + `SCRIPT_v1.md`; regenerate, never hand-edit.\n")
c("## Planet ladder (day → metres). THE COUNT displays exactly this number.\n")
c("| day | planet m | COUNT | master | beats |\n|---|---|---|---|---|")
bd=collections.defaultdict(list)
for b in beats:
    d=dict(b["tags"]); bd[int(d["DAY"])].append(b["beat"])
from masters import PLANET_FOR
for d in sorted(int(k) for k in LADDER):
    pm=LADDER[str(d)]; mid=PLANET_FOR[pm]; rc=" (re-crop)" if pm in (20,7) else ""
    c(f"| {d} | {pm} | {pm} | `{mid}`{rc} | {', '.join(bd.get(d,[]))} |")
c("\n## Fixed identity (no costume changes across 30 days)\n")
for k,v in man["identity_anchors"].items(): c(f"- **{k}**: {v}")
c("\n## Devices (kept separate — no rule collision)\n- **Red ring on the landing pad** = QUIT line (B05). Crossing it ends the game for both.\n- **Escape pod launch key + red lever/door** = STEAL device (B21 → B29). One seat, whole prize.\n- **Crate** on the equator: sealed until Day 20 (B06 OPEN → B15 FEED → B19 PAY).\n- **Goggle**: cracked brass, forehead, never removed (B17 OPEN → B27 PAY). Only ever worn DOWN in archive still `M_ARCH_02_stage_drums`.\n- **Truth beam**: PIP verified GREEN twice; GRUFF UNVERIFIED (B22) — replayed red at B29.\n- **Riff**: four-note ukulele motif (B16 OPEN → B30 PAY on a ration tin).\n")
c("## Open loops\n")
c("| loop | sequence |\n|---|---|")
for i,seq in loops.items(): c(f"| {i} | "+" → ".join(f"{b} {s}" for b,s in seq)+" |")
c("\n## PIP mouth-visible shots (cap 20)\n")
c("| shot | beat | t | line it carries |\n|---|---|---|---|")
onl=collections.defaultdict(list)
for l in out:
    if l["mouth"]=="ON": onl[l["beat"]].append(l["text"])
for s in shots:
    if "PIP" in s["mouth_visible"]:
        q=onl[s["beat"]]; txt=q.pop(0) if q else "(re-use — same line)"
        c(f"| {s['id']} | {s['beat']} | {s['t_in']} | {txt} |")
c(f"\nTotal: {sum(1 for s in shots if 'PIP' in s['mouth_visible'])} shots / {pip_on} mouth:ON lines.\n")
c("## Shots whose seed planet differs from the day's planet (allowed: macro / re-crop / replay)\n")
c("| shot | beat | day | planet | seeds | note |\n|---|---|---|---|---|---|")
for s in shots:
    if "continuity_note" in s: c(f"| {s['id']} | {s['beat']} | {s['day']} | {s['planet_m']} | {', '.join(m for m in s['seed_masters'] if m.startswith('M_PLANET'))} | {s['continuity_note']} |")
c("\n## Insert re-use counts (≤3 non-adjacent uses each)\n")
ic=collections.Counter(s["insert_of"] for s in shots if s["reuse"]=="insert")
c("| source shot | vantage | re-uses |\n|---|---|---|")
byid={s["id"]:s for s in shots}
for k,v in ic.most_common(): c(f"| {k} | {byid[k]['vantage']} | {v} |")
c("\n## Sets by shot count\n")
sc=collections.Counter(s["set"] for s in shots)
c("| set | shots |\n|---|---|"); [c(f"| {k} | {v} |") for k,v in sc.most_common()]
c("\n## Per-beat shot table\n")
c("| beat | span | day | m | shots (unique+insert) | PIP mouth |\n|---|---|---|---|---|---|")
for b in beats:
    ms=mshots[b["beat"]]; u=sum(1 for s in ms if s["reuse"]=="unique"); i=len(ms)-u
    c(f"| {b['beat']} {b['title']} | {b['t_in']}-{b['t_out']} | {ms[0]['day']} | {ms[0]['planet_m']} | {u}+{i} | {sum(1 for s in ms if 'PIP' in s['mouth_visible'])} |")
open(OUT+"/CONTINUITY_LEDGER_v1.md","w").write("\n".join(C)+"\n")
print("wrote prompts + ledger")
