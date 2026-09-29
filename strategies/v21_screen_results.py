#!/usr/bin/env python3
"""Pool the V21 screen: 8 signals x 4 markets x 2 eras, ~16,000 simulated trades."""
sig = ["0 trendL","1 trendS","2 fadeBrkDn L","3 fadeBrkUp S",
       "4 followBrkUp L","5 followBrkDn S","6 sweepL","7 sweepS"]
mkt = ["MGC","MNQ","MCL","6E"]

IS = {  # mean R, in-sample 2023-09 .. 2024-12
 "0 trendL":        [ 0.1970,-0.0545, 0.0136,-0.1159],
 "1 trendS":        [-0.1726, 0.0109, 0.0420,-0.1194],
 "2 fadeBrkDn L":   [-0.0407,-0.0935,-0.1342,-0.1890],
 "3 fadeBrkUp S":   [-0.1031,-0.0614,-0.0008,-0.0161],
 "4 followBrkUp L": [-0.0313,-0.0930,-0.0400,-0.2038],
 "5 followBrkDn S": [-0.1385, 0.1008,-0.0495,-0.1183],
 "6 sweepL":        [ 0.0995,-0.0443,-0.1301, 0.1653],
 "7 sweepS":        [-0.2171,-0.0046,-0.0430,-0.1240]}
OOS = { # mean R, out-of-sample 2025-01 .. 2026-09
 "0 trendL":        [-0.0691,-0.0933, 0.0158,-0.0822],
 "1 trendS":        [-0.1591, 0.0114,-0.0613, 0.0860],
 "2 fadeBrkDn L":   [-0.2290,-0.1288,-0.0772, 0.0803],
 "3 fadeBrkUp S":   [-0.2418,-0.0028,-0.1764,-0.0710],
 "4 followBrkUp L": [ 0.1216,-0.1212,-0.0147, 0.1049],
 "5 followBrkDn S": [-0.1368,-0.0587,-0.2477,-0.2597],
 "6 sweepL":        [-0.1499,-0.2686,-0.0184,-0.0900],
 "7 sweepS":        [-0.1041,-0.0879,-0.0245, 0.1411]}
COST = 0.08

print(f"{'signal':>16} {'IS +/4':>7} {'OOS +/4':>8} {'IS mean':>9} {'OOS mean':>9} {'verdict':>10}")
passed = []
for s in sig:
    i_pos = sum(1 for v in IS[s] if v > 0)
    o_pos = sum(1 for v in OOS[s] if v > 0)
    im = sum(IS[s]) / 4
    om = sum(OOS[s]) / 4
    ok = i_pos >= 3 and o_pos >= 3
    if ok:
        passed.append(s)
    print(f"{s:>16} {i_pos:>7} {o_pos:>8} {im:>9.4f} {om:>9.4f} {'PASS' if ok else 'fail':>10}")

allv = [v for s in sig for v in IS[s]] + [v for s in sig for v in OOS[s]]
n = len(allv)
net = sum(allv) / n
print(f"\ncells: {n}  (8 signals x 4 markets x 2 eras)")
print(f"pooled NET mean R per trade   : {net:+.4f}")
print(f"cost charged per trade        : {-COST:+.4f}")
print(f"implied GROSS mean R per trade: {net + COST:+.4f}   <-- the edge, before costs")
print(f"cells with positive mean R    : {sum(1 for v in allv if v > 0)}/{n}")
print(f"\nsignals clearing criteria 1 and 2: {passed if passed else 'NONE'}")
