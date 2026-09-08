import json, sys, collections
from masters import ART_STYLE, ANCHORS, NEG, build_masters, PLANET_FOR
import shots_hook_a1, shots_a2_a3, shots_a4_a5
OUT="/Users/jefflawrence/Documents/youtube-automation-production/research/mrbeast_teardown/shrinking_planet"
LADDER={"1":1000,"2":1000,"5":500,"6":500,"10":300,"12":300,"14":300,"15":300,"16":300,"20":25,"25":20,"26":12,"27":7,"28":4,"29":2,"30":2}
# beat: (t_in, t_out, day, title, act)
BEATS=[("B01","00:00","00:12",1,"Cold open","HOOK"),("B02","00:12","00:17",1,"Silent hold","HOOK"),("B03","00:17","00:21",1,"The wound","HOOK"),
("B04","00:21","00:30",1,"Anklets lock","HOOK"),("B05","00:30","00:45",1,"Red line + orbit pull-out","HOOK"),
("B06","00:45","01:30",1,"Planet tour","A1"),("B07","01:30","02:00",1,"Confessionals + flash-forward","A1"),("B08","02:00","02:45",2,"The engine","A1"),
("B09","02:45","03:30",5,"Day 5 · Offer #1","A1"),("B10","03:30","04:10",5,"The wedge","A1"),("B11","04:10","04:50",6,"It bites","A1"),
("B12","04:50","05:40",6,"The first fight","A1"),("B13","05:40","06:20",6,"The truce","A1"),
("B14","06:20","07:05",10,"Day 10 · free shrink + heart","A2"),("B15","07:05","07:40",12,"The talk (i)","A2"),("B16","07:40","08:15",12,"The talk (ii)","A2"),
("B17","08:15","08:45",14,"GRUFF's lap","A2"),("B18","08:45","09:45",15,"Day 15 · the dome refused","A2"),("B19","09:45","10:25",16,"Breakfast + the book","A2"),("B20","10:25","10:55",16,"The goggle","A2"),
("B21","10:55","11:30",20,"Day 20 · five platters","A3"),("B22","11:30","12:00",20,"Platter four","A3"),("B23","12:00","12:25",20,"The crate opens","A3"),("B24","12:25","12:45",20,"The cost","A3"),("B25","12:45","13:30",25,"Day 25 · the flip","A3"),
("B26","13:30","14:20",25,"The truth beam (i)","A4"),("B27","14:20","15:10",25,"The truth beam (ii)","A4"),("B28","15:10","15:40",25,"GRUFF at the pod","A4"),("B29","15:40","16:05",26,"Day 26 · soundproof pods","A4"),
("B30","16:05","16:25",27,"Day 27 · three-legged race","A4"),("B31","16:25","17:10",28,"Day 28 · taller than the world","A4"),("B32","17:10","17:55",29,"24 hours left · the secret","A4"),
("B33","17:55","18:35",29,"Night doubt","A4"),("B34","18:35","19:30",30,"The clock","A5"),("B35","19:30","19:55",30,"Half each + the riff","A5"),("B36","19:55","20:00",30,"Band's back","A5")]
OLD2NEW={"B01":"B01","B02":"B02","B03":"B03","B04":"B04","B05":"B05","B06":"B06","B07":"B07","B08":"B08","B10":"B11","B12":"B14","B14":"B17","B15":"B18","B16":"B19","B17":"B20","B19":"B23","B20":"B24","B21":"B25","B23":"B28","B24":"B29","B25":"B30","B26":"B31","B27":"B32","B28":"B33","B29":"B34","B30":"B35","B31":"B36"}
SPLIT={"B09":("B09","B10",{"wedge_shear_hero","camp_drifts_away_pov","count_front_update","planet_500_aftermath","gruff_watch_wedge"}),
       "B11":("B12","B13",{"truce_ration_insert","gruff_conf_B"}),
       "B13":("B15","B16",{"starfield_timelapse","pip_cu_firelit_B","vent_2shot_backs"}),
       "B18":("B21","B22",{"reveal_platter4","stunned_2shot","wedge_big_hero_ground","count_rotate"}),
       "B22":("B26","B27",{"count_malfunction","beam_strobe_ots","pip_cu_ask_beam","gruff_ms_beam_flicker","beam_split_2shot","orb_cu_withhold"})}
BEAT={b[0]:b for b in BEATS}
def sec(t): m,s=t.split(":"); return int(m)*60+int(s)
def tc(x): return f"{x//60:02d}:{x%60:02d}"
raw0=shots_hook_a1.SHOTS+shots_a2_a3.SHOTS+shots_a4_a5.SHOTS
from shots_extra import EXTRA
raw=[]
for r in raw0:
    raw.append(r)
    if r["key"] in EXTRA: raw.extend(EXTRA[r["key"]])
