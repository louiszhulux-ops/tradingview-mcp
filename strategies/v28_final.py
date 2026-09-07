#!/usr/bin/env python3
"""Horizon sweep, six markets. Does the effect survive the both-directions bar?"""
G = {  # gross mean R (long, short) by horizon
 "MGC gold":  {2:(+0.0237,+0.0220), 4:(+0.0797,+0.0639), 8:(+0.0553,+0.0025)},
 "MNQ nasdaq":{2:(+0.0505,+0.0386), 4:(+0.0156,+0.0278), 8:(-0.0003,+0.0420)},
 "MCL crude": {2:(-0.0208,-0.0779), 4:(-0.0310,-0.0694), 8:(+0.0580,-0.0874)},
 "6E euro":   {2:(-0.0783,-0.0499), 4:(-0.0776,-0.0210), 8:(-0.0380,+0.0355)},
 "MES s&p":   {2:(-0.0009,-0.0922), 4:(+0.0268,-0.0291), 8:(-0.0114,-0.0209)},
 "6J yen":    {2:(-0.1007,+0.0678), 4:(-0.1295,+0.0112), 8:(-0.1249,+0.1387)},
}
print(f"{'market':>12} " + "  ".join(f"h={h} L/S".rjust(17) for h in (2,4,8)))
for m, d in G.items():
    cells = [f"{d[h][0]:+.3f}/{d[h][1]:+.3f}".rjust(17) for h in (2,4,8)]
    print(f"{m:>12} " + "  ".join(cells))

print("\nboth directions positive:")
for h in (2,4,8):
    ok = [m for m in G if G[m][h][0] > 0 and G[m][h][1] > 0]
    print(f"  h={h}: {len(ok)}/6  {ok}")
print("\npre-registered bar was 3 of 4. At 6 markets that is 4 of 6. All fail.")

print("\npooled gross by horizon (all 6 markets, both directions):")
for h in (2,4,8):
    v = [x for m in G for x in G[m][h]]
    print(f"  h={h}: {sum(v)/len(v):+.4f} R")

print("\n--- what the failures look like ---")
print("6J yen  h=8:  long -0.125, short +0.139  -> the yen fell all sample")
print("MES s&p h=2:  long -0.001, short -0.092  -> neither side works")
print("The two markets that pass (gold, nasdaq) are the two strongest trenders.")
print("An effect that only appears in markets that trended, and shows up as")
print("whichever direction they trended, is realised drift -- not an edge you")
print("can rely on before knowing which way the market went.")

print("\n--- and even the best cell does not pass the evaluation ---")
netR, risk, per_year = 0.066, 220.0, 188
print(f"gold h=4: net {netR:+.3f} R, ~{per_year} trades/yr, 1 MGC = ${risk:.0f} risk")
print(f"  -> ${netR*risk:.1f}/trade x {per_year} = ${netR*risk*per_year:,.0f}/year")
print(f"  -> {3000/(netR*risk*per_year)*12:.0f} months to make the $3,000 target")
print(f"  the account allows a $2,000 drawdown; {per_year} trades at this")
print(f"  expectancy would swing far more than that along the way.")
