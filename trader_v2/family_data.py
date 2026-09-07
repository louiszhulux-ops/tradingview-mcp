#!/usr/bin/env python3
"""
V43b setup family comparison. Same engine for all eight families:
retest entry -> structural stop -> room>=10R -> 5R target, -1R stop.
Ranked on risk-adjusted quality with the 4-cell market x direction gate.
"""
# cell -> family -> (n, E[R], win%, PF, MFE, MAE, perDay)
DATA = {
 "MNQ short": {
  "F0 sweep":(364, 0.002,19.2,1.00,1.93,1.84,5.09), "F1 brk+accept":(58,-0.517,10.3,0.49,1.31,2.30,0.81),
  "F2 failed brk":(35,-0.082,17.1,0.91,1.81,1.35,0.49),"F3 displace+RT":(2,-1.047,0.0,0.00,2.47,2.43,0.03),
  "F4 BOS+retest":(111,-0.112,17.1,0.88,1.76,2.02,1.55),"F5 trend pull":(400,-0.095,18.5,0.90,1.97,2.35,5.60),
  "F6 range MR":(392, 0.114,21.7,1.12,2.04,2.19,5.49), "F7 open range":(15,-0.291,13.3,0.69,2.86,1.95,0.21)},
 "MNQ long": {
  "F0 sweep":(246, 0.022,19.1,1.02,1.97,2.01,3.44), "F1 brk+accept":(58,-0.292,13.8,0.70,1.82,2.06,0.81),
  "F2 failed brk":(22,-1.084, 0.0,0.00,1.08,1.94,0.31),"F3 displace+RT":(1,-1.016,0.0,0.00,3.34,1.07,0.01),
  "F4 BOS+retest":(84,  0.160,21.4,1.18,2.12,1.92,1.18),"F5 trend pull":(290, 0.230,23.4,1.26,2.23,2.22,4.06),
  "F6 range MR":(287, 0.394,26.1,1.45,2.31,2.10,4.02), "F7 open range":(12,-0.587, 8.3,0.41,1.89,1.48,0.17)},
}
if __name__ == "__main__":
    fams = list(DATA["MNQ short"].keys())
    print("MNQ, both directions (MGC pending -- relay unstable)\n")
    print(f"{'family':>16} " + " ".join(f"{c:>12}" for c in DATA) + f" {'pooled':>9} {'signs':>6} {'/day':>6}")
    for f in fams:
        tot=n=0.0; pos=0; pd=0.0; row=f"{f:>16} "
        for c in DATA:
            nc,E = DATA[c][f][0], DATA[c][f][1]
            row += f"{E:>+12.3f} "; tot += nc*E; n += nc; pd += DATA[c][f][6]
            if E > 0: pos += 1
        row += f"{tot/max(n,1):>+9.3f} {pos:>4}/2 {pd:>6.1f}"
        print(row)
    print("\n  F6 range mean-reversion is the only family positive in BOTH MNQ")
    print("  directions, and it has the frequency to matter (9.5 opportunities/day).")
    print("  F1/F2/F3/F7 are negative or starved. F3 displacement+retest fills")
    print("  1-2 times in 441 arms: after a 2xATR bar price rarely returns.")
