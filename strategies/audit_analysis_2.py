rows=[]
for ln in open('trades.txt'):
    p=ln.strip().split('|')
    if len(p)!=11: continue
    rows.append(dict(setup=p[0],reg=p[1],hr=int(p[2]),dow=int(p[3]),sess=int(p[4]),
        conf=int(p[5]),mult=float(p[6]),R=float(p[7]),mfe=float(p[8]),mae=float(p[9]),bars=int(p[10])))
W=[r for r in rows if r['R']>0]; L=[r for r in rows if r['R']<=0]
print(f"WINNERS {len(W)}  LOSERS {len(L)}\n")
print("MFE — how far losers ran into profit before dying (exit-timing evidence)")
for t in [0.25,0.5,0.75,1.0,1.5,2.0]:
    a=sum(1 for r in L if r['mfe']>=t)
    print(f"  losers reaching +{t:>4}R: {a:>3}/{len(L)} = {a/len(L):>5.1%}")
print()
print("MAE — how close winners came to being stopped out")
for t in [0.25,0.5,0.75,0.9]:
    a=sum(1 for r in W if r['mae']>=t)
    print(f"  winners with MAE >= {t:>4}R: {a:>3}/{len(W)} = {a/len(W):>5.1%}")
print()
# Counterfactual: what would a fixed 1R take-profit have earned vs actual?
print("COUNTERFACTUAL EXITS (using real MFE/MAE; a trade 'hits' X if MFE>=X)")
print(f"{'exit rule':<18}{'wins':>6}{'win%':>8}{'E[R]':>9}{'total R':>10}")
for tgt in [0.5,0.75,1.0,1.25,1.5,2.0,2.5,3.0]:
    tot=0.0; wins=0
    for r in rows:
        if r['mfe']>=tgt: tot+=tgt; wins+=1
        else: tot+= r['R'] if r['R']<0 else r['R']   # never reached target -> actual outcome
    print(f"  TP at {tgt:>4}R      {wins:>6}{wins/len(rows):>8.1%}{tot/len(rows):>9.3f}{tot:>10.1f}")
print(f"  {'ACTUAL (as run)':<16}{len(W):>6}{len(W)/len(rows):>8.1%}{sum(r['R'] for r in rows)/len(rows):>9.3f}{sum(r['R'] for r in rows):>10.1f}")
print()
print("BY HOUR (UTC) — only hours with >=8 trades")
buckets={}
for r in rows: buckets.setdefault(r['hr'],[]).append(r)
print(f"  {'hr':>3}{'n':>5}{'win%':>8}{'E[R]':>9}")
for h in sorted(buckets):
    b=buckets[h]
    if len(b)>=8:
        print(f"  {h:>3}{len(b):>5}{sum(1 for r in b if r['R']>0)/len(b):>8.1%}{sum(r['R'] for r in b)/len(b):>9.3f}")
print()
print("BY REGIME"); 
for g in ['U','D','S']:
    b=[r for r in rows if r['reg']==g]
    if b: print(f"  {g}: n={len(b):>3} win={sum(1 for r in b if r['R']>0)/len(b):>5.1%} E[R]={sum(r['R'] for r in b)/len(b):>+.3f}")
print()
tot_norm=sum(r['R'] for r in rows); tot_act=sum(r['R']*r['mult'] for r in rows)
print(f"EDGE DESTROYED BY SIZING: full-size total {tot_norm:.1f}R vs actual {tot_act:.1f}R "
      f"-> sizing keeps only {tot_act/tot_norm:.0%} of the edge")
