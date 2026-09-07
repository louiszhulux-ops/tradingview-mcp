# Exit lab — inverting the experiment, and what it settled

## Why this experiment

Every prior test in this project varied the **entry** and held the exit fixed.
Two pieces of evidence said that was backwards:

- The one verified trade: same entry, same stop — a 3.7R winner or a 1R loser
  depending *only* on where it was closed.
- The trade-level audit: 50.7% of losing trades reached +0.5R and 26.7% reached
  +1R before dying. I found that and never acted on it.

So I held one entry constant and varied only the exit, encoding the verified
trade's actual shape: fade a session extreme, stop just beyond it, target the
opposite extreme.

## The chain of results

**v1 — enter at the close of the rejection bar, target the opposite extreme**
174 trades, **71.8% win rate**, PF 0.685, −$40,598.
The hit rate is real: price returns to the opposite session extreme roughly 7
times in 10. But avg win $708 vs avg loss **$2,634** — the stop was
uncontrolled, because a bar that sets an extreme *and* closes weakly is by
definition a large bar.

**v2 — same, but cap the stop at 0.5×ATR**
1 trade. The two conditions are nearly incompatible. Dead end, and informative.

**v3 — work a LIMIT back near the extreme instead**
This is what the verified trade actually did (sold 4460 with the high at
4464.23, stop 4468 — risk $8, not $50) and what the notes describe: *"waited
patiently for price to retrace back… once this area was tapped, that was my
entry."* Risk becomes (entryOff + buffer) × ATR by construction.
234 trades, 15.4% win rate, PF 0.670, −$9,424. Largest loss fell from $13,197 to
$592 — the stop control worked. The win rate collapsed instead.

## The result that settles it

Same entry, same target, only the stop width changing:

| stop | n | win% | avg win | avg loss | W/L | breakeven win% | gap | PF |
|---|---|---|---|---|---|---|---|---|
| tight 0.35×ATR | 234 | 15.4% | $532 | $144 | 3.69 | 21.3% | **−6.0** | 0.670 |
| medium 1.10×ATR | 66 | 33.3% | $736 | $577 | 1.28 | 43.9% | **−10.6** | 0.638 |
| wide, uncontrolled | 174 | 71.8% | $708 | $2,634 | 0.27 | 78.8% | **−7.0** | 0.685 |

**The win rate slides from 15% to 72% and the profit factor never leaves ~0.65.**
Every configuration sits 6–11 points *below its own* breakeven win rate.

That is the signature of no edge rather than of mis-tuning. If an edge existed
and I had merely mis-set the stop, at least one point on that curve would cross
breakeven. None does. You can trade anywhere along the win-rate/reward tradeoff
and the line is never reached.

It also disposes of the "just get a higher win rate" idea permanently: a 71.8%
win rate is available here for the asking, and it loses $40,598.

## Where the whole search now stands

| Approach | Result |
|---|---|
| 9 textbook entries, fixed exits | 8 at/below breakeven; the 1 survivor failed out-of-sample (54.0% → 50.5%) |
| The discretionary process, encoded and ablated | no edge at 1R, 2R or 3R; the Asia and second-touch filters never even bound |
| Exit-first: session-extreme fade, 3 stop widths, 5 exit modes | PF ~0.65 across the entire win-rate range |

Three independent lines of attack, all negative, and the last one shows *why*:
the tradeoff curve itself sits below breakeven.

## My honest conclusion

I have not found an edge in 15-minute OHLC data on gold, and this last test
suggests I am not going to by rearranging entries, exits or stops. The verified
trade is real — a 5.1R short with a stop that was never threatened — but the
information that made it work is not in the bars I can see.

What I would need to go further is genuinely different data (order flow,
footprint, event timing), or enough logged trades to reverse-engineer the
discretionary judgement. Neither is available to me now.

What I will not do is keep tuning until something looks good. I have a 54%
win-rate result in this repo that did exactly that and then failed validation;
producing another one would be worse than producing nothing.
