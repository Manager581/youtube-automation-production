import csv,re,json
rows=list(csv.reader(open("STORYBOARD.tsv"),delimiter='\t'))
hdr=rows[0]
def ix(n): return hdr.index(n)
sc,sh,ct,ip,st,beat=ix("Scene"),ix("Shot"),ix("Clip type"),ix("Image prompt (still)"),ix("Status"),ix("Beat")
CH={
"[DEE]":"Dee the host (first-person POV; if visible only his tanned forearm/hand, a 30s man in a grey t-shirt)",
"[MAYA]":"Maya (28, warm brown skin, curly dark shoulder-length hair, white tee, denim shorts, green crossbody bag)",
"[RANGER TOM]":"Ranger Tom (40s white man, short greying beard, khaki DINOVERSE ranger uniform with round embroidered patch and cap, lanyard)",
"[LENA]":"Lena (early 20s, light-brown hair in a ponytail, khaki DINOVERSE polo)",
"[OMEGA REX]":"Omega Rex (massive unnatural hybrid theropod, charcoal-grey hide with faint glowing orange seams, oversized jaws, six-clawed hands, asymmetric armored back, menacing and wrong-proportioned)",
"[CROWD]":"generic casual tourists in summer clothes",
}
def expand(p):
    for k,v in CH.items(): p=p.replace(k,v)
    return p
out=[]
for r in rows[1:]:
    if r[ct]=="GEN" and r[st]!="still":
        out.append({"scene":r[sc],"shot":r[sh],"beat":r[beat],"prompt":expand(r[ip])})
json.dump(out,open("work/remaining_prompts.json","w"),indent=1)
print("remaining GEN to generate:",len(out))
# list scenes
from collections import OrderedDict
scenes=OrderedDict()
for o in out: scenes.setdefault(o["scene"],[]).append(o["shot"])
for s,shots in scenes.items(): print(f"  {s}: {shots}")
