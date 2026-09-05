#!/usr/bin/env python3
"""
Does gross expectancy rise with holding horizon?

Same signal (20-bar breakout, market order) at four horizons: stop and target
at h x ATR, time limit scaled by h. Both directions at every horizon so drift
cannot masquerade as edge. Pre-registered bar: both directions positive in at
least 3 of 4 markets.
"""
# gross mean R by (market, horizon) -> (long, short)
G = {
 "MGC": {1:(+0.0363,-0.0141), 2:(+0.0237,+0.0220), 4:(+0.0797,+0.0639), 8:(+0.0553,+0.0025)},
 "MNQ": {1:(-0.0178,-0.0202), 2:(+0.0505,+0.0386), 4:(+0.0156,+0.0278), 8:(-0.0003,+0.0420)},
 "MCL": {1:(-0.0199,-0.0950), 2:(-0.0208,-0.0779), 4:(-0.0310,-0.0694), 8:(+0.0580,-0.0874)},
 "6E":  {1:(-0.0715,-0.0282), 2:(-0.0783,-0.0499), 4:(-0.0776,-0.0210), 8:(-0.0380,+0.0355)},
}
COST = {  # measured cost_R at each horizon
 "MGC": {1:0.0223,2:0.0110,4:0.0055,8:0.0027},
 "MNQ": {1:0.0220,2:0.0104,4:0.0048,8:0.0023},
 "MCL": {1:0.0879,2:0.0439,4:0.0217,8:0.0110},
 "6E":  {1:0.1124,2:0.0558,4:0.0277,8:0.0143},
}

print("cost_R by horizon -- confirms cost falls linearly with stop width")
for m in COST:
    r = COST[m]
    print(f"  {m:>4}: h1 {r[1]:.4f}  h2 {r[2]:.4f}  h4 {r[4]:.4f}  h8 {r[8]:.4f}")

print("\nGROSS expectancy, both directions, by horizon")
print(f"{'horizon':>8} " + " ".join(f"{m:>16}" for m in G) + f" {'mkts both +':>12}")
for h in (1,2,4,8):
    cells = []
    both = 0
    for m in G:
        l, s = G[m][h]
        if l > 0 and s > 0:
            both += 1
        cells.append(f"{l:+.3f}/{s:+.3f}".rjust(16))
    print(f"{h:>7}x " + " ".join(cells) + f" {both:>10}/4")

print("\nPRE-REGISTERED BAR: both directions positive in >= 3 of 4 markets")
for h in (1,2,4,8):
    both = sum(1 for m in G if G[m][h][0] > 0 and G[m][h][1] > 0)
    print(f"  h={h}: {both}/4  ->  {'PASS' if both >= 3 else 'fail'}")

print("\npooled gross across all 4 markets, by horizon:")
for h in (1,2,4,8):
    vals = [v for m in G for v in G[m][h]]
    print(f"  h={h}: {sum(vals)/len(vals):+.4f} R")
