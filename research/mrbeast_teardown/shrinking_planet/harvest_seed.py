"""Harvest downloaded per-shot seed stills (~/Downloads/<shot>.png) into assets/shrinking_planet/seeds/ + ledger. Usage: harvest_seed.py S002 S005 ..."""
import json,hashlib,os,shutil,sys
from PIL import Image
S='research/mrbeast_teardown/shrinking_planet'; D='assets/shrinking_planet/seeds'; L=f'{D}/SEEDS_0-3min.json'
led=json.load(open(L)); p={x['shot']:x for x in json.load(open(f'{S}/seed_stills_prompts_0-3min.json'))}
for sid in sys.argv[1:]:
    src=os.path.expanduser(f'~/Downloads/{sid}.png'); dst=f'{D}/{sid}.png'
    if not os.path.exists(src): print(sid,'MISSING in Downloads'); continue
    shutil.copy(src,dst); im=Image.open(dst)
    led['seeds'][sid]={"file":dst,"sha256":hashlib.sha256(open(dst,'rb').read()).hexdigest(),"size":list(im.size),"prompt":p[sid]['send_text'],"status":"GEN"}
    print(sid,im.size,os.path.getsize(dst))
json.dump(led,open(L,'w'),indent=1); print('ledger',len(led['seeds']),'/',len(p))
