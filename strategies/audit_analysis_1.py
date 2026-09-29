rows=[]
for ln in open('trades.txt'):
    p=ln.strip().split('|')
    if len(p)!=11: continue
    rows.append(dict(setup=p[0],reg=p[1],hr=int(p[2]),dow=int(p[3]),sess=int(p[4]),
        conf=int(p[5]),mult=float(p[6]),R=float(p[7]),mfe=float(p[8]),mae=float(p[9]),bars=int(p[10])))
n=len(rows)
def stats(rs,label):
    if not rs: return None
    k=len(rs); w=[r for r in rs if r['R']>0]; l=[r for r in rs if r['R']<=0]
    gp=sum(r['R'] for r in w); gl=-sum(r['R'] for r in l)
    # dollar-weighted: R * sizeMult  (what the account actually earned)
    dollarR=sum(r['R']*r['mult'] for r in rs)
    pf=gp/gl if gl>0 else float('inf')
    print(f"{label:<22}{k:>5}{len(w)/k:>8.1%}{sum(r['R'] for r in rs)/k:>9.3f}{pf:>7.2f}"
          f"{(gp/len(w) if w else 0):>8.2f}{(gl/len(l) if l else 0):>8.2f}{dollarR:>10.2f}{dollarR/k:>8.3f}")
hdr=f"{'segment':<22}{'n':>5}{'win%':>8}{'E[R]':>9}{'PF':>7}{'avgW':>8}{'avgL':>8}{'$R tot':>10}{'$R/trd':>8}"
print("="*len(hdr)); print("OVERALL — R is per-trade risk; '$R' weights by the size multiplier actually used")
print(hdr); print("-"*len(hdr))
stats(rows,"ALL")
print()
print("BY SETUP"); print("-"*len(hdr))
for s in ['TL','TS','RL','RS']: stats([r for r in rows if r['setup']==s],s)
print()
print("BY SIZE MULTIPLIER (the defect)"); print("-"*len(hdr))
for m in [0.3,0.5,0.6,1.0]: stats([r for r in rows if abs(r['mult']-m)<0.01],f"mult {m}")
print()
print("BY CONFLUENCE"); print("-"*len(hdr))
for c in range(5): stats([r for r in rows if r['conf']==c],f"conf {c}")
print()
print("BY SESSION FLAG"); print("-"*len(hdr))
stats([r for r in rows if r['sess']==1],"in 07-16 UTC")
stats([r for r in rows if r['sess']==0],"outside")
