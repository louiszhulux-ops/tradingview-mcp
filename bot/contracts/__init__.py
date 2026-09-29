"""Typed contracts between the V53 strategy engine, its data, and its consumers.

**These are contracts, not an implementation.** Nothing here detects a sweep,
selects a CHOCH, qualifies a displacement, or decides an outcome. B2 implements
the behaviour; B3 verifies it against the A2 golden fixtures.

Deliberately absent, and deliberately so: no rule is enforced by a schema. The
contracts do not check that a target sits 5R from entry, that an R/ATR ratio
falls inside the frozen band, or that a stop lies on a particular side of entry.
Those are V53's rules; encoding them here would make the schema a second, silent
copy of the strategy — and the A2 fixtures contain two fills whose stop sits on
the near side of entry, which such a check would wrongly reject.
"""
