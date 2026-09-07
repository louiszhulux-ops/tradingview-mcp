#!/usr/bin/env python3
"""
FOLD C -- the sealed test period, 2026-08-09 to 2026-08-31. Run once.
Primary model, frozen and committed before this ran: config 4, sweep + B1 bias
+ room >= 10R. Everything else is secondary context, declared as such in
PHASE4_RESULTS.md sec 3.
"""
import math
CFG = ["1 sweep only","2 +bias","3 +room","4 +bias+room",
       "5 +bias+disp","6 +bias+reclaim","7 +bias+room+disp","8 FULL"]
CX  = {"MGC":"metals","SIL":"metals","MNQ":"equity","MCL":"energy","6E":"FX"}
# cell -> config -> (armed, n, E[R], win%);  n = 0 means the model never armed
C = {
 "MGC long": [(179,122, 0.179,21.3),(179,122, 0.179,21.3),(179, 31, 0.209,22.6),(179, 31, 0.209,22.6),
              ( 56, 37,-0.130,16.2),(119, 85, 0.031,18.8),( 56,  8,-0.413,12.5),( 50,  8,-0.413,12.5)],
 "MGC short":[(214,134, 0.023,18.7),(  0,  0, 0.0,  0.0),(214, 45, 0.316,24.4),(  0,  0, 0.0,  0.0),
              (  0,  0, 0.0,  0.0),(  0,  0, 0.0,  0.0),(  0,  0, 0.0,  0.0),(  0,  0, 0.0,  0.0)],
 "SIL long": [(232,150,-0.001,17.3),(232,150,-0.001,17.3),(232, 48, 0.063,18.8),(232, 48, 0.063,18.8),
              ( 71, 50,-0.192,14.0),(173,121, 0.098,19.0),( 71,  7,-0.195,14.3),( 63,  7,-0.195,14.3)],
 "SIL short":[(230,156, 0.188,20.5),(  0,  0, 0.0,  0.0),(230, 49, 0.537,26.5),(  0,  0, 0.0,  0.0),
              (  0,  0, 0.0,  0.0),(  0,  0, 0.0,  0.0),(  0,  0, 0.0,  0.0),(  0,  0, 0.0,  0.0)],
 "MNQ long": [(209,151,-0.043,17.9),(122, 84, 0.082,20.2),(209, 31,-0.420,12.9),(122, 22,-0.123,18.2),
              ( 33, 24,-0.096,16.7),( 80, 60, 0.071,20.0),( 33,  4, 0.307,25.0),( 29,  3, 0.794,33.3)],
 "MNQ short":[(257,164,-0.002,18.9),(111, 72, 0.060,19.4),(257, 57,-0.157,17.5),(111, 24, 0.088,20.8),
              ( 29, 18,-0.413,11.1),( 78, 51,-0.164,15.7),( 29,  0, 0.0,  0.0),( 26,  0, 0.0,  0.0)],
 "MCL long": [(220,141, 0.083,23.4),(158,102,-0.069,20.6),(220, 28,-0.817,10.7),(158, 19,-1.106, 5.3),
              ( 44, 33,-0.544,12.1),(110, 77,-0.078,20.8),( 44,  6,-1.461, 0.0),( 38,  6,-1.461, 0.0)],
 "MCL short":[(204,146, 0.094,23.3),( 75, 57,-0.447,14.0),(204, 35,-0.059,22.9),( 75, 14,-0.576,14.3),
              ( 17, 13,-1.182, 0.0),( 55, 43,-0.170,18.6),( 17,  1,-1.218, 0.0),( 12,  0, 0.0,  0.0)],
 "6E long":  [(174,139,-0.057,18.7),(174,139,-0.057,18.7),(174, 24, 0.279,25.0),(174, 24, 0.279,25.0),
              ( 50, 36, 0.173,22.2),(145,120,-0.086,18.3),( 50,  2, 4.743,100.0),( 49,  2, 4.743,100.0)],
 "6E short": [(167,114,-0.273,14.9),(  0,  0, 0.0,  0.0),(167, 15, 0.376,26.7),(  0,  0, 0.0,  0.0),
              (  0,  0, 0.0,  0.0),(  0,  0, 0.0,  0.0),(  0,  0, 0.0,  0.0),(  0,  0, 0.0,  0.0)],
}
CELLS = list(C)

def pooled(i, cells=CELLS):
    tot=n=w=0.0
    for c in cells:
        _,nc,E,wp = C[c][i]
        if nc==0: continue
        tot+=nc*E; n+=nc; w+=nc*wp
    if n==0: return 0.0,0,0.0,0.0
    E=tot/n; wp=w/n/100.0
    sd=math.sqrt(max(wp*25+(1-wp)-E*E,1e-9))
    return E,int(n),sd,E/(sd/math.sqrt(n))

