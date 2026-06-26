import sys, os, csv, glob, hashlib, shutil
shot=sys.argv[1]
dl=os.path.expanduser(f"~/Downloads/{shot}.png")
if not os.path.exists(dl):
    print("ERR: no exact ~/Downloads/%s.png (do not glob)"%shot); sys.exit(1)
dst=f"stills/{shot}.png"
shutil.move(dl,dst)
md5=hashlib.md5(open(dst,'rb').read()).hexdigest()
dups=[os.path.basename(f) for f in glob.glob("stills/*.png") if f!=dst and hashlib.md5(open(f,'rb').read()).hexdigest()==md5]
rows=list(csv.reader(open("STORYBOARD.tsv"),delimiter='\t'))
hdr=rows[0]; si=hdr.index("Status"); sh=hdr.index("Shot")
for r in rows[1:]:
    if r[sh]==shot: r[si]="still"
csv.writer(open("STORYBOARD.tsv","w",newline=''),delimiter='\t').writerows(rows)
print(f"SAVED {shot} {os.path.getsize(dst)}b md5={md5[:8]}"+(f"  DUP of {dups}" if dups else "  unique"))
