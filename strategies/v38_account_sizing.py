#!/usr/bin/env python3
"""
Which (contract, account) pairs are survivable?

The binding test is DOLLAR drawdown vs DOLLAR max-loss-limit. It is invariant
to stop width: tightening the stop shrinks R but lengthens losing streaks in R,
leaving the dollar drawdown roughly unchanged.
"""
import sys; sys.path.insert(0, '/home/user/tradingview-mcp/trader')
from prop_rules import LUCIDFLEX
from montecarlo import run

# contract: (avg R, trades/day, stop $, empirical max DD $)   1 concurrent, real costs
C = {
 "MGC micro gold":   (0.1178, 1.39, 105.56, 1424.40),
 "MNQ micro nasdaq": (0.2205, 2.51,  81.78, 2077.00),
 "SIL micro silver": (0.3784, 1.90, 238.88, 3023.84),
 "SIL @1.0xATR":     (0.3499, 2.33, 159.25, 2329.88),
 "SIL @0.75xATR":    (0.3147, 2.53, 119.44, 2416.32),
}
print("Empirical dollar drawdown vs each account's max loss limit\n")
print(f"{'contract':>18} {'avg R':>8} {'maxDD $':>9} " +
      "".join(f"{k:>9}" for k in LUCIDFLEX))
for name,(E,tpd,s,dd) in C.items():
    row = f"{name:>18} {E:>+8.4f} {dd:>9.0f} "
    for k,a in LUCIDFLEX.items():
        row += f"{('ok' if dd < a.max_loss_limit else 'BUST'):>9}"
    print(row)

print("\nThe stop width does not rescue SIL: $3,024 / $2,330 / $2,416 across")
print("1.5 / 1.0 / 0.75 xATR. The dollar drawdown is ~constant.\n")
print("="*80)
print("Pass probability where the pair is survivable (verified LucidFlex rules)\n")
print(f"{'contract':>18} {'account':>8} {'E':>9} {'buffer':>8} {'target':>8} "
      f"{'pass':>7} {'bust':>6} {'med d':>7}")
for name,(E,tpd,s,dd) in C.items():
    for k,a in LUCIDFLEX.items():
        if dd >= a.max_loss_limit:
            continue
        r = run(a, (E+1.0)/3.0, 2.0, max(1,int(round(tpd))), s, n=4000,
                max_days=250, daily_target_days=20, daily_stop_R=99.0)
        print(f"{name:>18} {k:>8} {E:>+9.4f} {a.max_loss_limit/s:>7.1f}R "
              f"{a.profit_target/s:>7.1f}R {r['pas']:>6.1%} {r['bust']:>5.1%} "
              f"{str(r['med']):>7}")
