#!/usr/bin/env python3
"""
What edge does a 2-7 day pass actually require?

This is the arithmetic that should have been done before any strategy was
written. It converts the goal into a required per-trade expectancy, given a
risk budget that survives the max loss limit.
"""
from prop_rules import LUCIDFLEX

a = LUCIDFLEX["50K"]

print(f"{a.name}   target ${a.profit_target:,.0f}   MLL ${a.max_loss_limit:,.0f}\n")

print("Safe risk per trade: how many consecutive full losses must be survivable?")
print("The MLL is checked on the CLOSING balance, so a day's damage is what")
print("matters. With a daily stop at half the buffer:\n")
daily_stop = a.max_loss_limit / 2
print(f"  daily stop = ${daily_stop:,.0f}  (half the ${a.max_loss_limit:,.0f} buffer)")
for r in (200, 300, 400, 500, 750, 1000):
    print(f"    risk ${r:>5}/trade -> {daily_stop/r:.1f} full losses before the day is cut")

print("\n" + "="*74)
print("REQUIRED EXPECTANCY, by days-to-pass and trades-per-day")
print("(daily profit needed = target / days, respecting consistency)\n")
print(f"{'days':>5} {'$/day':>8} " + "".join(f"{f'{n} trades':>12}" for n in (4, 6, 8, 10)))
for days in (2, 3, 5, 7, 14):
    per_day = a.ideal_daily_target(days)
    row = f"{days:>5} {per_day:>8,.0f} "
    for n in (4, 6, 8, 10):
        r = 400.0   # a risk level that survives 2.5 losses before the daily stop
        need_e = per_day / (r * n)
        row += f"{need_e:>11.3f}R"
    print(row)

print("\n  (at $400 risk per trade)")
print("\nMEASURED expectancies from this project, for comparison:")
meas = [
    ("unconditional trigger, market order",      -0.021),
    ("+ resting limit instead of market",        -0.001),
    ("+ trade with-trend, avoid chop",           +0.023),
    ("+ require a meaningful location",          +0.040),
    ("best single measured cell (V30, 3 mkts)",  +0.060),
]
for lbl, e in meas:
    print(f"  {lbl:>42}: {e:+.3f}R")

print("\n" + "="*74)
print("WHAT EACH MEASURED EDGE DELIVERS (at $400 risk, 6 trades/day)")
print(f"{'expectancy':>12} {'$/day':>9} {'days to $3,000':>16} {'verdict':>12}")
for lbl, e in meas:
    per = e * 400 * 6
    if per <= 0:
        print(f"{e:>11.3f}R {per:>9,.0f} {'never':>16} {'fail':>12}")
    else:
        d = a.profit_target / per
        v = "2-7 day" if d <= 7 else "slow" if d <= 21 else "fail"
        print(f"{e:>11.3f}R {per:>9,.0f} {d:>16.1f} {v:>12}")

print("\n" + "="*74)
print("THE GAP")
need2 = a.ideal_daily_target(2) / (400 * 6)
need7 = a.ideal_daily_target(7) / (400 * 6)
best = 0.060
print(f"  needed for a 2-day pass : {need2:.3f}R per trade")
print(f"  needed for a 7-day pass : {need7:.3f}R per trade")
print(f"  best measured           : {best:.3f}R per trade")
print(f"  -> 2-day pass is {need2/best:.1f}x beyond the measured edge")
print(f"  -> 7-day pass is {need7/best:.1f}x beyond the measured edge")
print(f"\n  Raising risk closes the gap linearly. For a 7-day pass at {best:.3f}R:")
r_need = a.ideal_daily_target(7) / (best * 6)
print(f"    required risk = ${r_need:,.0f}/trade with 6 trades/day")
print(f"    that is {r_need/a.max_loss_limit:.0%} of the entire MLL buffer per trade,")
print(f"    so {a.max_loss_limit/r_need:.1f} losses in a day would breach it.")
