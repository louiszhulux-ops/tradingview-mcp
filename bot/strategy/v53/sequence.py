"""V53 §§1–5 — the 24-slot sequence state machine.

**Section order is load-bearing and is preserved exactly:**

    §1 outcomes → §2 fills → §3 deadline → §4 LTF loop → §5 arm

That ordering is what makes a fill on bar *t* first judged on *t+1* (§1 runs
before §2), and what stops a sequence armed on bar *t* from being served by
bar *t*'s own LTF sub-bars (§5 runs after §4). Reordering these changes results;
a test asserts the order.

Nothing here is vectorised. Each section walks slots 0..23 in index order,
exactly as the artifact's `for i = 0 to SP - 1` loops do, because slot order
decides which slot wins a contested transition.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from bot.contracts.enums import Direction, ExitReason, SlotState
from bot.strategy.v53.constants import (
    DISP_MIN, DISP_WAIT, FVG_MIDDLE, FVG_NEWEST, FVG_OLDEST, LTF_SWING_LEN,
    MAX_BARS, MAX_RATR, MIN_RATR, RET_BARS, RING_SIZE, SLOT_COUNT, TGT_R,
)
from bot.strategy.v53.ltf import LtfState, RingEntry
from bot.strategy.v53.numeric import NA, is_na


@dataclass
class Slot:
    """One sequence slot: every V53 parallel array, one object.

    Strategy fields first, then the ten the artifact marks
    "measurement only; no strategy state".
    """

    index: int
    state: SlotState = SlotState.FREE
    sweep_bar_index: int = 0            # swB
    stop: float = NA                    # stp
    atr_at_arm: float = NA              # aRf
    choch_level: float = NA             # cLvl
    pivot_ref: float = NA               # pRef
    choch_pivot_index: int = -1         # cPvI
    choch_ltf_index: int = -1           # cBar
    retest_ltf_index: int = -1          # rBar
    displacement_ltf_index: int = -1    # dBar
    entry: float = NA                   # ent
    r_distance: float = NA              # rr
    fvg_wait_bars: int = 0              # wt
    bars_in_trade: int = 0              # bIn
    max_favourable_r: float = 0.0       # mfe
    max_adverse_r: float = 0.0          # mae
    target_reached: int = 0             # flg
    # ---- ledger fields ----
    ledger_sweep_ts_ms: int = 0         # lSwT
    ledger_sweep_kind: str = ""         # lSwG
    ledger_sweep_extreme: float = NA    # lSwX
    ledger_choch_ts_ms: int = 0         # lChT
    ledger_retest_ts_ms: int = 0        # lRtT
    ledger_bos_ts_ms: int = 0           # lBoT
    ledger_bos_level: float = NA        # lBoL
    ledger_fvg_low: float = NA          # lFlo
    ledger_fvg_high: float = NA         # lFhi
    ledger_entry_ts_ms: int = 0         # lEnT


@dataclass
class Outcome:
    """One resolved trade, as §1 produces it."""

    slot_index: int
    exit_reason: ExitReason
    won: bool
    r_gross: float          # vPre — +tgtR or −1
    r_net: float            # v
    pnl_usd: float          # usd
    bars_in_trade: int      # b
    max_favourable_r: float
    max_adverse_r: float
    slot: Slot              # snapshot for the ledger row


@dataclass
class Counters:
    """The `K` array. Indices are the artifact's, so the audit stays line-by-line."""

    k: list[int] = field(default_factory=lambda: [0] * 36)

    def bump(self, index: int, amount: int = 1) -> None:
        self.k[index] += amount

    def __getitem__(self, index: int) -> int:
        return self.k[index]

    # Named views onto the funnel, matching the artifact's §7 output table.
    @property
    def sweeps(self) -> int: return self.k[0]
    @property
    def dropped_no_slot(self) -> int: return self.k[1]
    @property
    def max_concurrent(self) -> int: return self.k[2]
    @property
    def choch(self) -> int: return self.k[3]
    @property
    def retests(self) -> int: return self.k[6]
    @property
    def bos_displacement(self) -> int: return self.k[8]
    @property
    def break_no_displacement(self) -> int: return self.k[9]
    @property
    def no_fvg(self) -> int: return self.k[10]
    @property
    def fvg(self) -> int: return self.k[11]
    @property
    def fills(self) -> int: return self.k[12]
    @property
    def r_band_rejects(self) -> int: return self.k[13]
    @property
    def outcomes(self) -> int: return self.k[14]
    @property
    def expire_pre_choch(self) -> int: return self.k[15]
    @property
    def expire_post_choch(self) -> int: return self.k[16]
    @property
    def expire_post_retest(self) -> int: return self.k[17]
    @property
    def fvg_retest_expiry(self) -> int: return self.k[18]
    @property
    def fold_bars(self) -> int: return self.k[30]
    @property
    def fold_bars_with_ltf(self) -> int: return self.k[29]
    @property
    def ltf_bars_seen(self) -> int: return self.k[31]

    @property
    def assertions(self) -> tuple[int, ...]:
        """K21–K27 and K32. All must read 0."""
        return tuple(self.k[i] for i in (21, 22, 23, 24, 25, 26, 27, 32))

    @property
    def assertions_all_zero(self) -> bool:
        return not any(self.assertions)