short = lambda c: c.replace(' short',' s').replace(' long',' l')
print("FOLD C -- SEALED TEST PERIOD, 2026-08-09 to 2026-08-31. Run once.\n")
print(f"{'config':<20}" + "".join(f"{short(c):>10}" for c in CELLS) + f"{'pooled':>9}{'+/pop':>8}{'n':>7}{'t':>7}")
for i,name in enumerate(CFG):
    line=f"{name:<20}"; pos=0; pop=0
    for c in CELLS:
        _,nc,E,_ = C[c][i]
        line += "         -" if nc==0 else f"{E:>+10.3f}"
        if nc>0:
            pop+=1
            if E>0: pos+=1
    E,n,sd,t = pooled(i)
    print(line + f"{E:>+9.3f}{pos:>4}/{pop:<3}{n:>7}{t:>+7.2f}")
print("\n  '-' = the model never armed in that cell during fold C.")

print("\n" + "="*118)
print("PRIMARY RESULT -- config 4 (sweep + B1 bias + room), the frozen model\n")
E,n,sd,t = pooled(3)
lo, hi = E-1.645*sd/math.sqrt(n), E+1.645*sd/math.sqrt(n)
pos = sum(1 for c in CELLS if C[c][3][1]>0 and C[c][3][2]>0)
pop = sum(1 for c in CELLS if C[c][3][1]>0)
print(f"  pooled E[R] {E:+.3f}   n {n}   t {t:+.2f}   90% CI [{lo:+.3f}, {hi:+.3f}]")
print(f"  cells positive {pos}/{pop} populated  ({10-pop} of 10 cells never armed at all)")
print("\n  GATE (pre-registered, Amendment 1):")
for txt, ok in ((f"pooled E[R] > 0", E>0),
                (f"pooled one-sided t >= +1.5", t>=1.5),
                (f">= 7 of 10 instrument cells positive", pos>=7),
                (f">= 6 of 8 complex cells positive", None)):
    print(f"    {'PASS' if ok else 'FAIL':>4}  {txt}")
print("\n  RESULT: FAILED. Three of the four criteria cannot even be evaluated as")
print("  designed, because three cells never armed.")

print("\n" + "="*118)
print("SECONDARY CONTEXT (declared secondary before the run; not a fallback result)\n")
for i in (0,2,3):
    E,n,sd,t = pooled(i)
    pos = sum(1 for c in CELLS if C[c][i][1]>0 and C[c][i][2]>0)
    pop = sum(1 for c in CELLS if C[c][i][1]>0)
    print(f"  {CFG[i]:<18} pooled {E:+.3f}R  n {n:5d}  cells {pos}/{pop}  t {t:+.2f}")

print("\nDEVELOPMENT (A+B) vs TEST (C), the three interpretable configs:")
AB = {0:(-0.100,5479),2:(+0.050,1378),3:(+0.132,674)}
print(f"  {'config':<18}{'A+B':>10}{'C':>10}{'change':>10}")
for i in (0,2,3):
    Ec,_,_,_ = pooled(i)
    print(f"  {CFG[i]:<18}{AB[i][0]:>+10.3f}{Ec:>+10.3f}{Ec-AB[i][0]:>+10.3f}")

print("\n" + "="*118)
print("DID THE BIAS FILTER SEPARATE OUT-OF-SAMPLE? kept vs discarded, where both exist\n")
print(f"{'cell':>11}{'kept':>10}{'n':>6}{'discarded':>12}{'n':>6}{'spread':>10}")
kn=ke=dn=de=kw=dw=0.0; sep=0; tested=0
for c in CELLS:
    _,n0,E0,w0 = C[c][0]
    _,n1,E1,w1 = C[c][1]
    nd = n0-n1
    if n1==0 or nd<=0:
        print(f"{c:>11}{'-':>10}{n1:>6}{'-':>12}{nd:>6}{'  not testable':>10}")
        continue
    tested+=1
    Ed=(n0*E0-n1*E1)/nd; wd=(n0*w0-n1*w1)/nd
    print(f"{c:>11}{E1:>+10.3f}{n1:>6}{Ed:>+12.3f}{nd:>6}{E1-Ed:>+10.3f}")
    kn+=n1; ke+=n1*E1; kw+=n1*w1; dn+=nd; de+=nd*Ed; dw+=nd*wd
    if E1>Ed: sep+=1
Ek,Ed_ = ke/kn, de/dn
wk,wdd = kw/kn/100, dw/dn/100
sdk=math.sqrt(wk*25+(1-wk)-Ek*Ek); sdd=math.sqrt(wdd*25+(1-wdd)-Ed_*Ed_)
se=math.sqrt(sdk*sdk/kn+sdd*sdd/dn)
print(f"{'POOLED':>11}{Ek:>+10.3f}{kn:>6.0f}{Ed_:>+12.3f}{dn:>6.0f}{Ek-Ed_:>+10.3f}")
print(f"\n  separates in {sep}/{tested} testable cells")
print(f"  difference {Ek-Ed_:+.3f}R, SE {se:.3f}, t {(Ek-Ed_)/se:+.2f}")
print(f"  90% CI [{Ek-Ed_-1.645*se:+.3f}, {Ek-Ed_+1.645*se:+.3f}]")
