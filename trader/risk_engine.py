#!/usr/bin/env python3
"""
Risk engine (brief sections 22-25).

Risk is defined in R and sized from the STOP DISTANCE, never as a fixed
contract count. Risk then scales with evaluation state, not with mood:

  * distance to the MLL floor      -- closer means smaller
  * distance to the profit target  -- near the target, protect it
  * today's P&L                    -- do not give back a good day
  * losing streak                  -- reduce and reassess, never increase
  * setup quality                  -- A+ gets more than B, within limits

Explicitly NOT implemented, per section 24: martingale, loss-chasing,
size-up-on-winning-streak, uncontrolled averaging.
"""
from dataclasses import dataclass


@dataclass
class RiskConfig:
    base_risk_pct: float = 0.150      # of the MLL buffer, per trade
    #  0.15 x $2,000 = $300, which the Monte Carlo shows is the sweet spot:
    #  large enough to reach the target, small enough to survive a bad run
    max_risk_pct: float = 0.250
    min_risk_usd: float = 50.0
    quality_mult: tuple = (1.30, 1.00, 0.65, 0.0)   # A+, A, B, C
    daily_stop_R: float = 2.5
    streak_cut: tuple = (1.0, 1.0, 0.7, 0.5)        # 0,1,2,3+ consecutive losses
    protect_near_target: float = 0.80   # once this fraction of target is banked
    protect_mult: float = 0.60


class RiskEngine:
    def __init__(self, acct, cfg: RiskConfig = None):
        self.a = acct
        self.c = cfg or RiskConfig()

    def risk_for(self, state, quality: int, stop_distance: float,
                 point_value: float, day_pnl: float, loss_streak: int):
        """
        Returns (contracts, risk_dollars, reason). contracts == 0 means no trade.
        """
        buffer_ = state.room_today()
        if buffer_ <= 0:
            return 0, 0.0, "no buffer left"

        qm = self.c.quality_mult[min(quality, len(self.c.quality_mult) - 1)]
        if qm <= 0:
            return 0, 0.0, "setup quality below threshold"

        risk = buffer_ * self.c.base_risk_pct * qm

        # streak: reduce after consecutive losses, never increase after wins
        risk *= self.c.streak_cut[min(loss_streak, len(self.c.streak_cut) - 1)]

        # protect a good day: do not hand back what is already banked
        if day_pnl > 0:
            banked = day_pnl / self.a.profit_target
            if banked > 0.25:
                risk *= max(0.5, 1.0 - banked)

        # protect near the target
        total = state.balance - self.a.start_balance + day_pnl
        if total >= self.c.protect_near_target * self.a.profit_target:
            risk *= self.c.protect_mult

        # daily stop
        if day_pnl <= -self.c.daily_stop_R * (buffer_ * self.c.base_risk_pct):
            return 0, 0.0, "daily stop reached"

        risk = min(risk, buffer_ * self.c.max_risk_pct)
        if risk < self.c.min_risk_usd:
            return 0, 0.0, "risk below minimum viable size"

        per_contract = stop_distance * point_value
        if per_contract <= 0:
            return 0, 0.0, "invalid stop"
        n = int(risk // per_contract)
        # allow one contract if the buffer can absorb it comfortably
        if n < 1:
            if buffer_ > per_contract * 3.0:
                n = 1
            else:
                return 0, 0.0, "one contract too large for remaining buffer"
        n = min(n, self.a.max_micros)
        return n, n * per_contract, "ok"


if __name__ == "__main__":
    from prop_rules import LUCIDFLEX, EvalState
    a = LUCIDFLEX["50K"]
    st = EvalState(a)
    re_ = RiskEngine(a)
    print("MGC micro gold, $10/point. Stop distances in dollars.\n")
    print(f"{'scenario':>34} {'stop$':>6} {'qual':>5} {'ctr':>4} {'risk$':>7}  reason")
    cases = [
        ("fresh account, A+ setup",        0.0, 0, 8.0, 0),
        ("fresh account, A setup",         0.0, 1, 8.0, 0),
        ("fresh account, B setup",         0.0, 2, 8.0, 0),
        ("fresh account, C setup",         0.0, 3, 8.0, 0),
        ("after 2 losses today",        -600.0, 1, 8.0, 2),
        ("after 3 losses today",        -800.0, 1, 8.0, 3),
        ("good day banked +$1,200",     1200.0, 1, 8.0, 0),
        ("wide stop ($40)",                0.0, 1, 40.0, 0),
        ("very wide stop ($150)",          0.0, 1, 150.0, 0),
    ]
    for lbl, dpnl, q, stop, streak in cases:
        n, r, why = re_.risk_for(st, q, stop, 10.0, dpnl, streak)
        print(f"{lbl:>34} {stop:>6.0f} {q:>5} {n:>4} {r:>7.0f}  {why}")

    print("\nnote: risk falls with losing streak and with a banked day, and rises")
    print("with setup quality -- but never with a winning streak (section 24).")
