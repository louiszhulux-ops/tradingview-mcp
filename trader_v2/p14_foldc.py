#!/usr/bin/env python3
"""
Phase 14 -- Fold C analysis. Reads only committed run files; changes nothing.
Reuses the Phase 13G clustering identities verbatim.
"""
import re, glob, os, statistics
from collections import OrderedDict
D = os.path.dirname(os.path.abspath(__file__))

def parse(line):
    p = line.split("|")
    def v(i, pre):
        s = p[i]; return s[len(pre):].strip() if s.startswith(pre) else s.strip()
    return dict(inst=p[0], dir=p[1], ltf=p[2], fold=p[3],
        sw=v(4,"sw "), swtype=p[5].strip(), swX=float(v(6,"swX ")),
        ch=v(7,"ch "), chL=float(v(8,"chL ")), rt=v(9,"rt "),
        bos=v(10,"bos "), bosL=float(v(11,"bosL ")), fvg=v(12,"fvg "),
        en=v(13,"en "), enPx=float(v(14,"enPx ")), stop=float(v(15,"stop ")),
        outcome=p[16].strip(), R=float(p[17].replace("R","")),
        usd=float(p[18].replace("$","")), reason=p[19].strip(),
        bars=int(p[20].replace("bars","")))

def load(sub):
    rows=[]
    for f in sorted(glob.glob(os.path.join(D,sub,"*.txt"))):
        if not re.match(r"^(MGC|MNQ)_[LS]_\dm_[ABC]\.txt$", os.path.basename(f)): continue
        for line in open(f):
            if re.match(r"^(MGC1!|MNQ1!)\|", line): rows.append(parse(line.rstrip()))
    return rows

def cells(sub):
    out=[]
    for f in sorted(glob.glob(os.path.join(D,sub,"*.txt"))):
        if not re.match(r"^(MGC|MNQ)_[LS]_\dm_[ABC]\.txt$", os.path.basename(f)): continue
        t=open(f).read(); inst,d,ltf,fold=os.path.basename(f)[:-4].split("_")
        fn=re.search(r"sweeps (\d+) \| CHOCH (\d+) \| retests (\d+) \| BOS\+disp (\d+) \| FVG (\d+) \| fills (\d+)",t)
        bars=re.search(r"foldbars (\d+) \| w/LTF (\d+)",t)
        cov=re.search(r"cov (\S+ \S+) -> (\S+ \S+)",t)
        p=re.search(r"fills (\d+) \| W(\d+) Lstop(\d+) TO(\d+).*?Rpre (-?\d+) \| Rpost (-?[\d.]+).*?tot\$ (-?[\d.]+)",t)
        mdd=re.search(r"DD_R ([\d.]+) \| DD_\$ ([\d.]+)",t); mcl=re.search(r"maxConsecL (\d+)",t); med=re.search(r"\| med (-?[\d.]+)",t)
        out.append(dict(inst=inst,d=d,ltf=ltf,fold=fold,bars=int(bars.group(1)),cov=int(bars.group(2)),
            cov0=cov.group(1) if cov else "-", cov1=cov.group(2) if cov else "-",
            sw=int(fn.group(1)),ch=int(fn.group(2)),rt=int(fn.group(3)),bos=int(fn.group(4)),
            fvg=int(fn.group(5)),fill=int(fn.group(6)),
            W=int(p.group(2)) if p else 0,Ls=int(p.group(3)) if p else 0,TO=int(p.group(4)) if p else 0,
            Rpre=float(p.group(5)) if p else 0.0,Rpost=float(p.group(6)) if p else 0.0,usd=float(p.group(7)) if p else 0.0,
            ddR=float(mdd.group(1)) if mdd else 0.0,ddU=float(mdd.group(2)) if mdd else 0.0,
            mcl=int(mcl.group(1)) if mcl else 0, med=float(med.group(1)) if med else None))
    return out

C=cells("v53_runs_foldc"); AB=cells("v53_runs")
rc=load("v53_runs_foldc"); rab=load("v53_runs")

print("="*118)
print("FOLD C -- 8-CELL EXECUTION-LEVEL RESULTS")
print("="*118)
h=f"{'cell':<16}{'bars':>6}{'cov':>6}{'swp':>5}{'CHOCH':>6}{'rtst':>5}{'BOS':>4}{'FVG':>4}{'fill':>5}{'W':>2}{'Ls':>3}{'TO':>3}{'wr':>7}{'Rpre':>6}{'Rpost':>8}{'avg':>9}{'med':>9}{'mcL':>4}{'ddR':>7}{'ddUSD':>8}{'USD':>9}"
print(h); print("-"*len(h))
for c in C:
    n=c['fill']
    print(f"{c['inst']+' '+c['d']+' '+c['ltf']+' C':<16}{c['bars']:>6}{c['cov']:>6}{c['sw']:>5}{c['ch']:>6}{c['rt']:>5}{c['bos']:>4}{c['fvg']:>4}{n:>5}{c['W']:>2}{c['Ls']:>3}{c['TO']:>3}"
        + (f"{100*c['W']/n:>6.1f}%" if n else f"{'-':>7}") + f"{c['Rpre']:>6.0f}{c['Rpost']:>8.3f}"
        + (f"{c['Rpost']/n:>9.4f}" if n else f"{'-':>9}")
        + (f"{c['med']:>9.4f}" if c['med'] is not None else f"{'-':>9}")
        + f"{c['mcl']:>4}{c['ddR']:>7.3f}{c['ddU']:>8.2f}{c['usd']:>9.2f}")

