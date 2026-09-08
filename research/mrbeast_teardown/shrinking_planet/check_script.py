import re, json, sys
from collections import Counter, defaultdict
D='/Users/jefflawrence/Documents/youtube-automation-production/research/mrbeast_teardown/'
src=open(D+'shrinking_planet/SCRIPT_v1.md').read()
beat_re=re.compile(r'^## (B\d\d) \[(\d\d:\d\d)-(\d\d:\d\d)\] (.*)$',re.M)
line_re=re.compile(r'^\*\*(PIP|GRUFF|ORB)\*\* \(([^)]*)\): (.*)$')
def ts(s): m,sec=s.split(':'); return int(m)*60+int(sec)
beats=[(m.group(1),m.group(2),m.group(3),m.group(4),m.start()) for m in beat_re.finditer(src)]
lines=[]; words=Counter(); pip_on=0; tags=defaultdict(list); issues=[]
for i,(bid,t0,t1,title,pos) in enumerate(beats):
    end=beats[i+1][4] if i+1<len(beats) else len(src)
    body=src[pos:end]
    dl=[]
    for ln in body.split('\n'):
        m=line_re.match(ln)
        if m:
            sp,attr,txt=m.groups()
            mouth=None
            if sp=='PIP':
                mm=re.search(r'mouth:(ON|OFF)',attr); mouth=mm.group(1) if mm else 'MISSING'
                if mouth=='ON': pip_on+=1
            if 'emotion:' not in attr and 'energy:' not in attr: issues.append(f'{bid} no emotion: {ln[:50]}')
            w=len(re.findall(r"[A-Za-z0-9'’\-]+",txt))
            words[sp]+=w
            dl.append(dict(beat=bid,speaker=sp,mouth=mouth,words=w,text=txt,attr=attr))
        for tg in re.findall(r'^\[([A-Z]+)[ \]]',ln): tags[bid].append(tg)
    n=len(dl); a,b=ts(t0),ts(t1)
    for k,d in enumerate(dl):
        t=a+(b-a)*(k+0.5)/max(n,1); d['t']='%02d:%02d'%(t//60,t%60)
    lines+=dl
    dur=b-a
    ret=[x for x in tags[bid] if x in('FLASHFWD','TIMER','TEXT','MUSIC','LOOP')]
    if dur>60 and not any(x in tags[bid] for x in ('FLASHFWD','TIMER')): issues.append(f'{bid} {dur}s no TIMER/FLASHFWD')
    for req in ('DAY','PLANET','COUNT'):
        if req not in tags[bid]: issues.append(f'{bid} missing {req}')
# day/planet/count consistency
days=[]; 
for m in re.finditer(r'\[DAY (\d+)\]\n\[PLANET (\d+)\]\n\[COUNT (\d+)\]',src):
    d,p,c=map(int,m.groups()); days.append(d)
    if p!=c: issues.append(f'day {d} planet {p}!=count {c}')
if days!=sorted(days): issues.append('DAY not monotonic '+str(days))
tot=sum(words.values())
print('beats',len(beats),'lines',len(lines),'words',tot,{k:(v,round(v/tot*100,1)) for k,v in words.items()},'pip_on',pip_on, 'pip_lines',sum(1 for l in lines if l['speaker']=='PIP'))
print('days',days)
# loops
loops=re.findall(r'\[LOOP (\w+) (OPEN|FEED|PAY)\]',src); print('loops',loops)
print('issues',issues)
# n-gram overlap vs transcript
def norm(s):
    s=s.lower().replace('’',"'"); s=re.sub(r"[^a-z0-9' ]+",' ',s); return s.split()
tr=[]
for ln in open(D+'01_4l97aNza_Zc/transcript.txt'):
    tr+=norm(re.sub(r'^\d\d:\d\d ','',ln))
N=5
tgr=set(tuple(tr[i:i+N]) for i in range(len(tr)-N+1))
hits=[]
for l in lines:
    w=norm(l['text'])
    for i in range(len(w)-N+1):
        g=tuple(w[i:i+N])
        if g in tgr: hits.append((l['beat'],l['speaker'],' '.join(g)))
print('5gram hits',hits)
# lifted-phrase check (from review)
lifted=["locked in","oh gosh","salty","can't force","stranger","absolutely insane","accessory","fresh start","friends?","bawling","don't feel well","regretful","still wear it","night before we leave","come at a cost","fundamentally change","gets fun","revenge story","good question","12h43","fair for me","minute and 12","16 seconds","not expecting","band's back","looks like the band"]
low=src.lower()
print('lifted',[p for p in lifted if p in low])
json.dump([dict(beat=l['beat'],t=l['t'],speaker=l['speaker'],mouth=l['mouth'],words=l['words'],text=l['text']) for l in lines],open(D+'shrinking_planet/script_lines_v1.json','w'),indent=1,ensure_ascii=False)
