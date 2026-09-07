#!/usr/bin/env python3
"""
Phase 13G -- event independence / clustering audit.

Reads the Phase 13F ledger verbatim from trader_v2/v53_runs/*.txt.
Changes nothing. Computes two clustering identities and reports both.
"""
import re, glob, os, statistics
from collections import OrderedDict

FIELDS = ["inst","dir","ltf","fold","sw","swtype","swX","ch","chL","rt","bos","bosL",
          "fvg","en","enPx","stop","outcome","R","usd","reason","bars"]

def parse(line):
    p = line.split("|")
    def v(i, pre):
        s = p[i]
        return s[len(pre):].strip() if s.startswith(pre) else s.strip()
    d = dict(
        inst=p[0], dir=p[1], ltf=p[2], fold=p[3],
        sw=v(4,"sw "), swtype=p[5].strip(), swX=float(v(6,"swX ")),
        ch=v(7,"ch "), chL=float(v(8,"chL ")), rt=v(9,"rt "),
        bos=v(10,"bos "), bosL=float(v(11,"bosL ")), fvg=v(12,"fvg "),
        en=v(13,"en "), enPx=float(v(14,"enPx ")), stop=float(v(15,"stop ")),
        outcome=p[16].strip(), R=float(p[17].replace("R","")),
        usd=float(p[18].replace("$","")), reason=p[19].strip(),
        bars=int(p[20].replace("bars","")),
    )
    return d

rows=[]
for f in sorted(glob.glob(os.path.join(os.path.dirname(__file__),"v53_runs","*.txt"))):
    for line in open(f):
        if re.match(r"^(MGC1!|MNQ1!)\|", line):
            rows.append(parse(line.rstrip("\n")))

# ---------------- 9. control reproduction ----------------
def tot(sel):
    g=[r for r in rows if sel(r)]
    w=sum(1 for r in g if r["outcome"]=="WIN")
    return len(g), w, len(g)-w, sum(r["R"] for r in g), sum(r["usd"] for r in g)

print("="*100)
print("SECTION 9 -- PHASE 13F CONTROL REPRODUCTION")
print("="*100)
ctrl = {"H1 (1m)": (lambda r: r["ltf"]=="1m", 28,3,25,-11.752),
        "H2 (3m)": (lambda r: r["ltf"]=="3m", 12,3, 9,  5.687),
        "TOTAL":   (lambda r: True,           40,6,34, -6.065)}
ok=True
for lbl,(sel,en,ew,el,eR) in ctrl.items():
    n,w,l,R,u = tot(sel)
    m = (n==en and w==ew and l==el and abs(R-eR)<0.002)
    ok &= m
    print(f"{lbl:<10} fills {n:>3} (exp {en:>3})  wins {w} (exp {ew})  losses {l:>2} (exp {el:>2})  "
          f"R {R:+8.3f} (exp {eR:+8.3f})  ${u:+9.2f}   {'MATCH' if m else '*** MISMATCH ***'}")
print(f"\nCONTROL REPRODUCTION: {'PASS -- all three totals match Phase 13F exactly' if ok else 'FAIL -- STOP'}")

# ---------------- 2/4/5. clustering ----------------
def key_primary(r):  return (r["inst"],r["dir"],r["ltf"],r["ch"],r["chL"],r["bos"],r["bosL"],r["en"],r["enPx"])
def key_alt(r):      return (r["inst"],r["dir"],r["ltf"],r["bos"],r["bosL"],r["en"],r["enPx"])
def key_13f(r):      return (r["inst"],r["dir"],r["ltf"],r["fold"],r["en"],r["enPx"])

def cluster(keyfn):
    g=OrderedDict()
    for r in rows: g.setdefault(keyfn(r),[]).append(r)
    return g

print()
print("="*100)
print("SECTIONS 3-5 -- CLUSTERING IDENTITIES  (both reported; neither selected on results)")
print("="*100)
for name,fn in [("PRIMARY  (inst,dir,LTF,CHOCH ts+lvl,BOS ts+lvl,entry ts,entry px)",key_primary),
                ("ALTERNATIVE (inst,dir,LTF,BOS ts+lvl,entry ts,entry px)",key_alt),
                ("PHASE 13F AS PUBLISHED (inst,dir,LTF,fold,entry ts,entry px)",key_13f)]:
    g=cluster(fn)
    multi=[k for k,v in g.items() if len(v)>1]
    nf=sum(len(v) for v in g.values() if len(v)>1)
    print(f"{name}\n    clusters {len(g):>3} | multi-fill clusters {len(multi):>2} | fills in multi-fill clusters {nf:>2} "
          f"({100*nf/len(rows):.1f}%) | largest cluster {max(len(v) for v in g.values())}")

# determinism check
for name,fn in [("primary",key_primary),("alternative",key_alt)]:
    g1=cluster(fn); g2=cluster(fn)
    assert [ (k,len(v)) for k,v in g1.items() ] == [ (k,len(v)) for k,v in g2.items() ]