def roll(cs,sel):
    g=[c for c in cs if sel(c)]
    n=sum(c['fill'] for c in g); W=sum(c['W'] for c in g)
    return dict(n=n,W=W,L=n-W,R=sum(c['Rpost'] for c in g),Rpre=sum(c['Rpre'] for c in g),
        usd=sum(c['usd'] for c in g),sw=sum(c['sw'] for c in g),ch=sum(c['ch'] for c in g),
        rt=sum(c['rt'] for c in g),bos=sum(c['bos'] for c in g),fvg=sum(c['fvg'] for c in g),
        ddR=max([c['ddR'] for c in g],default=0))
print()
for lt in ["1m","3m"]:
    r=roll(C,lambda c,lt=lt: c['ltf']==lt)
    print(f"  FOLD C {'H1' if lt=='1m' else 'H2'} ({lt}): fills {r['n']:>2} | W {r['W']} L {r['L']} | "
          f"wr {100*r['W']/r['n'] if r['n'] else 0:5.1f}% | Rpre {r['Rpre']:+.0f} | Rpost {r['R']:+7.3f} | "
          f"avg {r['R']/r['n'] if r['n'] else 0:+7.4f} | ${r['usd']:+9.2f}")
rt=roll(C,lambda c: True)
print(f"  FOLD C TOTAL:      fills {rt['n']:>2} | W {rt['W']} L {rt['L']} | wr {100*rt['W']/rt['n']:5.1f}% | Rpost {rt['R']:+7.3f} | ${rt['usd']:+9.2f}")

print()
print("="*118)
print("FUNNEL -- FOLD C vs A+B")
print("="*118)
def fun(cs,sel,lbl):
    r=roll(cs,sel)
    print(f"{lbl:<16} sweeps {r['sw']:>5} | ->CHOCH {r['ch']:>5} {100*r['ch']/r['sw']:5.1f}% | ->retest {r['rt']:>4} {100*r['rt']/r['ch']:5.1f}% | "
          f"->BOS+disp {r['bos']:>3} {100*r['bos']/r['rt']:5.2f}% | ->FVG {r['fvg']:>3} {100*r['fvg']/r['bos'] if r['bos'] else 0:5.1f}% | "
          f"->fill {r['n']:>3} {100*r['n']/r['fvg'] if r['fvg'] else 0:5.1f}% | sweep->fill {100*r['n']/r['sw']:5.2f}%")
fun(AB,lambda c: c['ltf']=='1m',"A+B  1m")
fun(C, lambda c: c['ltf']=='1m',"C    1m")
fun(AB,lambda c: c['ltf']=='3m',"A+B  3m")
fun(C, lambda c: c['ltf']=='3m',"C    3m")

print()
print("="*118)
print("EVENT CLUSTERING -- Phase 13G identities applied verbatim")
print("="*118)
kp=lambda r:(r["inst"],r["dir"],r["ltf"],r["ch"],r["chL"],r["bos"],r["bosL"],r["en"],r["enPx"])
ka=lambda r:(r["inst"],r["dir"],r["ltf"],r["bos"],r["bosL"],r["en"],r["enPx"])
def clus(rows,fn):
    g=OrderedDict()
    for r in rows: g.setdefault(fn(r),[]).append(r)
    return g
for lbl,rows in [("FOLD C",rc),("A+B (13G control)",rab)]:
    for nm,fn in [("primary",kp),("alternative",ka)]:
        for lt in [None,"1m","3m"]:
            sub=[r for r in rows if lt is None or r["ltf"]==lt]
            if not sub: 
                print(f"  {lbl:<18} {nm:<12} {lt or 'all':<4}: execution N  0 | clusters  0"); continue
            g=clus(sub,fn); m=[v for v in g.values() if len(v)>1]; nm2=sum(len(v) for v in m)
            print(f"  {lbl:<18} {nm:<12} {lt or 'all':<4}: execution N {len(sub):>2} | clusters {len(g):>2} | "
                  f"multi-fill {len(m):>2} | largest {max(len(v) for v in g.values())} | fills in multi {nm2:>2} ({100*nm2/len(sub):5.1f}%)")
    print()

# ---- statistical treatment ----
from math import sqrt
def wilson(k,n,z=1.645):
    if n==0: return None
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d
    h=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (max(0,c-h),min(1,c+h))
def meanci(k,n,win=4.97,loss=-1.03):
    if n<2: return None
    xs=[win]*k+[loss]*(n-k); m=statistics.mean(xs); sd=statistics.stdev(xs)
    return m,sd,(m-1.645*sd/sqrt(n), m+1.645*sd/sqrt(n))
print()
print("="*118)
print("STATISTICAL TREATMENT -- execution level ONLY; event level reported as N, not as an interval")
print("="*118)
for lbl,k,n in [("Fold C H1 (1m)",2,13),("Fold C H2 (3m)",1,5),("Fold C total",3,18),
                ("A+B H1 (1m)",3,28),("A+B H2 (3m)",3,12),("A+B total",6,40)]:
    w=wilson(k,n); mc=meanci(k,n)
    ws=f"[{100*w[0]:5.1f}%,{100*w[1]:5.1f}%]" if w else "n/a"
    ms=f"mean {mc[0]:+.3f} sd {mc[1]:.2f} CI [{mc[2][0]:+.3f},{mc[2][1]:+.3f}]" if mc else "n/a"
    print(f"  {lbl:<16} wins {k}/{n:<3} = {100*k/n:5.1f}%  90% Wilson {ws}  {ms}")
print("\n  Breakeven win rate at +5R/-1R = 16.7%.")
print("  These are EXECUTION-LEVEL intervals and assume independence between fills, which the")
print("  clustering above shows is violated (88.9% of Fold C fills sit in multi-fill clusters).")
print("  No event-level confidence interval is computed: 10 alternative-identity events, of which")
print("  8 are 1m and 3 are 3m, does not support one.")
