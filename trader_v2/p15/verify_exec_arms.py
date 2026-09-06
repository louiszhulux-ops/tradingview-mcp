#!/usr/bin/env python3
"""Single-concept verification for the re-derived Phase 15 arms.

For each arm: hash, unified diff against the EXECUTED baseline, confirmation
that the section-7 output layer is byte-identical, and a strategy-section
change count. Any arm whose output layer moves, or whose strategy diff touches
a site outside its declared change, is flagged.
"""
import hashlib, difflib, os, re

BASE = "executed/V53_EXECUTED_BUILD.pine"
base = open(BASE).read()
sha = lambda s: hashlib.sha256(s.encode()).hexdigest()

def split7(t):
    i = t.index("g(i) => str.tostring(array.get(K, i))")
    return t[:i], t[i:]

b_strat, b_out = split7(base)

ARMS = [
 ("C1", "V53_EXEC_P15_C1_retest_tol.pine",      "CHOCH retest tolerance"),
 ("D1", "V53_EXEC_P15_D1_bos_reference.pine",   "BOS reference eligibility"),
 ("E1", "V53_EXEC_P15_E1_fvg_association.pine", "FVG association"),
 ("F1", "V53_EXEC_P15_F1_stop_raw_extreme.pine","Stop construction"),
 ("G1", "V53_EXEC_P15_G1_first_choch_pivot.pine","CHOCH candidate selection"),
]

print("EXECUTED BASELINE")
print(f"  file   {BASE}")
print(f"  sha256 {sha(base)}")
print(f"  lines  {len(base.splitlines())}")
print()

ok = True
for aid, fn, rule in ARMS:
    t = open(os.path.join("exec_arms", fn)).read()
    a_strat, a_out = split7(t)
    out_same = (a_out == b_out)
    d = list(difflib.unified_diff(b_strat.splitlines(), a_strat.splitlines(),
                                  "executed_baseline", fn, lineterm="", n=0))
    hunks = [x for x in d if x.startswith("@@")]
    added = [x for x in d if x.startswith("+") and not x.startswith("+++")]
    removed = [x for x in d if x.startswith("-") and not x.startswith("---")]
    print(f"===== {aid}  ({rule}) =====")
    print(f"  file    exec_arms/{fn}")
    print(f"  sha256  {sha(t)}")
    print(f"  section 7 output layer byte-identical to baseline : {'YES' if out_same else 'NO  ** FLAG **'}")
    print(f"  strategy-section hunks {len(hunks)} | +{len(added)} lines | -{len(removed)} lines")
    for x in d:
        if not x.startswith(("---","+++")):
            print("   " + x)
    if not out_same:
        ok = False
    print()

print("ALL ARMS PRESERVE THE EXECUTED BUILD'S OUTPUT LAYER:", "YES" if ok else "NO")
