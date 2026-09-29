"""Closed vocabularies for the V53 contracts.

Every value here is transcribed from the frozen artifact
`trader_v2/p15/executed/V53_EXECUTED_BUILD.pine` (sha256 2dafbafd…). Nothing is
invented, and no member encodes a trading rule — these name states and reasons,
they do not decide anything.
"""

from __future__ import annotations

from enum import Enum, IntEnum


class Direction(str, Enum):
    """V53 runs one direction per instance (`dirMode` 1 = long, -1 = short)."""

    LONG = "L"
    SHORT = "S"

    @property
    def dir_mode(self) -> int:
        return 1 if self is Direction.LONG else -1

    @property
    def sign(self) -> int:
        """+1 long, -1 short. Orientation only, not a price calculation."""
        return 1 if self is Direction.LONG else -1


class Timeframe(str, Enum):
    """The three timeframes V53 touches.

    M5 is the parent bar on which every decision resolves. M1/M3 are the lower
    timeframe selected by `ltfSel`. An LTF stream never substitutes for M5.
    """

    M1 = "1m"
    M3 = "3m"
    M5 = "5m"

    @property
    def minutes(self) -> int:
        return {"1m": 1, "3m": 3, "5m": 5}[self.value]

    @property
    def is_ltf(self) -> bool:
        return self in (Timeframe.M1, Timeframe.M3)


LTF_CHOICES = (Timeframe.M1, Timeframe.M3)


class SlotState(IntEnum):
    """`st` in V53 §"SEQUENCE SLOTS". Integer values are the frozen encoding."""

    FREE = 0
    ARMED = 1
    CHOCH = 2
    RETESTED = 3
    BOS_AWAIT_FVG = 4
    FVG_AWAIT_FILL = 5
    IN_TRADE = 6


#: States V53's §3 deadline loop can expire (`s >= 1 and s <= 3`).
DEADLINE_STATES = (SlotState.ARMED, SlotState.CHOCH, SlotState.RETESTED)

#: States counted as "live" when deciding whether to run §4b (`s0 >= 1 and s0 <= 4`).
LIVE_STATES = (SlotState.ARMED, SlotState.CHOCH, SlotState.RETESTED, SlotState.BOS_AWAIT_FVG)


class SweepSource(str, Enum):
    """Which reference level the sweep took out. A bar may hit several."""

    PD = "PD"   # previous day high/low
    AS = "AS"   # Asia session high/low (hUTC < 7)
    SW = "SW"   # 5m swing pivot, ta.pivot*(swLen=10)


#: V53 renders a combination in this order, joined by "+": "PD+AS", "AS+SW".
SWEEP_SOURCE_ORDER = (SweepSource.PD, SweepSource.AS, SweepSource.SW)


class ExitReason(str, Enum):
    """`rsn` in V53 §1. Integer values are the frozen encoding."""

    STOP = "stop"        # rsn 1
    TARGET = "target"    # rsn 2
    TIMEOUT = "timeout"  # rsn 3

    @property
    def rsn(self) -> int:
        return {"stop": 1, "target": 2, "timeout": 3}[self.value]


class Outcome(str, Enum):
    """`won = flg >= 1` in V53 §1. Not a P&L sign: a timeout is a LOSS."""

    WIN = "WIN"
    LOSS = "LOSS"


class TransitionReason(str, Enum):
    """The complete transition vocabulary, with its V53 counter index.

    B2 emits one of these for every slot state change. The `k_index` mapping is
    the audit trail back to the frozen counters; it is documentation, not logic.
    """

    ARMED = "armed"                                    # K0  st 0 -> 1
    DROPPED_NO_SLOT = "dropped_no_slot"                # K1  no free slot
    CHOCH_CONFIRMED = "choch_confirmed"                # K3  st 1 -> 2
    RETEST_CONFIRMED = "retest_confirmed"              # K6  st 2 -> 3
    BOS_DISPLACEMENT_CONFIRMED = "bos_displacement"    # K8  st 3 -> 4
    BREAK_WITHOUT_DISPLACEMENT = "break_no_disp"       # K9  no transition
    FVG_FOUND = "fvg_found"                            # K11 st 4 -> 5
    FVG_INVALID = "fvg_invalid"                        # K10 st 4 -> 0
    FILLED = "filled"                                  # K12 st 5 -> 6
    R_BAND_REJECT = "r_band_reject"                    # K13 st 5 -> 0
    FVG_RETEST_EXPIRY = "fvg_retest_expiry"            # K18 st 5 -> 0
    EXPIRE_PRE_CHOCH = "expire_pre_choch"              # K15 st 1 -> 0
    EXPIRE_POST_CHOCH = "expire_post_choch"            # K16 st 2 -> 0
    EXPIRE_POST_RETEST = "expire_post_retest"          # K17 st 3 -> 0
    OUTCOME_RECORDED = "outcome_recorded"              # K14 st 6 -> 0

    @property
    def k_index(self) -> int:
        return _K_INDEX[self]

    @property
    def frees_slot(self) -> bool:
        """True when the transition returns the slot to FREE."""
        return self in _FREES_SLOT


_K_INDEX = {
    TransitionReason.ARMED: 0,
    TransitionReason.DROPPED_NO_SLOT: 1,
    TransitionReason.CHOCH_CONFIRMED: 3,
    TransitionReason.RETEST_CONFIRMED: 6,
    TransitionReason.BOS_DISPLACEMENT_CONFIRMED: 8,
    TransitionReason.BREAK_WITHOUT_DISPLACEMENT: 9,
    TransitionReason.FVG_INVALID: 10,
    TransitionReason.FVG_FOUND: 11,
    TransitionReason.FILLED: 12,
    TransitionReason.R_BAND_REJECT: 13,
    TransitionReason.OUTCOME_RECORDED: 14,
    TransitionReason.EXPIRE_PRE_CHOCH: 15,
    TransitionReason.EXPIRE_POST_CHOCH: 16,
    TransitionReason.EXPIRE_POST_RETEST: 17,
    TransitionReason.FVG_RETEST_EXPIRY: 18,
}

_FREES_SLOT = frozenset({
    TransitionReason.FVG_INVALID,
    TransitionReason.R_BAND_REJECT,
    TransitionReason.FVG_RETEST_EXPIRY,
    TransitionReason.EXPIRE_PRE_CHOCH,
    TransitionReason.EXPIRE_POST_CHOCH,
    TransitionReason.EXPIRE_POST_RETEST,
    TransitionReason.OUTCOME_RECORDED,
})

#: The eight assertion counters that must read 0 (V53 §7 "ASSERTS 21-27,32").
ASSERTION_COUNTERS = (21, 22, 23, 24, 25, 26, 27, 32)
