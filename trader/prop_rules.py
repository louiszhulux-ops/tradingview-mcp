#!/usr/bin/env python3
"""
Prop-firm rule engine. Every rule is configurable; nothing is hardcoded.

LucidFlex rules verified from Lucid's documentation and secondary sources,
September 2026. Two details matter more than anything else and were modelled
WRONG in every earlier version of this project:

  1. The Max Loss Limit is END-OF-DAY, computed on the highest CLOSING balance.
     Intraday excursions do NOT trail or tighten it. You can be down the full
     MLL intraday and recover by the close with no penalty. Only AFTER the
     floor locks is a breach checked intraday.

  2. Consistency (largest day / total profit <= 50%) means OVERSHOOTING A DAY
     IS HARMFUL. Making $2,500 on day 1 does not put you 83% of the way to a
     $3,000 target -- it raises the total you now need to $5,000. The correct
     behaviour is a DAILY PROFIT TARGET that stops trading when hit, which is
     the opposite of maximising.
"""
from dataclasses import dataclass, field


@dataclass
class PropAccount:
    name: str
    start_balance: float
    profit_target: float
    max_loss_limit: float          # trailing, on closing balance
    max_micros: int
    max_minis: int
    consistency: float = 0.50      # largest day / total profit must be <= this
    lock_offset: float = 100.0     # floor locks at start + this
    daily_loss_limit: float = 0.0  # 0 = disabled (LucidFlex default)
    mll_intraday_before_lock: bool = False   # verified: EOD only until locked
    mll_intraday_after_lock: bool = True     # verified: intraday once locked

    @property
    def lock_trigger(self) -> float:
        """Closing balance above which the floor locks permanently."""
        return self.start_balance + self.max_loss_limit + self.lock_offset

    @property
    def locked_floor(self) -> float:
        return self.start_balance + self.lock_offset

    def ideal_daily_target(self, days: int) -> float:
        """
        Smallest per-day profit that reaches the target in `days` while keeping
        largest_day / total <= consistency. Equal days are optimal: with N equal
        days the ratio is exactly 1/N, so N >= 1/consistency days are required.
        """
        min_days = int(round(1.0 / self.consistency))
        n = max(days, min_days)
        return self.profit_target / n

    def consistency_ok(self, day_pnls) -> bool:
        wins = [p for p in day_pnls if p > 0]
        total = sum(day_pnls)
        if total <= 0 or not wins:
            return False
        return max(wins) / total <= self.consistency + 1e-9

    def profit_needed_for_consistency(self, day_pnls) -> float:
        """
        Extra profit required so that the largest day is within the threshold.
        If largest day L and total P, we need L/P' <= c, i.e. P' >= L/c.
        """
        wins = [p for p in day_pnls if p > 0]
        if not wins:
            return self.profit_target
        L = max(wins)
        P = sum(day_pnls)
        need_total = max(self.profit_target, L / self.consistency)
        return max(0.0, need_total - P)


LUCIDFLEX = {
    "25K":  PropAccount("LucidFlex 25K",  25_000,  1_250, 1_000, max_micros=20,  max_minis=2),
    "50K":  PropAccount("LucidFlex 50K",  50_000,  3_000, 2_000, max_micros=40,  max_minis=4),
    "100K": PropAccount("LucidFlex 100K", 100_000, 6_000, 3_000, max_micros=60,  max_minis=6),
    "150K": PropAccount("LucidFlex 150K", 150_000, 9_000, 4_500, max_micros=100, max_minis=10),
}


class EvalState:
    """Tracks one evaluation attempt under the rules above."""

    def __init__(self, acct: PropAccount):
        self.a = acct
        self.balance = acct.start_balance
        self.peak_close = acct.start_balance
        self.floor = acct.start_balance - acct.max_loss_limit
        self.locked = False
        self.day_pnls = []
        self.today = 0.0
        self.day_index = 0
        self.status = "running"

    # ---- intraday ----
    @property
    def equity(self):
        return self.balance + self.today

    def room_today(self):
        """How much more the account can lose today before it is unsafe."""
        if self.locked:
            return max(0.0, self.equity - self.floor)
        # before lock the floor only bites at the CLOSE, so the day's budget is
        # what can be lost and still close above the floor
        return max(0.0, self.balance + self.today - self.floor)

    def apply_trade(self, pnl: float, worst_excursion: float = 0.0):
        """worst_excursion is a positive number: the adverse swing during the trade."""
        if self.status != "running":
            return
        if self.locked and self.a.mll_intraday_after_lock:
            if self.equity - worst_excursion < self.floor:
                self.status = "bust"
                return
        self.today += pnl

    def close_day(self):
        if self.status != "running":
            return
        self.balance += self.today
        self.day_pnls.append(self.today)
        self.today = 0.0
        self.day_index += 1
        # EOD breach check
        if self.balance < self.floor:
            self.status = "bust"
            return
        # trail the floor on the new closing balance
        if not self.locked:
            self.peak_close = max(self.peak_close, self.balance)
            self.floor = max(self.floor, self.peak_close - self.a.max_loss_limit)
            if self.balance >= self.a.lock_trigger:
                self.floor = self.a.locked_floor
                self.locked = True
        # pass check
        if self.balance >= self.a.start_balance + self.a.profit_target:
            if self.a.consistency_ok(self.day_pnls):
                self.status = "pass"

    def days_elapsed(self):
        return self.day_index


if __name__ == "__main__":
    a = LUCIDFLEX["50K"]
    print(f"{a.name}: target ${a.profit_target:,.0f}  MLL ${a.max_loss_limit:,.0f}")
    print(f"  floor locks once a CLOSING balance reaches ${a.lock_trigger:,.0f}")
    print(f"  and then sits permanently at ${a.locked_floor:,.0f}")
    print(f"  consistency {a.consistency:.0%} -> a pass needs at least "
          f"{int(round(1/a.consistency))} profitable days\n")
    for d in (2, 3, 5, 7):
        print(f"  ideal daily target for a {d}-day pass: ${a.ideal_daily_target(d):,.0f}")
    print("\n  why overshooting hurts:")
    for d1 in (1500, 2000, 2500, 3000):
        need = a.profit_needed_for_consistency([d1])
        print(f"    day 1 = ${d1:,}  ->  still need ${need:,.0f} more "
              f"(total ${d1+need:,.0f}, not ${a.profit_target:,})")
