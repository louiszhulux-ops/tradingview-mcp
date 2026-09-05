#!/usr/bin/env python3
"""
Pool the ICT 2022 model screen across 4 markets, 15m.

Each filter is nested inside the next, so comparing rows shows what each beat
of the published sequence actually contributes:
  raid+MSS -> +displacement -> +FVG retracement entry -> +killzone
"""
from math import sqrt

# (n, meanR, t) per market, from the V24 screen
D = {
 "0 raid+MSS L":  [(137,-0.055,-0.62),(179,-0.052,-0.68),(159,-0.215,-2.63),(181,-0.118,-1.54)],
 "1 raid+MSS S":  [(148,-0.012,-0.13),(178, 0.077, 0.92),(163,-0.056,-0.67),(157, 0.002, 0.02)],
 "2 +disp L":     [(129,-0.065,-0.71),(163,-0.066,-0.82),(146,-0.271,-3.21),(169,-0.132,-1.66)],
 "3 +disp S":     [(139,-0.020,-0.22),(172, 0.074, 0.87),(154,-0.046,-0.55),(152,-0.015,-0.17)],
 "4 +FVG L":      [( 57, 0.074, 0.49),( 66,-0.040,-0.28),( 60,-0.139,-0.93),( 65, 0.041, 0.28)],
 "5 +FVG S":      [( 48,-0.105,-0.61),( 67,-0.093,-0.66),( 60, 0.044, 0.30),( 66,-0.030,-0.21)],
 "6 +killzone L": [( 13, 0.764, 2.86),( 23,-0.186,-0.90),( 12,-0.044,-0.14),(  9, 0.093, 0.25)],
 "7 +killzone S": [(  7, 0.053, 0.13),( 15,-0.367,-1.38),( 10,-0.183,-0.54),( 11, 0.042, 0.15)],
}
MK = ["MGC","MNQ","MCL","6E"]

print(f"{'variant':>15} {'N':>5} {'pooled meanR':>13} {'pooled t':>9} {'mkts +':>7}   per-market meanR")
for k, rows in D.items():
    N = sum(r[0] for r in rows)
    # pooled mean weighted by n; pooled se from each market's se = mean/t
    tot = sum(r[0] * r[1] for r in rows)
    m = tot / N
    var = 0.0
    for n, mu, t in rows:
        se = abs(mu / t) if t not in (0,) else 0.0
        sd = se * sqrt(n) if se else 0.0
        var += (n - 1) * sd * sd + n * (mu - m) ** 2
    sd_p = sqrt(var / (N - 1)) if N > 1 else 0.0
    t_p = m / (sd_p / sqrt(N)) if sd_p > 0 else 0.0
    pos = sum(1 for r in rows if r[1] > 0)
    detail = "  ".join(f"{mk} {r[1]:+.3f}" for mk, r in zip(MK, rows))
    print(f"{k:>15} {N:>5} {m:>+13.4f} {t_p:>9.2f} {pos:>5}/4   {detail}")

print("\nthe killzone-long cell that looked significant:")
n, mu, t = D["6 +killzone L"][0]
print(f"  gold alone: n={n}, meanR {mu:+.3f}, t={t:.2f}")
print(f"  other three: " + ", ".join(f"{mk} {r[1]:+.3f} (n={r[0]})"
      for mk, r in zip(MK[1:], D["6 +killzone L"][1:])))
tot_n = sum(r[0] for r in D["6 +killzone L"])
print(f"  pooled n across all four markets = {tot_n} -- far too few to conclude anything")
