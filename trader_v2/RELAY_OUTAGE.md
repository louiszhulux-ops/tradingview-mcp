# Relay outage — the room curve was not measured

## Status: BLOCKED. No curve exists. Nothing was estimated.

The room-to-destination cumulative expectancy curve is the next required
measurement. It has not been produced because the TradingView MCP relay was
unavailable for the whole attempt window.

## Retry log

All retries were `tv_health_check` or `chart_get_state` against the relay, with
exponential backoff. Times UTC, 2026-09-05.

| time | wait before | result |
|---|---|---|
| 18:05:54 | — | 502 origin_bad_gateway (during `pine_set_source` of V48) |
| 18:05:58 | 4s | 502 |
| 18:06:40 | 42s | 502 |
| 18:06:50 | 10s | 502 |
| 18:07:02 | 12s | 502 |
| 18:07:31 | 29s | 502 |
| 18:07:47 | 16s | 502 |
| 18:09:06 | 90s | 502 |
| 18:12:39 | 200s | 502 |
| 18:21:37 | — | 502 |
| 18:22:47 | 60s | 502 |
| 18:24:54 | 120s | 502 |
| 18:29:02 | 240s | 502 |
| 18:37:11 | 480s | 502 |
| 18:47:19 | 600s | 502 |
| 18:49:50 | 150s | 502 |
| 18:53:0x | 180s | **MCP server "f" is not connected** |
| 18:55:0x | 120s | **404 CLIENT_HTTP_NOT_IMPLEMENTED — server failed to connect** |

**The failure mode degraded rather than recovered.** It began as HTTP 502
(`origin_bad_gateway` — the relay's origin overloaded or misconfigured), moved
to the MCP client reporting the server as disconnected, and ended as a hard 404
on the session's MCP route:

```
f (404): SdkHttpError dialing https://api.anthropic.com/v2/ccr-sessions/.../mcp
         (CLIENT_HTTP_NOT_IMPLEMENTED)
```

That last state is a session-level connection failure, not a transient gateway
blip, and more waiting does not clear it. It needs the connector re-established
or the session restarted — on the user's side, not mine.

Total elapsed across retries: ~49 minutes, 18 attempts.

## What was NOT done, deliberately

- `V48_candidate_ledger.pine` is **unmodified** since it was committed in
  `3b2b581`. md5 `9bd48f069234a5787d0eebc95dbc4151`. The experiment was not
  changed, tuned or simplified while it could not be run.
- The 10R room threshold is **unchanged**.
- No filters added, no parameters touched.
- **The room curve was not inferred from earlier results.** `room_curve.py`
  holds `DATA = {}` and prints `NO DATA` rather than producing a plausible-looking
  curve. This matters: the earlier V44/V45/V47 runs contain room-adjacent numbers
  that could be arranged into something curve-shaped, and doing that would be
  fabrication.

## What runs the moment the relay returns

1. Inject `V48_candidate_ledger.pine`, compile, add to chart.
2. Fold A+B, all ten instrument × direction cells: MGC, SIL, MNQ, MCL, 6E,
   long and short.
3. Read the nine room buckets per cell plus the ledger counters.
4. Feed `room_curve.py`, which emits per-bucket and cumulative-from-every-floor
   rows: n, trades/day, mean R, median R, win rate, derived PF, 90% CI, t,
   R/day, and the incremental frequency cost against the expectancy change at
   each step up.
5. **Stop and report the complete curve before any strategy change.**

## Two limits of the measurement, stated in advance

- **Median R is not informative here.** Every trade resolves to +5R or −1R minus
  cost, so the median is −1R at any win rate below 50% — which is every bucket
  measured so far. That is a property of the fixed-target design, not a finding
  about room.
- **True per-bucket drawdown is not available.** V48 records no equity ordering.
  `room_curve.py` reports the expected longest losing run as a labelled proxy and
  does not call it drawdown.
