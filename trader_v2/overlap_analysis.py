#!/usr/bin/env python3
"""
V45 F0/F6 overlap. Raw table rows copied from the four chart runs.
Answers the open question left in SETUP_FAMILIES.md: are the liquidity-sweep
family and the range-mean-reversion family the same effect?
"""
import math

# cell -> group -> (armed, n, E[R], win%)
D = {
 "MNQ long": {"G0":(896,137,0.061,19.7),"G1":(700,169,0.348,25.4),"G2":(133,16,0.740,31.3),
              "G3":(1029,153,0.132,20.9),"G4":(833,197,0.470,27.4),"G5":(133,29,1.126,37.9)},
 "MNQ short":{"G0":(1084,211,0.057,20.4),"G1":(848,271,0.155,22.5),"G2":(148,30,0.011,20.0),
              "G3":(1232,240,0.057,20.4),"G4":(996,305,0.161,22.6),"G5":(148,39,0.184,23.1)},
 "MGC short":{"G0":(839,174,0.326,24.7),"G1":(615,180,0.292,25.6),"G2":(109,17,0.219,23.5),
              "G3":(948,191,0.317,24.6),"G4":(724,202,0.216,24.3),"G5":(109,24,-0.488,12.5)},
 "MGC long": {"G0":(861,146,0.038,19.9),"G1":(723,190,0.070,22.1),"G2":(108,15,1.216,40.0),
              "G3":(969,161,0.147,21.7),"G4":(831,209,0.069,22.0),"G5":(108,19,0.051,21.1)},
}
# tag census: cell -> (F0 arms, %extreme, %lowADX, %isF6, %htf, %reclaim, %disp,
#                      F6 arms, %sweep<=12b, %htf, %isF0)
T = {
 "MNQ long": (1029,30.8,38.6,12.9,48.1,59.0,20.4,  833,42.4,40.5,16.0),
 "MNQ short":(1232,25.1,47.6,12.0,49.5,57.1,17.2,  996,49.0,54.2,14.9),
 "MGC short":( 948,28.8,34.7,11.5,58.3,58.0,15.4,  724,38.8,56.4,15.1),
 "MGC long": ( 969,29.5,31.5,11.1,34.1,55.9,17.3,  831,33.0,35.0,13.0),
}
CELLS = ["MGC long","MGC short","MNQ long","MNQ short"]
LBL = {"G0":"F0 only (sweep, not range-regime)","G1":"F6 only (range extreme, no sweep)",
       "G2":"F0 n F6  entry at swept level","G3":"F0 all","G4":"F6 all",
       "G5":"F6 n F0  entry at range extreme"}

TGT, STOP = 5.0, -1.0
def stats(n, E, w):
    p = w/100.0
    sd = math.sqrt(p*TGT*TGT + (1-p)*STOP*STOP - E*E)
    return sd, (2*E/(sd*sd) if sd > 0 else 0.0), (E/(sd/math.sqrt(n)) if n else 0.0)

print("V45 -- F0/F6 OVERLAP, E[R] by bucket, four market x direction cells\n")
print(f"{'bucket':>36} " + "".join(f"{c:>11}" for c in CELLS) +
      f"{'pooled':>9}{'signs':>7}{'n':>7}{'lam':>8}{'t':>7}")
res = {}
for g in ("G0","G1","G2","G3","G4","G5"):
    tot = n = wsum = 0.0; pos = 0; line = f"{LBL[g]:>36} "
    for c in CELLS:
        a_, nc, E, w = D[c][g]
        line += f"{E:>+11.3f}"; tot += nc*E; n += nc; wsum += nc*w
        if E > 0: pos += 1
    E = tot/n; w = wsum/n
    sd, lam, t = stats(n, E, w)
    res[g] = (E, n, w, lam, t, pos)
    print(line + f"{E:>+9.3f}{pos:>5}/4{n:>7.0f}{lam:>8.4f}{t:>+7.2f}")

print("\nHOW MUCH DO THE TWO FAMILIES OVERLAP?")
print(f"{'cell':>12}{'F0 arms':>9}{'that are F6':>13}{'F6 arms':>9}{'that are F0':>13}")
a=b=c_=d=0
for c in CELLS:
    t = T[c]
    print(f"{c:>12}{t[0]:>9}{t[3]:>12.1f}%{t[7]:>9}{t[10]:>12.1f}%")
    a += t[0]; b += t[0]*t[3]/100; c_ += t[7]; d += t[7]*t[10]/100
print(f"{'POOLED':>12}{a:>9}{100*b/a:>12.1f}%{c_:>9}{100*d/c_:>12.1f}%")
print(f"\n  Jaccard(F0, F6) = |A n B| / |A u B| = {b:.0f} / {a+c_-b:.0f} = {b/(a+c_-b):.3f}")
print("  -> only 11.9% of sweep arms are also range-regime arms, and 14.7% of")
print("     range arms are also sweeps. They are NOT the same effect.")

print("\nTAG CENSUS on F0 (sweep) arms -- what else is true when a sweep fires?")
print(f"{'cell':>12}{'range extr':>12}{'low ADX':>10}{'HTF align':>11}{'reclaim':>10}{'displace':>10}")
for c in CELLS:
    t = T[c]
    print(f"{c:>12}{t[1]:>11.1f}%{t[2]:>9.1f}%{t[4]:>10.1f}%{t[5]:>9.1f}%{t[6]:>9.1f}%")
print("\nTAG CENSUS on F6 (range extreme) arms")
print(f"{'cell':>12}{'sweep<=12b':>12}{'HTF align':>11}")
for c in CELLS:
    t = T[c]
    print(f"{c:>12}{t[8]:>11.1f}%{t[9]:>10.1f}%")

print("\n" + "="*96)
print("DECOMPOSITION -- does either family survive with the other removed?")
for g, name in (("G0","F0 with every F6 condition ABSENT"),
                ("G1","F6 with no sweep present     ")):
    E, n, w, lam, t, pos = res[g]
    print(f"  {name}: E={E:+.3f}R  n={n:.0f}  signs {pos}/4  lambda {lam:.4f}  t {t:+.2f}")
print("  Both survive standalone -> neither family is an artefact of the other.")
print("\nINTERSECTION (small n, do not over-read):")
for g in ("G2","G5"):
    E, n, w, lam, t, pos = res[g]
    print(f"  {LBL[g]:>34}: E={E:+.3f}R  n={n:.0f}  signs {pos}/4  t {t:+.2f}")
