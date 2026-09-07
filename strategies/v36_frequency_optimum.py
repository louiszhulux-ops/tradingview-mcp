#!/usr/bin/env python3
"""
Where does the fewer-larger-trades direction actually optimise?

V35 measured the execution drag as roughly FIXED in dollars per trade:
  commission ~$1.04 RT + ~1 tick slippage each way ~$2.00 + fill-timing ~$1.35
  = D ~ $4.40, largely independent of how wide the stop is.

So with stop s dollars/contract and gross R-edge g:
    net E(s) = g - D/s          (drag shrinks as a fraction of R)
    L(s)     = MLL / s          (buffer in R coarsens)
    U(s)     = target / s

P(pass) depends on lambda*L and lambda*U, lambda = 2E/sd^2. Maximising
lambda*L over s gives an interior optimum -- wider is NOT monotonically better.
"""
import math

D_DRAG = 4.40
MLL, TGT, SD = 2000.0, 3000.0, 1.43

def ppass(E, s):
    if E <= 0: return 0.0
    lam = 2*E/(SD*SD)
    L, U = MLL/s, TGT/s
    return (1-math.exp(-lam*L))/(1-math.exp(-lam*(U+L)))

print("Drag D = $4.40/trade fixed.  MLL $2,000, target $3,000, sd 1.43R.\n")
print(f"{'stop $':>8} {'L (R)':>7} {'U (R)':>7} | " + " | ".join(
      f"g={g:.2f}" for g in (0.06, 0.08, 0.12, 0.20)))
print(f"{'':>8} {'':>7} {'':>7} | " + " | ".join("  net   P(pass)" for _ in range(4)))
best = {}
for s in (33, 50, 75, 100, 150, 200, 300, 450, 700, 1000):
    row = f"{s:>8} {MLL/s:>7.1f} {TGT/s:>7.1f} |"
    for g in (0.06, 0.08, 0.12, 0.20):
        E = g - D_DRAG/s
        p = ppass(E, s)
        if p > best.get(g, (0,0))[0]:
            best[g] = (p, s)
        row += f" {E:>+6.3f} {p:>6.1%} |"
    print(row)

print("\noptimum stop size by gross edge:")
for g,(p,s) in sorted(best.items()):
    print(f"  gross {g:+.2f}R  ->  stop ${s}/contract, P(pass) {p:.1%}"
          f"   (analytic s* = 2D/g = ${2*D_DRAG/g:.0f})")

print("\nwhat that stop means on the instruments available:")
for name, pv, atr_by_tf in (("MGC gold", 10.0, {"5m":2.2,"15m":4.0,"60m":9.0,"4h":22.0,"D":50.0}),
                            ("MNQ nasdaq", 2.0, {"5m":30.0,"15m":55.0,"60m":120.0,"4h":300.0,"D":700.0})):
    print(f"  {name} (${pv:.0f}/pt):")
    for tf, atr in atr_by_tf.items():
        for mult in (1.5, 2.0):
            s = mult*atr*pv
            print(f"     {tf:>3} x {mult}ATR = {mult*atr:6.1f} pts = ${s:7.0f}/contract"
                  f"   L={MLL/s:5.1f}R  drag={D_DRAG/s:.4f}R")
