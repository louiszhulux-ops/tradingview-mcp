"""Trading-system implementation tree.

Everything under ``bot/`` is new implementation code. Everything outside it —
``trader_v2/``, ``trader/``, ``strategies/``, ``src/`` — is research and is
treated as read-only by this package.

Phase 16 (out-of-sample validation) is accumulating forward-held-out data from
2026-08-31 00:00 UTC to 2027-04-02 00:00 UTC. Development code in this tree
must never read, test against, or otherwise consume data at or after that
boundary. See :mod:`bot.guards`.
"""