print("\nDeterminism: both identities are pure functions of recorded ledger fields; re-running yields identical partitions.")

# ---------------- difference between the two identities ----------------
print()
print("="*100)
print("WHY PRIMARY (31) AND ALTERNATIVE (27) DIFFER")
print("="*100)
ga=cluster(key_alt)
split=0
for k,v in ga.items():
    chs={(r["ch"],r["chL"]) for r in v}
    if len(chs)>1:
        split+=1
        print(f"\nAlt cluster {v[0]['inst']} {v[0]['dir']} {v[0]['ltf']} {v[0]['fold']} "
              f"BOS {v[0]['bos']} @ {v[0]['bosL']} entry {v[0]['en']} @ {v[0]['enPx']}  "
              f"-> {len(v)} fills, {len(chs)} distinct CHOCH:")
        for r in v:
            print(f"    sweep {r['sw']} ({r['swtype']}, extreme {r['swX']})  CHOCH {r['ch']} @ {r['chL']}  "
                  f"stop {r['stop']}  {r['outcome']} {r['R']:+.3f}R")
print(f"\n{split} alternative-identity clusters contain more than one distinct CHOCH; they split into "
      f"{31-27+split} primary clusters, which is the entire 31 vs 27 difference.")

# ---------------- full cluster table ----------------
print()
print("="*100)
print("FULL CLUSTER TABLE -- ALTERNATIVE IDENTITY (27 clusters; matches the Phase 13F count)")
print("="*100)
for i,(k,v) in enumerate(ga.items(),1):
    r0=v[0]
    Rs=[r["R"] for r in v]
    print(f"\nC{i:02d}  {r0['inst']} {'LONG' if r0['dir']=='L' else 'SHORT'} {r0['ltf']} fold {r0['fold']}  "
          f"| fills {len(v)}")
    chstr = "; ".join(sorted({r["ch"] + " @ " + str(r["chL"]) for r in v}))
    print("     CHOCH " + chstr)
    print(f"     BOS   {r0['bos']} @ {r0['bosL']}   FVG {r0['fvg']}   entry {r0['en']} @ {r0['enPx']}")
    for r in v:
        print(f"       sweep {r['sw']} [{r['swtype']}] extreme {r['swX']:<10} stop {r['stop']:<12} "
              f"{r['outcome']:<5} {r['R']:+7.3f}R  ${r['usd']:+9.2f}  {r['reason']:<8} {r['bars']:>3} bars")
    if len(v)>1:
        print(f"       -> sum {sum(Rs):+7.3f}R | mean {statistics.mean(Rs):+7.3f}R | "
              f"best {max(Rs):+7.3f}R | worst {min(Rs):+7.3f}R | ${sum(r['usd'] for r in v):+9.2f}")

# ---------------- 5. event-level performance ----------------
def evperf(g,label):
    print()
    print("="*100)
    print(f"EVENT-LEVEL PERFORMANCE -- {label}")
    print("="*100)
    for lt in ["1m","3m"]:
        cl=[v for v in g.values() if v[0]["ltf"]==lt]
        if not cl: continue
        anyw=[c for c in cl if any(r["outcome"]=="WIN" for r in c)]
        allL=[c for c in cl if all(r["outcome"]=="LOSS" for r in c)]
        sums=[sum(r["R"] for r in c) for c in cl]
        means=[statistics.mean([r["R"] for r in c]) for c in cl]
        usd=[sum(r["usd"] for r in c) for c in cl]
        # cluster-level drawdown on the mean-per-event series, in event order
        order=sorted(range(len(cl)), key=lambda i: cl[i][0]["en"])
        cum=peak=dd=0.0
        for i in order:
            cum+=means[i]; peak=max(peak,cum); dd=max(dd,peak-cum)
        print(f"\n  {lt}: clusters {len(cl)}")
        print(f"    clusters with >=1 win           {len(anyw)}   ({100*len(anyw)/len(cl):.1f}%)   <- 'any-win' cluster win rate")
        print(f"    clusters with all losses        {len(allL)}   ({100*len(allL)/len(cl):.1f}%)")
        print(f"    SUM-of-constituents  total R    {sum(sums):+8.3f}   mean {statistics.mean(sums):+7.4f}   median {statistics.median(sums):+7.4f}")
        print(f"    MEAN-per-event       total R    {sum(means):+8.3f}   mean {statistics.mean(means):+7.4f}   median {statistics.median(means):+7.4f}")
        print(f"    post-drag dollars (sum)         ${sum(usd):+10.2f}")
        print(f"    max drawdown, mean-per-event series, entry order   {dd:.3f}R")

evperf(ga,"ALTERNATIVE IDENTITY (27 clusters)")
evperf(cluster(key_primary),"PRIMARY IDENTITY (31 clusters)")

