import csv
from collections import Counter
rows=list(csv.reader(open("STORYBOARD.tsv"),delimiter='\t'))
hdr=rows[0]
def ix(n): return hdr.index(n)
sc,sh,ct,ip,st=ix("Scene"),ix("Shot"),ix("Clip type"),ix("Image prompt (still)"),ix("Status")
print("Clip type counts:",dict(Counter(r[ct] for r in rows[1:])))
print()
n=0
for r in rows[1:]:
    if r[ip].strip():
        n+=1
        print(f"{r[sc]:16} {r[sh]:5} status={r[st]:6} type={r[ct][:24]}")
print("TOTAL with image prompt:",n)
