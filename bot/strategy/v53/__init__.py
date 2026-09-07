"""Deterministic Python reproduction of the frozen V53 artifact.

Reproduces `trader_v2/p15/executed/V53_EXECUTED_BUILD.pine` (sha256 2dafbafd…),
the Phase 15 provenance anchor. **Not a reinterpretation**: where V53 is
unusual, it is preserved. See `bot/B2_V53_IMPLEMENTATION_AUDIT.md` for the
Pine-line-to-Python map.
"""

from bot.strategy.v53.constants import EXECUTED_SHA256, STRATEGY_ID
from bot.strategy.v53.engine import SECTION_ORDER, BarOutput, V53Config, V53Engine, in_fold
from bot.strategy.v53.sequence import Counters, Outcome, SequenceMachine, Slot

__all__ = [
    "EXECUTED_SHA256", "STRATEGY_ID", "SECTION_ORDER", "BarOutput",
    "V53Config", "V53Engine", "in_fold", "Counters", "Outcome",
    "SequenceMachine", "Slot",
]
