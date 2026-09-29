#!/usr/bin/env python3
"""
Does win rate rise fast enough as the target tightens?

You were right that win rate rises. The question is whether it rises faster
than the breakeven line. It does not -- and the gap gets WIDER, not narrower,
which is the opposite of the intuition.

Two reference lines matter:
  breakeven win rate  p_be   = (1 + c) / (RR + 1)          c = 0.08R of cost
  random-walk win rate p_rw  = 1 / (RR + 1)   -- a driftless price with a stop
                                                 at -1R and target at +RR hits
                                                 the target this often by pure
                                                 chance, no skill involved
"""
C = 0.08
# best observed win% on gold 15m at each reward:risk, from the V23 screen
obs = {1.5: ("7 sweepS",   41.8),
       1.0: ("0 trendL",   52.1),
       0.5: ("1 trendS",   67.8),
       0.33:("5 follBrkS", 74.4)}

print(f"{'RR':>6} {'need':>7} {'chance':>8} {'best obs':>9} {'vs chance':>10} {'vs need':>9}  {'signal':>12}")
for rr in (1.5, 1.0, 0.5, 0.33):
    p_be = (1 + C) / (rr + 1) * 100
    p_rw = 1 / (rr + 1) * 100
    name, o = obs[rr]
    print(f"{rr:>6.2f} {p_be:>6.1f}% {p_rw:>7.1f}% {o:>8.1f}% "
          f"{o - p_rw:>+9.1f} {o - p_be:>+8.1f}  {name:>12}")

print("\nedge over pure chance that would be REQUIRED to break even:")
for rr in (1.5, 1.0, 0.5, 0.33):
    need = ((1 + C) / (rr + 1) - 1 / (rr + 1)) * 100
    print(f"  RR {rr:>4.2f}:  +{need:.1f} percentage points   "
          f"(cost is {C/rr*100:>4.1f}% of each win)")

print("\nWhy tightening the target makes it harder, not easier:")
print("  cost is a fixed fraction of the STOP, but a win only pays RR x stop.")
print("  so a smaller target is eaten by proportionally more cost, and the")
print("  win rate you must beat rises faster than the win rate you actually get.")
