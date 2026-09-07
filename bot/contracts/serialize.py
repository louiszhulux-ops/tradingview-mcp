"""Deterministic serialisation for every contract type.

Rules, all enforced by tests:

* prices and R multiples are ``Decimal`` in memory and **exact decimal strings**
  on the wire — never floats, whose repr is not a stable interchange format;
* mappings are emitted with sorted keys;
* sequences keep their declared order, which is meaningful everywhere it appears;
* nothing reads the wall clock, generates a random id, or embeds a filesystem
  path.

The same input therefore always produces byte-identical output, which is what
lets B3 compare a replay against a golden fixture by equality rather than by
tolerance.
"""

from __future__ import annotations

import json
from decimal import Decimal
from enum import Enum
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Serialisable(Protocol):
    """Anything the contracts can put on the wire."""

    def to_dict(self) -> dict[str, Any]:
        ...


def encode(value: Any) -> Any:
    """Convert a contract value into JSON-native form, deterministically."""
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, float):
        raise TypeError(
            f"float is not serialisable in a contract ({value!r}); prices and R "
            f"multiples must be Decimal so comparison is exact"
        )
    if isinstance(value, dict):
        return {str(k): encode(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (list, tuple)):
        return [encode(v) for v in value]
    if hasattr(value, "to_dict"):
        return encode(value.to_dict())
    raise TypeError(f"not serialisable in a contract: {type(value).__name__}")


def dumps(value: Any) -> str:
    """Canonical JSON text: sorted keys, two-space indent, trailing newline."""
    return json.dumps(encode(value), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def canonical(value: Any) -> str:
    """Compact canonical form, for hashing and equality keys."""
    return json.dumps(encode(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
