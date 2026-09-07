#!/usr/bin/env python3
"""
Phase 16 OOS artifact derivation. Data-selection extension ONLY.

Derives trader_v2/p16/executed/V53_P16_OOS_BUILD.pine from the Phase 15 executed
provenance baseline by adding one foldSel option selecting time >= FE.

Every edit is an exact-string replacement that must match exactly once, or this
script aborts. Nothing is inferred, nothing is fuzzy-matched. No strategy
condition, parameter, execution rule or outcome rule is touched.
"""
import hashlib, sys, os

SRC = "trader_v2/p15/executed/V53_EXECUTED_BUILD.pine"
DST = "trader_v2/p16/executed/V53_P16_OOS_BUILD.pine"
SRC_SHA_EXPECTED = "2dafbafd5f6731e93c6fc4a2d55048bb32d5c0d75581ed7fffd877a0cf58efe6"

sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
src = open(SRC).read()

if sha(src) != SRC_SHA_EXPECTED:
    sys.exit(f"ABORT: source SHA {sha(src)} != expected {SRC_SHA_EXPECTED}")

def rep(s, old, new, tag):
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT [{tag}]: anchor found {n} times, expected exactly 1")
    return s.replace(old, new)

out = src

# ---- EDIT 1 of 2: widen the foldSel input's range and label ----------------
# The input keeps its position (2nd input -> in_1) and its default (3).
# Values 0-4 keep their existing meaning exactly.
out = rep(out,
  'foldSel  = input.int(3,  "fold 0=A 1=B 2=C 3=A+B 4=all", minval=0, maxval=4, group="Test")',
  'foldSel  = input.int(3,  "fold 0=A 1=B 2=C 3=A+B 4=all 5=OOS", minval=0, maxval=5, group="Test")',
  "EDIT 1: foldSel input range")

# ---- EDIT 2 of 2: add the forward/OOS branch to the fold gate --------------
# The former trailing else (time < FE) becomes an explicit foldSel == 4 branch,
# so options 0,1,2,3,4 are semantically UNCHANGED. The new trailing else is the
# forward window, time >= FE. FB, FC and FE are untouched.
out = rep(out,
  'inFold = foldSel == 0 ? (time < FB) : foldSel == 1 ? (time >= FB and time < FC) : '
  'foldSel == 2 ? (time >= FC and time < FE) : foldSel == 3 ? (time < FC) : (time < FE)',
  'inFold = foldSel == 0 ? (time < FB) : foldSel == 1 ? (time >= FB and time < FC) : '
  'foldSel == 2 ? (time >= FC and time < FE) : foldSel == 3 ? (time < FC) : '
  'foldSel == 4 ? (time < FE) : (time >= FE)',
  "EDIT 2: fold gate forward branch")

os.makedirs(os.path.dirname(DST), exist_ok=True)
open(DST, "w").write(out)
print(f"source  {SRC}\n        sha256 {sha(src)}\n")
print(f"derived {DST}\n        sha256 {sha(out)}\n")
print(f"lines   {len(src.splitlines())} -> {len(out.splitlines())}")