class SequenceMachine:
    """The 24 slots and the five sections that act on them."""

    def __init__(self, direction: Direction, point_value: float,
                 cost_usd: float, counters: Counters) -> None:
        self.direction = direction
        self.is_long = direction is Direction.LONG
        self.point_value = point_value
        self.cost_usd = cost_usd
        self.counters = counters
        self.slots = [Slot(index=i) for i in range(SLOT_COUNT)]

    # ---------------------------------------------------------------- §1

    def section1_outcomes(self, high: float, low: float) -> list[Outcome]:
        """§1 OUTCOME LOOP. Runs **first**, so a fill on bar t is first judged on t+1.

        Adverse is tested before favourable, so a bar that reaches both the stop
        and the target within its range resolves as a stop.
        """
        resolved: list[Outcome] = []
        for slot in self.slots:
            if slot.state is not SlotState.IN_TRADE:
                continue
            entry, r = slot.entry, slot.r_distance
            bars = slot.bars_in_trade + 1
            slot.bars_in_trade = bars

            adverse = (entry - low) / r if self.is_long else (high - entry) / r
            favourable = (high - entry) / r if self.is_long else (entry - low) / r

            if adverse > slot.max_adverse_r:
                slot.max_adverse_r = adverse

            done = False
            reason = 0
            if adverse >= 1.0:
                done, reason = True, 1
            else:
                # mfe is updated only on this branch — asymmetric, reproduced.
                if favourable > slot.max_favourable_r:
                    slot.max_favourable_r = favourable
                if favourable >= TGT_R:
                    slot.target_reached = 1
                    done, reason = True, 2
                elif bars >= MAX_BARS:
                    done, reason = True, 3

            if not done:
                continue

            if bars < 1:
                self.counters.bump(25)  # K25 — 0 by construction, not by validation
            cost_r = self.cost_usd / (r * self.point_value)
            won = slot.target_reached >= 1
            r_gross = TGT_R if won else -1.0
            r_net = r_gross - cost_r
            pnl_usd = r_net * r * self.point_value
            self.counters.bump(14)

            resolved.append(Outcome(
                slot_index=slot.index,
                exit_reason={1: ExitReason.STOP, 2: ExitReason.TARGET, 3: ExitReason.TIMEOUT}[reason],
                won=won, r_gross=r_gross, r_net=r_net, pnl_usd=pnl_usd,
                bars_in_trade=bars,
                max_favourable_r=slot.max_favourable_r,
                max_adverse_r=slot.max_adverse_r,
                slot=Slot(**vars(slot)),
            ))
            slot.state = SlotState.FREE
        return resolved

    # ---------------------------------------------------------------- §2

    def section2_fills(self, high: float, low: float, bar_open_ts_ms: int) -> list[int]:
        """§2 FVG RETEST / FILL LOOP, on 5m bars, within the `retBars` window.

        The fill test is **touch ⇒ fill** on a resting limit, and `bars_in_trade`
        starts at 0 so §1 never judges the fill bar. Both are optimistic and both
        are reproduced deliberately (audit §4.4); do not "fix" them here.
        """
        filled: list[int] = []
        for slot in self.slots:
            if slot.state is not SlotState.FVG_AWAIT_FILL:
                continue
            entry = slot.entry
            hit = low <= entry if self.is_long else high >= entry
            if hit:
                r = abs(entry - slot.stop)
                ratio = r / slot.atr_at_arm
                if MIN_RATR <= ratio <= MAX_RATR:
                    slot.state = SlotState.IN_TRADE
                    slot.r_distance = r
                    slot.bars_in_trade = 0
                    slot.max_favourable_r = 0.0
                    slot.max_adverse_r = 0.0
                    slot.target_reached = 0
                    slot.ledger_entry_ts_ms = bar_open_ts_ms
                    self.counters.bump(12)
                    filled.append(slot.index)
                else:
                    slot.state = SlotState.FREE
                    self.counters.bump(13)
            else:
                slot.fvg_wait_bars += 1
                if slot.fvg_wait_bars >= RET_BARS:
                    slot.state = SlotState.FREE
                    self.counters.bump(18)
        return filled

    # ---------------------------------------------------------------- §3

    def section3_deadline(self, bar_index: int) -> None:
        """§3 DEADLINE — `dispWait` governs sweep → displacement, so stages 1–3 only.

        Counted in **5m chart bars**, not minutes: across a weekend gap 12 bars
        spans two days.
        """
        for slot in self.slots:
            state = int(slot.state)
            if 1 <= state <= 3:
                if bar_index - slot.sweep_bar_index > DISP_WAIT:
                    self.counters.bump(14 + state)  # K15 / K16 / K17
                    slot.state = SlotState.FREE

    # ---------------------------------------------------------------- §4

    def count_live(self) -> int:
        """`nLive` — snapshotted **before** the LTF loop and not recomputed."""
        return sum(1 for slot in self.slots if 1 <= int(slot.state) <= 4)

    def section4_advance(self, ltf: LtfState, entry_ring: RingEntry, atr: float,
                         high_5m: float, low_5m: float) -> None:
        """§4b — advance every live sequence with one LTF bar."""
        h, l, c = entry_ring.high, entry_ring.low, entry_ring.close
        ltf_n = ltf.ltf_bars_seen
        o_value, o_index, o_bar, q_value, q_index = ltf.opposing(self.is_long)

        for slot in self.slots:
            state = slot.state

            if state is SlotState.ARMED:
                if is_na(o_value) or o_bar <= slot.sweep_bar_index:
                    continue
                if not is_na(slot.pivot_ref) and slot.pivot_ref != o_value:
                    self.counters.bump(4)
                slot.pivot_ref = o_value
                broke = c > o_value if self.is_long else c < o_value
                wicked = ((h > o_value and c <= o_value) if self.is_long
                          else (l < o_value and c >= o_value))
                if wicked:
                    self.counters.bump(5)
                if broke:
                    if o_bar <= slot.sweep_bar_index:
                        self.counters.bump(21)   # A21 — CHOCH on an ineligible pivot
                    if o_index + LTF_SWING_LEN == ltf_n:
                        self.counters.bump(32)   # A32
                    slot.choch_level = o_value
                    slot.choch_pivot_index = o_index
                    slot.choch_ltf_index = ltf_n
                    slot.ledger_choch_ts_ms = ltf.newest_ts_ms()
                    slot.state = SlotState.CHOCH
                    self.counters.bump(3)

            elif state is SlotState.CHOCH:
                if ltf_n <= slot.choch_ltf_index:
                    continue
                level = slot.choch_level
                # Exact level, zero tolerance, same polarity. No proximity gate,
                # no timeout, no re-arm — those are other phases' variants.
                retested = l <= level if self.is_long else h >= level
                if retested:
                    slot.retest_ltf_index = ltf_n
                    slot.ledger_retest_ts_ms = ltf.newest_ts_ms()
                    slot.state = SlotState.RETESTED
                    self.counters.bump(6)
                else:
                    distance = l - level if self.is_long else level - h
                    if 0 < distance <= 0.01 * atr:
                        self.counters.bump(7)   # near-miss diagnostic only

            elif state is SlotState.RETESTED:
                if ltf_n <= slot.retest_ltf_index:
                    continue
                bos_value, bos_index = NA, -1
                if not is_na(o_value) and o_index != slot.choch_pivot_index:
                    bos_value, bos_index = o_value, o_index
                elif not is_na(q_value) and q_index != slot.choch_pivot_index:
                    bos_value, bos_index = q_value, q_index
                if is_na(bos_value):
                    continue
                broke = c > bos_value if self.is_long else c < bos_value
                bar_range = h - l
                displaced = bar_range > DISP_MIN * atr and (
                    c > l + 0.6 * bar_range if self.is_long else c < l + 0.4 * bar_range
                )
                if broke and not displaced:
                    self.counters.bump(9)
                if broke and displaced:
                    if bos_index == slot.choch_pivot_index:
                        self.counters.bump(22)   # A22 — BOS on the CHOCH pivot
                    if slot.retest_ltf_index >= ltf_n:
                        self.counters.bump(23)   # A23 — retest not before BOS
                    slot.displacement_ltf_index = ltf_n
                    slot.ledger_bos_ts_ms = ltf.newest_ts_ms()
                    slot.ledger_bos_level = bos_value
                    slot.state = SlotState.BOS_AWAIT_FVG
                    self.counters.bump(8)

            elif state is SlotState.BOS_AWAIT_FVG:
                # The associated FVG is tested at the single LTF bar after the
                # displacement bar, and its middle candle IS that displacement
                # candle. No other FVG qualifies.
                if ltf_n != slot.displacement_ltf_index + 1 or not ltf.ring_full:
                    continue
                if ltf.ring[FVG_MIDDLE].ltf_index != slot.displacement_ltf_index:
                    self.counters.bump(24)   # A24 — middle candle is not the BOS bar
                entry = NA
                far = NA
                if self.is_long:
                    if ltf.ring[FVG_NEWEST].low > ltf.ring[FVG_OLDEST].high:
                        entry = ltf.ring[FVG_OLDEST].high
                        far = ltf.ring[FVG_NEWEST].low
                else:
                    if ltf.ring[FVG_NEWEST].high < ltf.ring[FVG_OLDEST].low:
                        entry = ltf.ring[FVG_OLDEST].low
                        far = ltf.ring[FVG_NEWEST].high
                if is_na(entry):
                    slot.state = SlotState.FREE
                    self.counters.bump(10)
                else:
                    slot.entry = entry
                    slot.ledger_fvg_low = min(entry, far)
                    slot.ledger_fvg_high = max(entry, far)
                    slot.fvg_wait_bars = 0
                    slot.state = SlotState.FVG_AWAIT_FILL
                    self.counters.bump(11)
                    if (low_5m <= entry) if self.is_long else (high_5m >= entry):
                        self.counters.bump(19)   # same-bar touch diagnostic

    # ---------------------------------------------------------------- §5

    def section5_arm(self, bar_index: int, bar_open_ts_ms: int, high: float,
                     low: float, atr: float, sweep_kind: str) -> int | None:
        """§5 ARM NEW SWEEPS. Runs **last**, after the LTF loop.

        Returns the slot index armed, or `None` when every slot is busy.
        """
        self.counters.bump(0)
        busy = sum(1 for slot in self.slots if slot.state is not SlotState.FREE)
        if busy > self.counters[2]:
            self.counters.k[2] = busy

        free = next((slot for slot in self.slots if slot.state is SlotState.FREE), None)
        if free is None:
            self.counters.bump(1)
            return None

        free.state = SlotState.ARMED
        free.sweep_bar_index = bar_index
        free.ledger_sweep_ts_ms = bar_open_ts_ms
        free.ledger_sweep_kind = sweep_kind
        free.ledger_sweep_extreme = low if self.is_long else high
        free.stop = (low - 0.20 * atr) if self.is_long else (high + 0.20 * atr)
        free.atr_at_arm = atr
        free.pivot_ref = NA
        free.choch_pivot_index = -1
        free.choch_ltf_index = -1
        free.retest_ltf_index = -1
        free.displacement_ltf_index = -1
        return free.index
