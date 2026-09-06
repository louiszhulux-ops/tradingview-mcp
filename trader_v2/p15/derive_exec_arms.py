#!/usr/bin/env python3
"""Re-derive Phase 15 arms C1-G1 from the ACTUAL EXECUTED baseline artifact.

Every edit is an exact-string replacement that must match exactly once, or the
script aborts. Nothing is inferred, nothing is fuzzy-matched. The executed
build's diagnostic layer (K33/K34/K35 are absent from it by definition) and its
section 7 output layer are carried through untouched.
"""
import hashlib, sys, os

BASE = "executed/V53_EXECUTED_BUILD.pine"
src0 = open(BASE).read()

def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()

def rep(s, old, new, tag):
    n = s.count(old)
    if n != 1:
        sys.exit(f"ABORT [{tag}]: anchor found {n} times, expected exactly 1")
    return s.replace(old, new)

arms = {}

# ---------------- C1 : CHOCH retest proximity = 0.10 x LTF ATR ----------------
s = src0
s = rep(s,
  'aT = request.security_lower_tf(syminfo.tickerid, ltfStr, time)\n',
  'aT = request.security_lower_tf(syminfo.tickerid, ltfStr, time)\n'
  'aA = request.security_lower_tf(syminfo.tickerid, ltfStr, ta.atr(14))   // P15-C1 ONLY\n',
  "C1 site 1 (LTF ATR field)")
s = rep(s,
  '                        L = array.get(cLvl, i)\n'
  '                        hitR = isLong ? l <= L : h >= L\n',
  '                        L = array.get(cLvl, i)\n'
  '                        // P15-C1: proximity band of 0.10 x LTF ATR replaces zero tolerance\n'
  '                        tolA = array.size(aA) > k ? array.get(aA, k) : na\n'
  '                        tol = na(tolA) ? 0.0 : 0.10 * tolA\n'
  '                        hitR = isLong ? l <= L + tol : h >= L - tol\n',
  "C1 site 2 (retest test)")
arms["V53_EXEC_P15_C1_retest_tol.pine"] = s

# ---------------- D1 : BOS reference may be the CHOCH pivot ----------------
s = src0
s = rep(s,
  '                        if not na(oV) and oI != array.get(cPvI, i)\n'
  '                            bV := oV\n'
  '                            bI := oI\n'
  '                        else if not na(qV) and qI != array.get(cPvI, i)\n'
  '                            bV := qV\n'
  '                            bI := qI\n',
  '                        // P15-D1: the CHOCH pivot is NO LONGER excluded from BOS eligibility\n'
  '                        if not na(oV)\n'
  '                            bV := oV\n'
  '                            bI := oI\n',
  "D1 (BOS reference eligibility)")
arms["V53_EXEC_P15_D1_bos_reference.pine"] = s

# ---------------- E1 : first qualifying FVG at/after the displacement candle ----------------
s = src0
s = rep(s,
  '                    if ltfN == array.get(dBar, i) + 1 and array.size(bH) == RB\n'
  '                        if array.get(bIX, RB - 2) != array.get(dBar, i)\n',
  '                    // P15-E1: scan forward for the FIRST qualifying FVG whose middle candle is\n'
  '                    // at or after the displacement candle, bounded by the existing dispWait deadline\n'
  '                    if ltfN >= array.get(dBar, i) + 1 and array.size(bH) == RB\n'
  '                        if ltfN == array.get(dBar, i) + 1 and array.get(bIX, RB - 2) != array.get(dBar, i)\n',
  "E1 site 1 (scan window)")
s = rep(s,
  '                        if na(E)\n'
  '                            array.set(st, i, 0)\n'
  '                            array.set(K, 10, array.get(K, 10) + 1)\n',
  '                        if na(E)\n'
  '                            if bar_index - array.get(swB, i) > dispWait\n'
  '                                array.set(st, i, 0)\n'
  '                                array.set(K, 10, array.get(K, 10) + 1)\n',
  "E1 site 2 (deferred invalidation)")
arms["V53_EXEC_P15_E1_fvg_association.pine"] = s

# ---------------- F1 : raw sweep-extreme stop, no ATR buffer ----------------
s = src0
s = rep(s,
  '        array.set(stp, fr, isLong ? low - bufATR * atr : high + bufATR * atr)\n',
  '        array.set(stp, fr, isLong ? low : high)   // P15-F1: raw sweep extreme, no 0.20xATR buffer\n',
  "F1 (stop construction)")
arms["V53_EXEC_P15_F1_stop_raw_extreme.pine"] = s

# ---------------- G1 : latch the FIRST eligible CHOCH pivot, never roll ----------------
s = src0
s = rep(s,
  'var int[]   dBar = array.new_int(SP, -1)\n',
  'var int[]   dBar = array.new_int(SP, -1)\n'
  'var int[]   gPvI = array.new_int(SP, -1)   // P15-G1: latched CHOCH pivot index\n',
  "G1 site 1 (latch array)")
s = rep(s,
  '                        p = array.get(pRef, i)\n'
  '                        if not na(p) and p != oV\n'
  '                            array.set(K, 4, array.get(K, 4) + 1)\n'
  '                        array.set(pRef, i, oV)\n'
  '                        brk = isLong ? c > oV : c < oV\n'
  '                        wick = isLong ? (h > oV and c <= oV) : (l < oV and c >= oV)\n',
  '                        // P15-G1: latch the FIRST eligible opposing pivot; never roll forward\n'
  '                        if na(array.get(pRef, i))\n'
  '                            array.set(pRef, i, oV)\n'
  '                            array.set(gPvI, i, oI)\n'
  '                        rV = array.get(pRef, i)\n'
  '                        rI = array.get(gPvI, i)\n'
  '                        if not na(oV) and oV != rV\n'
  '                            array.set(K, 4, array.get(K, 4) + 1)\n'
  '                        brk = isLong ? c > rV : c < rV\n'
  '                        wick = isLong ? (h > rV and c <= rV) : (l < rV and c >= rV)\n',
  "G1 site 2 (latch instead of roll)")
s = rep(s,
  '                            if oI + lSw == ltfN\n',
  '                            if rI + lSw == ltfN\n',
  "G1 site 3 (A32 uses the latched pivot)")
s = rep(s,
  '                            array.set(cLvl, i, oV)\n'
  '                            array.set(cPvI, i, oI)\n',
  '                            array.set(cLvl, i, rV)\n'
  '                            array.set(cPvI, i, rI)\n',
  "G1 site 4 (CHOCH records the latched pivot)")
s = rep(s,
  '        array.set(dBar, fr, -1)\n',
  '        array.set(dBar, fr, -1)\n'
  '        array.set(gPvI, fr, -1)\n',
  "G1 site 5 (reset on arm)")
arms["V53_EXEC_P15_G1_first_choch_pivot.pine"] = s

os.makedirs("exec_arms", exist_ok=True)
print(f"executed baseline : {BASE}")
print(f"                    sha256 {sha(src0)}")
print()
for name, text in arms.items():
    p = os.path.join("exec_arms", name)
    open(p, "w").write(text)
    print(f"{name:44s} sha256 {sha(text)}")