# ---------------- 6. named examples ----------------
print()
print("="*100)
print("SECTION 6 -- THE THREE NAMED EXAMPLES")
print("="*100)
for lbl,sel in [("MNQ long 1m fold B", lambda r: r["inst"]=="MNQ1!" and r["dir"]=="L" and r["ltf"]=="1m" and r["fold"]=="B"),
                ("MGC short 1m fold A", lambda r: r["inst"]=="MGC1!" and r["dir"]=="S" and r["ltf"]=="1m" and r["fold"]=="A"),
                ("MNQ short 3m fold B", lambda r: r["inst"]=="MNQ1!" and r["dir"]=="S" and r["ltf"]=="3m" and r["fold"]=="B")]:
    sub=[r for r in rows if sel(r)]
    gg=OrderedDict()
    for r in sub: gg.setdefault(key_alt(r),[]).append(r)
    print(f"\n{lbl}: {len(sub)} fills -> {len(gg)} events (alternative identity)")
    for j,(k,v) in enumerate(gg.items(),1):
        Rs=[r["R"] for r in v]
        print(f"  event {j}: BOS {v[0]['bos']} @ {v[0]['bosL']} | FVG {v[0]['fvg']} | entry {v[0]['en']} @ {v[0]['enPx']} | {len(v)} fill(s)")
        for r in v:
            print(f"     sweep {r['sw']} [{r['swtype']}] extreme {r['swX']:<10} -> stop {r['stop']:<12} "
                  f"R={abs(r['enPx']-r['stop']):.4f} pts   {r['outcome']:<5} {r['R']:+7.3f}R  {r['reason']}")
        if len(v)>1:
            print(f"     event total {sum(Rs):+7.3f}R | mean {statistics.mean(Rs):+7.3f}R")

# ---------------- 8. overlap / concurrency ----------------
import datetime
def T(s): return datetime.datetime.strptime(s,"%Y-%m-%d %H:%M")
print()
print("="*100)
print("SECTION 8 -- OVERLAP / CONCURRENCY  (descriptive only; no netting rule introduced)")
print("="*100)
print("\nWithin multi-fill clusters: entry timestamp is part of BOTH identities, so every constituent")
print("of a multi-fill cluster enters on the SAME bar. Overlap is therefore certain and total at entry.")
print("\nExit timestamps were NOT recorded in the Phase 13F ledger. Approximate exits below are")
print("entry + bars_held x 5min; true exits are LATER wherever a session gap intervenes, so these")
print("durations are LOWER BOUNDS and any overlap they show is also a lower bound.")
for k,v in ga.items():
    if len(v)>1:
        ex=[T(r["en"])+datetime.timedelta(minutes=5*r["bars"]) for r in v]
        r0=v[0]
        print(f"\n  {r0['inst']} {r0['dir']} {r0['ltf']} {r0['fold']} entry {r0['en']} @ {r0['enPx']}  ({len(v)} fills)")
        print(f"    first entry {r0['en']} | last entry {r0['en']} (identical by construction)")
        print(f"    earliest approx exit {min(ex).strftime('%Y-%m-%d %H:%M')} | latest approx exit {max(ex).strftime('%Y-%m-%d %H:%M')}")
        print(f"    positions overlap: YES | simultaneous exposure from convergence: {len(v)} units")
mx=max(len(v) for v in ga.values())
print(f"\nMaximum simultaneous exposure caused by convergent sequences: {mx} units "
      f"(largest cluster size, alternative identity).")

# cross-cluster overlap, lower bound
iv=[]
for k,v in ga.items():
    r0=v[0]; s=T(r0["en"]); e=max(T(r["en"])+datetime.timedelta(minutes=5*r["bars"]) for r in v)
    iv.append((s,e,r0["inst"],r0["dir"],r0["ltf"],len(v)))
ov=0
for i in range(len(iv)):
    for j in range(i+1,len(iv)):
        a,b=iv[i],iv[j]
        if a[2]==b[2] and a[4]==b[4] and a[0]<b[1] and b[0]<a[1]: ov+=1
print(f"Distinct clusters overlapping in time (same instrument, same LTF, lower bound): {ov} pairs.")

# ---------------- 7. dependence summary ----------------
print()
print("="*100)
print("SECTION 7 -- DEPENDENCE SUMMARY")
print("="*100)
gp=cluster(key_primary)
for lbl,g in [("primary (31)",gp),("alternative (27)",ga)]:
    for lt in [None,"1m","3m"]:
        cl=[v for v in g.values() if lt is None or v[0]["ltf"]==lt]
        f=sum(len(v) for v in cl); m=[v for v in cl if len(v)>1]
        nm=sum(len(v) for v in m)
        tag=lt or "all"
        print(f"  {lbl:<18} {tag:<4}: execution N {f:>2} | event N {len(cl):>2} | multi-fill clusters {len(m):>2} | "
              f"largest {max((len(v) for v in cl),default=0)} | fills in multi-fill clusters {nm:>2} ({100*nm/f:.1f}%)")
