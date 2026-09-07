#!/usr/bin/env python3
"""
Phase 4 ablation, folds A+B, ten instrument x direction cells.
Config list fixed in PHASE2_PROTOCOL.md sec 4 before this ran.
Bias frozen = B1 (4H EMA20/50), selected in Phase 2.
Cells with fewer than 30 fills are marked uninterpretable, not ranked.
"""
import math
CFG = ["1 sweep only","2 +bias","3 +room","4 +bias+room",
       "5 +bias+disp","6 +bias+reclaim","7 +bias+room+disp","8 FULL"]
CX  = {"MGC":"metals","SIL":"metals","MNQ":"equity","MCL":"energy","6E":"FX"}
MIN_N = 30

D = {
 "MGC long": [(790,581,-0.235,14.5),(151,111,-0.206,15.3),(790,130, 0.133,21.5),(151, 23, 0.359,26.1),
              ( 53, 42,-0.684, 7.1),( 99, 73,-0.405,12.3),( 53,  5,-1.197, 0.0),( 41,  4,-1.201, 0.0)],
 "MGC short":[(734,513, 0.046,19.3),(553,378, 0.096,20.1),(734,146, 0.317,24.7),(553,114, 0.469,27.2),
              (135, 91,-0.248,14.3),(400,290, 0.019,19.0),(135, 10, 0.038,20.0),(124,  9, 0.166,22.2)],
 "SIL long": [(902,608,-0.195,14.0),(159,104,-0.059,16.3),(902,159, 0.046,18.2),(159, 29,-0.232,13.8),
              ( 53, 38,-0.090,15.8),(109, 82,-0.095,15.9),( 53,  3,-1.069, 0.0),( 43,  2,-1.068, 0.0)],
 "SIL short":[(681,495, 0.114,19.2),(569,418, 0.098,18.9),(681,154,-0.192,14.3),(569,130,-0.123,15.4),
              (168,124,-0.453, 9.7),(388,299, 0.267,21.7),(168, 20,-0.442,10.0),(140, 15,-0.642, 6.7)],
 "MNQ long": [(820,559,-0.061,17.0),(373,254, 0.039,18.9),(820,122, 0.272,23.0),(373, 42, 0.443,26.2),
              (104, 84,-0.300,13.1),(261,200, 0.100,20.0),(104, 10, 0.074,20.0),( 89,  9, 0.218,22.2)],
 "MNQ short":[(975,674,-0.002,18.2),(499,357, 0.005,18.2),(975,183, 0.123,21.3),(499, 86, 0.325,24.4),
              (116, 91,-0.410,11.0),(334,264,-0.183,15.2),(116,  6,-1.141, 0.0),(100,  6,-1.141, 0.0)],
 "MCL long": [(866,609,-0.251,16.7),(325,237,-0.217,16.9),(866,147, 0.055,23.8),(325, 66, 0.009,22.7),
              ( 98, 74,-0.660, 9.5),(231,178,-0.265,16.3),( 98, 11,-0.933, 9.1),( 87, 10,-0.851,10.0)],
 "MCL short":[(701,490,-0.265,16.7),(474,325,-0.291,16.6),(701,120, 0.101,25.0),(474, 76, 0.070,25.0),
              (141,100,-0.558,12.0),(338,241,-0.176,18.7),(141, 12, 0.093,25.0),(123, 11, 0.226,27.3)],
 "6E long":  [(686,530,-0.052,18.3),(193,158,-0.211,15.8),(686,123,-0.368,13.8),(193, 35,-0.693, 8.6),
              ( 58, 46,-0.514,10.9),(148,121,-0.077,18.2),( 58,  7,-1.218, 0.0),( 54,  7,-1.218, 0.0)],
 "6E short": [(557,420,-0.061,18.1),(404,303, 0.121,21.1),(557, 94,-0.032,19.1),(404, 73, 0.297,24.7),
              (144,113, 0.069,20.4),(320,253, 0.149,21.7),(144, 13,-0.750, 7.7),(130, 11,-0.667, 9.1)],
}
CELLS = list(D)

def pooled(i, cells=CELLS):
    tot=n=w=0.0
    for c in cells:
        _,nc,E,wp = D[c][i]; tot+=nc*E; n+=nc; w+=nc*wp
    if n==0: return 0.0,0,0.0,0.0
    E=tot/n; wp=w/n/100.0
    sd=math.sqrt(max(wp*25+(1-wp)-E*E,1e-9))
    return E,int(n),sd,E/(sd/math.sqrt(n))

print("PHASE 4 ABLATION -- folds A+B, E[R] per instrument x direction cell")
print("(* = fewer than 30 fills in that cell: uninterpretable, shown but not ranked)\n")
short = lambda c: c.replace(' short',' s').replace(' long',' l')
print(f"{'config':<20}" + "".join(f"{short(c):>10}" for c in CELLS) + f"{'pooled':>9}{'signs':>7}{'n':>7}{'t':>7}")
res={}
for i,name in enumerate(CFG):
    line=f"{name:<20}"; pos=0; thin=0
    for c in CELLS:
        _,nc,E,_ = D[c][i]
        mark = "*" if nc < MIN_N else " "
        line += f"{E:>+9.3f}{mark}"
        if E>0: pos+=1
        if nc<MIN_N: thin+=1
    E,n,sd,t = pooled(i)
    res[i]=(E,n,t,pos,thin)
    print(line + f"{E:>+9.3f}{pos:>5}/10{n:>7}{t:>+7.2f}")

print("\nFill counts per cell (the reason configs 7 and 8 cannot be read):")
print(f"{'config':<20}" + "".join(f"{short(c):>10}" for c in CELLS) + f"{'total':>8}")
for i,name in enumerate(CFG):
    print(f"{name:<20}" + "".join(f"{D[c][i][1]:>10}" for c in CELLS) + f"{sum(D[c][i][1] for c in CELLS):>8}")

def marginal(a,b,label):
    d=[D[c][b][2]-D[c][a][2] for c in CELLS]
    ok=sum(1 for x in d if x>0)
    thin=sum(1 for c in CELLS if D[c][b][1]<MIN_N)
    print(f"  {label:<34}" + "".join(f"{x:>+8.2f}" for x in d) +
          f"   {ok}/10   mean {sum(d)/10:+.3f}" + (f"   [{thin} thin cells]" if thin else ""))

print("\nMARGINAL EFFECT of each condition (same event stream, one thing changed):")
print(f"  {'':<34}" + "".join(f"{short(c):>8}" for c in CELLS))
marginal(0,2,"ROOM, without bias        (3-1)")
marginal(1,3,"ROOM, with bias           (4-2)")
marginal(0,1,"BIAS, without room        (2-1)")
marginal(2,3,"BIAS, with room           (4-3)")
marginal(1,5,"RECLAIM, on bias          (6-2)")
marginal(1,4,"DISPLACEMENT, on bias     (5-2)")
marginal(3,6,"DISPLACEMENT, on bias+room(7-4)")

print("\n" + "="*118)
print("RANKING, configs with >= 30 fills in every cell only:")
ok=[(i,)+res[i] for i in res if res[i][4]==0]
ok.sort(key=lambda r: (-r[4-1], -r[1]))
for i,E,n,t,pos,thin in sorted(ok, key=lambda r:(-r[4],-r[1])):
    print(f"  {CFG[i]:<20} {pos}/10 cells   pooled {E:+.3f}R   n {n:5d}   t {t:+.2f}")
print("\nConfigs 7 and 8 have 2-20 fills per cell. They are not ranked and no")
print("conclusion is drawn from them either way.")
