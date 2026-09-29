"""Frozen V53 parameters, transcribed from V53_EXECUTED_BUILD.pine.

Every value here is an `input.*` in the artifact's "Frozen" group, or a
structural constant of the state machine. **Nothing in this module may be
changed**: a different value is a different strategy, not a configuration.
"""

from __future__ import annotations

from typing import Final

from bot.guards import FE_MS

#: sha256 of the artifact this implementation reproduces (Phase 15 anchor).
EXECUTED_SHA256: Final[str] = (
    "2dafbafd5f6731e93c6fc4a2d55048bb32d5c0d75581ed7fffd877a0cf58efe6"
)
STRATEGY_ID: Final[str] = "V53"

# ---- the "Frozen" input group, in artifact order ----
TGT_R: Final[float] = 5.0        # tgtR     target, in R
BUF_ATR: Final[float] = 0.20     # bufATR   stop buffer, × 5m ATR
MIN_WICK: Final[float] = 0.10    # minWick  minimum sweep depth, × 5m ATR
DISP_MIN: Final[float] = 1.50    # dispMin  displacement range, × 5m ATR
DISP_WAIT: Final[int] = 12       # dispWait 5m bars, sweep → displacement
RET_BARS: Final[int] = 24        # retBars  5m bars, FVG retest window
MIN_RATR: Final[float] = 0.05    # minRatr  minimum R / ATR
MAX_RATR: Final[float] = 3.00    # maxRatr  maximum R / ATR
MAX_BARS: Final[int] = 144       # maxBars  5m bars in trade before timeout
COST_USD: Final[float] = 3.00    # costUSD  round-trip drag
SWING_LEN: Final[int] = 10       # swLen    5m swing pivot half-width
LTF_SWING_LEN: Final[int] = 3    # lSw      LTF swing pivot half-width

# ---- structural ----
SLOT_COUNT: Final[int] = 24                      # SP
RING_SIZE: Final[int] = 2 * LTF_SWING_LEN + 1    # RB = 7
ATR_LENGTH: Final[int] = 14                      # ta.atr(14)

#: Asia session window: `hour(time, "UTC") < 7`. **UTC, not the exchange day.**
ASIA_END_HOUR_UTC: Final[int] = 7

# ---- fold boundaries, epoch ms UTC (V53 `FB`, `FC`, `FE`) ----
FOLD_B_START_MS: Final[int] = 1784160000000   # FB  2026-07-16 00:00 UTC
FOLD_C_START_MS: Final[int] = 1786233600000   # FC  2026-08-09 00:00 UTC
FOLD_END_MS: Final[int] = FE_MS               # FE  2026-08-31 00:00 UTC

#: Ring positions used by the FVG test in §4b (`RB-1` newest, `RB-2` middle).
FVG_NEWEST: Final[int] = RING_SIZE - 1
FVG_MIDDLE: Final[int] = RING_SIZE - 2
FVG_OLDEST: Final[int] = RING_SIZE - 3
