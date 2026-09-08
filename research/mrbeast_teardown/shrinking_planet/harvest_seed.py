"""Harvest downloaded per-shot seed stills (~/Downloads/<shot>.png) into assets/shrinking_planet/seeds/ + ledger. Usage: harvest_seed.py S002 S005 ..."""
import json,hashlib,os,shutil,sys,glob
from PIL import Image
S='research/mrbeast_teardown/shrinking_planet'; D='assets/shrinking_planet/seeds'; L=f'{D}/SEEDS_0-3min.json'
led=json.load(open(L)); p={x['shot']:x for x in json.load(open(f'{S}/seed_stills_prompts_0-3min.json'))}
for sid in sys.argv[1:]:
    cands=sorted(glob.glob(os.path.expanduser(f'~/Downloads/{sid}*.png')),key=os.path.getmtime); dst=f'{D}/{sid}.png'
    if not cands: print(sid,'MISSING in Downloads'); continue
    src=cands[-1]; old=led['seeds'].get(sid,{}).get('sha256')
    shutil.copy(src,dst); im=Image.open(dst)
    prev=led['seeds'].get(sid,{}); led['seeds'][sid]={"file":dst,"regen_of_sha":old if old else None,"history":prev.get("history",[])+([prev.get("verdict")] if prev.get("verdict") else []),"sha256":hashlib.sha256(open(dst,'rb').read()).hexdigest(),"size":list(im.size),"prompt":p[sid]['send_text'],"status":"GEN"}
    print(sid,im.size,os.path.getsize(dst))
json.dump(led,open(L,'w'),indent=1); print('ledger',len(led['seeds']),'/',len(p))
