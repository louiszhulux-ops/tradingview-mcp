#!/usr/bin/env python3
"""
Monte Carlo evaluation simulator (brief section 34).

Reports probability of passing within 2/3/5/7/14 days, days-to-pass
percentiles, drawdown and bust probability -- under the VERIFIED LucidFlex
rules (end-of-day MLL until lock, 50% consistency, no daily loss limit).

Trades can be generated from (win rate, RR) or replayed from an empirical
R-multiple sequence.
"""
import random
from statistics import median
from prop_rules import LUCIDFLEX, EvalState


def simulate(acct, win_rate, rr, trades_per_day, risk, max_days=30,
             daily_stop_R=2.5, daily_target_days=3, seed=None, empirical=None):
    """
    daily_target_days: the bot aims to make target/N per day and STOPS when hit,
    because consistency punishes overshooting. This is the single most important
    behavioural rule in the whole system.
    """
    rng = random.Random(seed)
    st = EvalState(acct)
    day_target = acct.ideal_daily_target(daily_target_days)

    for _ in range(max_days):
        if st.status != "running":
            break
        day_pnl = 0.0
        for _t in range(trades_per_day):
            # stop for the day once the daily target is reached
            if day_pnl >= day_target:
                break
            # daily stop
            if day_pnl <= -daily_stop_R * risk:
                break
            if empirical:
                r = rng.choice(empirical)
            else:
                r = rr if rng.random() < win_rate else -1.0
            pnl = r * risk
            st.apply_trade(pnl, worst_excursion=abs(min(0.0, pnl)))
            if st.status != "running":
                break
            day_pnl += pnl
        st.close_day()
    return st


def run(acct, win_rate, rr, tpd, risk, n=20000, **kw):
    passes, busts, days, peaks = 0, 0, [], []
    within = {2: 0, 3: 0, 5: 0, 7: 0, 14: 0}
    for i in range(n):
        st = simulate(acct, win_rate, rr, tpd, risk, seed=i, **kw)
        if st.status == "pass":
            passes += 1
            d = st.days_elapsed()
            days.append(d)
            for k in within:
                if d <= k:
                    within[k] += 1
        elif st.status == "bust":
            busts += 1
    e = win_rate * rr - (1 - win_rate)
    return dict(exp=e, pas=passes / n, bust=busts / n,
                med=median(days) if days else None,
                within={k: v / n for k, v in within.items()})


if __name__ == "__main__":
    a = LUCIDFLEX["50K"]
    print(f"{a.name}  --  20,000 runs per row, verified LucidFlex rules")
    print("daily target = target/3 (stop trading when hit; consistency punishes overshoot)")
    print("daily stop = 2.5R;  risk $400/trade;  6 trades/day\n")
    print(f"{'win%':>5} {'RR':>5} {'E(R)':>7} {'pass':>7} {'bust':>6} {'med d':>6} "
          f"{'<=2d':>7} {'<=3d':>7} {'<=5d':>7} {'<=7d':>7} {'<=14d':>7}")
    scen = [
        (0.40, 1.5), (0.45, 1.5), (0.50, 1.5), (0.55, 1.5),
        (0.50, 1.0), (0.55, 1.0), (0.60, 1.0), (0.65, 1.0), (0.75, 1.0),
    ]
    for w, rr in scen:
        r = run(a, w, rr, 6, 400)
        wi = r["within"]
        print(f"{w*100:>4.0f}% {rr:>5.1f} {r['exp']:>+7.3f} {r['pas']:>6.1%} "
              f"{r['bust']:>5.1%} {str(r['med']):>6} "
              f"{wi[2]:>6.1%} {wi[3]:>6.1%} {wi[5]:>6.1%} {wi[7]:>6.1%} {wi[14]:>6.1%}")

def sweep():
    a = LUCIDFLEX["50K"]
    print("\n" + "="*78)
    print("2-DAY CONFIGURATION: daily target = $1,500 (target/2), the consistency floor")
    print(f"{'win%':>5} {'RR':>5} {'risk':>6} {'pass':>7} {'bust':>6} {'<=2d':>7} {'<=3d':>7} {'<=5d':>7} {'<=7d':>7}")
    for w, rr in [(0.55,1.5),(0.60,1.0),(0.65,1.0),(0.75,1.0)]:
        for risk in (400, 600, 800):
            r = run(a, w, rr, 6, risk, daily_target_days=2)
            wi = r["within"]
            print(f"{w*100:>4.0f}% {rr:>5.1f} {risk:>6} {r['pas']:>6.1%} {r['bust']:>5.1%} "
                  f"{wi[2]:>6.1%} {wi[3]:>6.1%} {wi[5]:>6.1%} {wi[7]:>6.1%}")

    print("\n" + "="*78)
    print("RISK SWEEP at a realistic mechanical edge (E = +0.18R, the 7-day requirement)")
    print("modelled as 55% win at 1.5:1 -> E = +0.325R, and 47% at 1.5 -> E = +0.175R")
    print(f"{'edge':>18} {'risk':>6} {'tpd':>4} {'pass':>7} {'bust':>6} {'<=5d':>7} {'<=7d':>7} {'<=14d':>7}")
    for lbl, w, rr in [("E=+0.175R (47%@1.5)", 0.47, 1.5), ("E=+0.325R (55%@1.5)", 0.55, 1.5)]:
        for risk in (300, 400, 500, 700):
            r = run(a, w, rr, 6, risk, daily_target_days=3)
            wi = r["within"]
            print(f"{lbl:>18} {risk:>6} {6:>4} {r['pas']:>6.1%} {r['bust']:>5.1%} "
                  f"{wi[5]:>6.1%} {wi[7]:>6.1%} {wi[14]:>6.1%}")

sweep()

def final():
    a = LUCIDFLEX["50K"]
    print("\n" + "="*78)
    print("PASS PROBABILITY AT THE CROSS-VALIDATED MEASURED EDGE")
    print("3 setups surviving both markets: +0.0884R over 367 trades")
    print("(modelled as 43.5% win at 1.5:1 -> E = +0.088R)\n")
    print(f"{'risk':>6} {'tpd':>4} {'pass':>7} {'bust':>6} {'med d':>6} "
          f"{'<=2d':>7} {'<=3d':>7} {'<=5d':>7} {'<=7d':>7} {'<=14d':>7}")
    for risk in (250, 300, 400, 500):
        for tpd in (4, 6):
            r = run(a, 0.435, 1.5, tpd, risk, daily_target_days=3)
            wi = r["within"]
            print(f"{risk:>6} {tpd:>4} {r['pas']:>6.1%} {r['bust']:>5.1%} "
                  f"{str(r['med']):>6} {wi[2]:>6.1%} {wi[3]:>6.1%} {wi[5]:>6.1%} "
                  f"{wi[7]:>6.1%} {wi[14]:>6.1%}")

    print("\nfor comparison, the same table at the edge a 7-day pass needs (+0.179R):")
    for risk in (300, 400):
        r = run(a, 0.4716, 1.5, 6, risk, daily_target_days=3)
        wi = r["within"]
        print(f"{risk:>6} {6:>4} {r['pas']:>6.1%} {r['bust']:>5.1%} "
              f"{str(r['med']):>6} {wi[2]:>6.1%} {wi[3]:>6.1%} {wi[5]:>6.1%} "
              f"{wi[7]:>6.1%} {wi[14]:>6.1%}")

final()