# mouth cap: only shots where a mouth:ON line lands
for r in raw:
    if r["key"]=="pip_cu_surprise": r["mouth"]=[]
    if r["ins"] in ("pip_cu_laugh","pip_cu_surprise","pip_cu_halve_it"): r["mouth"]=[]
# remap beats (31-beat authoring -> 36-beat gate layout)
for r in raw:
    b=r["beat"]
    if b in SPLIT:
        a_,b_,second=SPLIT[b]
        k=r["key"] or r["ins"]
        if r["ins"]=="pip_cu_halve_it": r["beat"]=b_
        elif r["ins"]=="pip_cry_cu": r["beat"]=b_
        elif r["ins"]=="pip_cu_beam": r["beat"]=b_
        elif r["ins"]=="pip_react_flip": r["beat"]=b_
        else: r["beat"]=b_ if k in second else a_
    else: r["beat"]=OLD2NEW[b]
# assign ids, keys
key2id={}; shots=[]
for i,r in enumerate(raw,1):
    sid=f"S{i:03d}"; r["id"]=sid
    if r["key"]: key2id[r["key"]]=sid
# time allocation per beat (proportional to duration weights)
by_beat=collections.defaultdict(list)
for r in raw: by_beat[r["beat"]].append(r)
for b,(bid,ti,to,day,title,act) in BEAT.items():
    lst=by_beat[bid]; T0,T1=sec(ti),sec(to); span=T1-T0
    w=[r["dur"] for r in lst]; tot=sum(w); acc=T0; edges=[T0]
    for k,r in enumerate(lst):
        acc=T0+round(span*sum(w[:k+1])/tot); edges.append(acc)
    n=len(lst); assert span>=n,(bid,span,n)
    for k in range(1,n+1): edges[k]=max(edges[k],edges[k-1]+1)
    edges[n]=T1
    for k in range(n-1,0,-1): edges[k]=min(edges[k],edges[k+1]-1)
    for k,r in enumerate(lst): r["t_in"],r["t_out"]=tc(edges[k]),tc(edges[k+1])
def top_ids(seeds,chars):
    ids=[]
    for m in seeds:
        t=m
        for c in ("PIP","GRUFF","ORB","COUNT"):
            if m.startswith("M_"+c+"_"): t="M_"+c
        if t not in ids: ids.append(t)
    for c in chars:
        if "M_"+c not in ids: ids.append("M_"+c)
    return ids
errors=[]
prev=None; out=[]
comp=0
for r in raw:
    bid,ti,to,day,title,act=BEAT[r["beat"]]
    pm=LADDER[str(day)]
    reuse="insert" if r["ins"] else "unique"
    src=key2id.get(r["ins"]) if r["ins"] else None
    if r["ins"] and not src: errors.append(f"{r['id']} insert key missing {r['ins']}")
    if reuse=="unique":
        comp+=1; cid=f"C{comp:03d}"
    else:
        cid=next(x["composite_seed_id"] for x in out if x["id"]==src)
    d=dict(id=r["id"],beat=r["beat"],act=act,t_in=r["t_in"],t_out=r["t_out"],day=day,planet_m=pm,count_display=pm,
           characters=r["chars"],set=r["set"],vantage=r["vantage"],seed_masters=top_ids(r["seeds"],r["chars"]),seed_views=r["seeds"],composite_seed_id=cid,
           shot_type=r["stype"],i2v_prompt=(r["prompt"] if reuse=="unique" else f"REUSE of {src} (same clip; re-crop/re-grade in FFmpeg only, no new generation)"),
           duration_s=r["dur"],reuse=reuse,loops=r["loops"],mouth_visible=r["mouth"])
    if src: d["insert_of"]=src
    # continuity note for macros/replays whose seed planet differs
    seedplanets=[m for m in r["seeds"] if m.startswith("M_PLANET_")]
    want=PLANET_FOR[pm]
    if seedplanets and want not in seedplanets:
        d["continuity_note"]=("replay/flashback clip — planet size on screen is the source day's" if "replay" in r["vantage"] or "re-use" in r["vantage"] else "planet not visible in frame (macro/re-crop)")
    if r["set"]=="orbit" and reuse=="unique" and want not in r["seeds"]: errors.append(f"{r['id']} orbit shot missing planet master {want}")
    if r["set"]!="orbit" and reuse=="unique" and pm>=300 and not any(s.startswith("M_SET_") for s in r["seeds"]) and not seedplanets: errors.append(f"{r['id']} no set/planet master")
    # adjacency rules
    if prev:
        if prev["vantage"]==d["vantage"]: errors.append(f"{d['id']} adjacent identical vantage: {d['vantage']}")
        if d["reuse"]=="insert" and (prev.get("insert_of")==src or prev["id"]==src): errors.append(f"{d['id']} insert adjacent to itself/source {src}")
        if prev["reuse"]=="insert" and prev.get("insert_of")==d["id"]: errors.append("impossible")
        if sec(d["t_in"])<sec(prev["t_out"]): errors.append(f"{d['id']} time overlap {prev['t_out']}>{d['t_in']}")
    if d["count_display"]!=d["planet_m"] or d["planet_m"]!=LADDER[str(day)]: errors.append(f"{d['id']} ladder mismatch")
    if sec(d["t_out"])<=sec(d["t_in"]): errors.append(f"{d['id']} zero-length {d['t_in']} {d['t_out']}")
    if d["duration_s"]>10: errors.append(f"{d['id']} >10s")
    out.append(d); prev=d
