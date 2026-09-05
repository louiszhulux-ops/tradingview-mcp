#!/usr/bin/env python3
"""
Human label vs bot label, on the same market events.

Human label  = the THESIS the trader stated (what they expected AFTER entry),
               taken from their own written narrative, not from my inference.
Bot label    = what my opportunity engine actually generates at that same
               structure, using the family definitions as they stand.
"""
ROWS = [
  # id, source, human thesis, event the bot sees, bot's generated trade, agree?
  ("N1","narrative","CONTINUATION short","trend leg, no sweep, no range extreme",
       "nothing armed",                     "NO EVENT"),
  ("N2","narrative","CONTINUATION short","sweep of the Asia LOW",
       "F0 LONG (fade the swept low)",      "OPPOSITE"),
  ("N3","narrative","CONTINUATION long", "Asia spike breaks highs (inferred)",
       "F0 SHORT (fade the swept high)",    "OPPOSITE"),
  ("A1","Aug 31 verified","CONTINUATION long","pullback inside an intraday rally",
       "F5 LONG (trend pullback)",          "SAME-but-rejected"),
  ("A2","Aug 31 verified","REVERSAL short",  "sweep of the session HIGH",
       "F0 SHORT (fade the swept high)",    "SAME"),
  ("L1","loss note","REVERSAL short",        "rally into an unmitigated OB at a range high",
       "F6 SHORT (fade the range extreme)", "SAME"),
]
print("HUMAN-vs-BOT CONFUSION MATRIX  (n = 6 recoverable manual trades)\n")
print(f"{'#':<3}{'human thesis':<20}{'what the bot generates at the same event':<38}{'verdict':<18}")
print("-"*79)
for i,(id_,src,human,ev,bot,verd) in enumerate(ROWS):
    print(f"{id_:<3}{human:<20}{bot:<38}{verd:<18}")
print("-"*79)

cats = ["SAME","SAME-but-rejected","OPPOSITE","NO EVENT"]
print(f"\n{'':<24}" + "".join(f"{c:>20}" for c in cats))
for thesis in ("CONTINUATION","REVERSAL"):
    row = [sum(1 for r in ROWS if r[2].startswith(thesis) and r[5]==c) for c in cats]
    print(f"human {thesis:<18}" + "".join(f"{v:>20}" for v in row))

print("""
READING

  The bot reproduces 2 of 2 human REVERSAL trades, from families it keeps
  (F0 fade, F6 fade), in the correct direction.

  The bot reproduces 0 of 4 human CONTINUATION trades:
    - 2 it trades in the OPPOSITE direction, because F0 places its limit at
      the swept level and fills on the return TO it, which is a fade by
      construction whatever the context;
    - 1 it never arms at all (no sweep, no range extreme -- it is a trend leg);
    - 1 it does get directionally right, but only through F5 trend-pullback,
      the family the setup comparison rejected at 1/4 signs.

  The disagreement is therefore entirely on the continuation half of the
  human's process, and it is a disagreement about DIRECTION and ARMING, not
  about which bars are interesting. Both sides look at the same events.
""")
