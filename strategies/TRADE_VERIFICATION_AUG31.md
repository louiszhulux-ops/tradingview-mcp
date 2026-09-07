# Verification: Aug 31 2026 long — first independently checkable trade

Record given: `Aug 31, 10:18AM, Buy, entry 4439-4434, stop 4429, "440+ pips"`
Checked against OANDA:XAUUSD 4H bars.

**Correction to my first pass:** I initially read OANDA's daily bar as the UTC
calendar day. OANDA dailies are anchored at 21:00 UTC, so the bar labelled
"Aug 31" is mostly Sep 1 action (which crashed to 4322). On that misreading I
was about to report the trade as an immediate loss. That was my error. The
corrected 4H reconstruction is below.

## Aug 31 2026, actual UTC sequence

| bar start (UTC) | open | high | low | close |
|---|---|---|---|---|
| 01:00 | 4456.31 | 4463.30 | 4396.52 | 4424.64 |
| 05:00 | 4424.61 | 4449.53 | 4419.37 | 4435.65 |
| **09:00** | **4435.69** | **4464.23** | **4435.44** | 4435.80 |
| 13:00 | 4435.81 | 4448.26 | **4415.75** | 4433.36 |
| 17:00 | 4433.36 | 4455.93 | 4426.30 | 4449.24 |
| 21:00 | 4454.26 | 4461.70 | 4441.85 | 4453.74 |

10:18 resolves to the 09:00–13:00 bar whether it is UTC or UK time, so the
timezone ambiguity does not matter.

## What verifies — and it is genuinely good

- The entry zone **4434–4439 brackets that bar's open (4435.69) and its low
  (4435.44) almost exactly.** The zone was located to within $0.44 of the low.
- The stop at 4429 sits just under that structure and was **not** touched in the
  entry bar (low 4435.44).
- Price then ran to **4464.23** inside the same window.

| fill | risk to 4429 | max favourable | R |
|---|---|---|---|
| 4434.0 | $5.00 | +$30.23 (302 pips) | **6.0R** |
| 4436.5 | $7.50 | +$27.73 (277 pips) | **3.7R** |
| 4439.0 | $10.00 | +$25.23 (252 pips) | **2.5R** |

This is the first hard evidence of real skill in the project: a precisely
located zone, a structurally tight stop, and a 2.5–6R favourable move.

## What does not verify

- **440 pips is not supported for this long.** Aug 31's high was 4464.23;
  440 pips from the entry needs ~4478–4483, which never printed that day.
  Maximum available was **302 pips** at the best possible fill.
- **The 4429 stop was breached later the same day**, in the 13:00–17:00 bar
  (low 4415.75). Held to the stated stop, this trade was a loss.

The likely reconciliation is in the note itself: *"catch the low, ride the move
all the way up to the high, and then catch the reversal back down."* A short from
4464 to 4415.75 is another ~480 pips, so 440+ is very plausible as the **day's
total across both trades**, not this long alone.

## The finding that actually matters for the bot

The stop was eventually hit, so **the profit came from a discretionary exit at or
near the extreme, not from holding to a target.** Encoding the entry alone would
have produced a losing trade on this exact setup.

That relocates the problem. The entry logic is real, precise and probably
encodable. The exit is doing decisive work and is completely unspecified in every
note so far — no note in this project has ever stated where profit was taken.

## What is now needed

For each trade, the **exit price and time**, alongside entry and stop. Entry
location without exit rule is not a strategy — this trade proves it, because the
same entry is a 3.7R winner or a 1R loser depending entirely on the exit.