# beat coverage
for b in BEAT:
    if not by_beat[b]: errors.append(f"beat {b} has no shot")
uniq=[s for s in out if s["reuse"]=="unique"]; ins=[s for s in out if s["reuse"]=="insert"]
mouth=[s for s in uniq if "PIP" in s["mouth_visible"]]
mouth_all=[s for s in out if "PIP" in s["mouth_visible"]]
peract=collections.Counter(s["act"] for s in uniq)
# day monotonic
days=[BEAT[b][3] for b in [x[0] for x in BEATS]]
assert days==sorted(days)
masters=build_masters()
mids={m["id"] for m in masters}|{v["id"] for m in masters if m["kind"]=="character" for v in m["views"]}
for s in out:
    for m in s["seed_views"]:
        if m not in mids: errors.append(f"{s['id']} unknown master {m}")
    for m in s["seed_masters"]:
        if m not in {x["id"] for x in masters}: errors.append(f"{s['id']} unknown top master {m}")
print("shots",len(out),"unique",len(uniq),"inserts",len(ins),"PIP mouth unique",len(mouth),"all",len(mouth_all))
print("per act",dict(peract))
print("ERRORS",len(errors)); [print(" ",e) for e in errors]
manifest={"title":"Shrinking Planet","version":"v1","source_of_truth":"research/mrbeast_teardown/SHRINKING_PLANET_bible_v2.html",
 "art_style":ART_STYLE,"identity_anchors":ANCHORS,"negative_constraints":NEG,
 "ladder":LADDER,
 "ladder_notes":"Rungs from the bible (Day 1/5/10/20/25/26/27/28/29/30). Intermediate story days (2,6,12,14,15,16) carry the unchanged planet size so count_display == planet_m == ladder[day] holds on every shot. 20 m and 7 m are re-crops of the 25 m and 12 m masters.",
 "characters":{
  "ORB":{"role":"host","design":ANCHORS["ORB"],"speech":"halo pulse (brightness keyframe in FFmpeg); never lip-sync","master":"M_ORB","views":["M_ORB_front","M_ORB_3q","M_ORB_expr"],"colour_code":"chrome + gold","mouth":"none"},
  "PIP":{"role":"contestant (went solo)","design":ANCHORS["PIP"],"speech":"small mouth; mouth-visible lines capped at 20, rest VO on reactions","master":"M_PIP","views":["M_PIP_front","M_PIP_3q","M_PIP_expr"],"colour_code":"magenta","emote":"fronds: droop=sad, flare=angry, curl=playful"},
  "GRUFF":{"role":"contestant (got left)","design":ANCHORS["GRUFF"],"speech":"fur movement + brows; mouth never visible","master":"M_GRUFF","views":["M_GRUFF_front","M_GRUFF_3q","M_GRUFF_expr"],"colour_code":"cyan","plot_object":"cracked brass goggle (forehead)"},
  "COUNT":{"role":"scoreboard","design":ANCHORS["COUNT"],"speech":"beeps only; digits composited over blank display plates","master":"M_COUNT","views":["M_COUNT_front","M_COUNT_3q","M_COUNT_expr"],"colour_code":"black + red","rule":"inserts only, never adjacent to itself"}},
 "seed_masters":masters,
 "rules":{"unique_target":176,"adjacent_vantage_must_differ":True,"inserts_never_adjacent_to_self":True,"pip_mouth_visible_cap":20,"default_duration_s":6,"hero_max_duration_s":10},
 "totals":{"shots":len(out),"unique":len(uniq),"inserts":len(ins),"unique_per_act":dict(peract),"pip_mouth_visible_shots":len(mouth_all),"beats":len(BEATS)},
 "shots":out}
json.dump(manifest,open(OUT+"/shot_manifest_v1.json","w"),indent=1)
json.dump({"errors":errors},open("/private/tmp/claude-501/-Users-jefflawrence-Documents-youtube-automation-production/51043878-27a8-418b-9e48-7eded56b9566/scratchpad/sp/errors.json","w"))
