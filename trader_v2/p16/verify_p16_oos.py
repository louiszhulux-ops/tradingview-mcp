#!/usr/bin/env python3
"""
Phase 16 derivation audit. Proves the OOS artifact differs from the Phase 15
executed provenance baseline ONLY by the authorised data-selection extension.
Read-only. Exits non-zero if any check fails.
"""
import hashlib, difflib, re, sys

SRC="trader_v2/p15/executed/V53_EXECUTED_BUILD.pine"
DST="trader_v2/p16/executed/V53_P16_OOS_BUILD.pine"

# Pinned absolute hashes. The relative diff checks below prove only that DST
# differs from SRC by the authorised change; without these two assertions a
# consistent edit to BOTH files would still pass. Section 8 of the protocol
# invalidates the accumulation period on any change to the derived artifact,
# so that condition is asserted here rather than left to a manual step.
SRC_SHA_EXPECTED="2dafbafd5f6731e93c6fc4a2d55048bb32d5c0d75581ed7fffd877a0cf58efe6"
DST_SHA_EXPECTED="5c21acfab1b0c832aaa562a0afc84c94e595da2318f2366dd153c1d08172b333"

sha=lambda p: hashlib.sha256(open(p,'rb').read()).hexdigest()
a=open(SRC).read().splitlines(); b=open(DST).read().splitlines()
ok=True
def chk(cond,label):
    global ok
    ok &= bool(cond); print(f"  [{'PASS' if cond else 'FAIL'}] {label}")

print("PHASE 16 DERIVATION AUDIT\n")
src_sha=sha(SRC); dst_sha=sha(DST)
print(f"  source  {SRC}\n          sha256 {src_sha}")
print(f"  derived {DST}\n          sha256 {dst_sha}\n")

print("0. PINNED SHA-256 ASSERTIONS (hard fail)")
chk(src_sha==SRC_SHA_EXPECTED,
    f"source   sha256 == {SRC_SHA_EXPECTED}" +
    ("" if src_sha==SRC_SHA_EXPECTED else f"  <-- GOT {src_sha}"))
chk(dst_sha==DST_SHA_EXPECTED,
    f"derived  sha256 == {DST_SHA_EXPECTED}" +
    ("" if dst_sha==DST_SHA_EXPECTED else f"  <-- GOT {dst_sha}"))
if not ok:
    print("\n" + "="*70)
    print("DERIVATION AUDIT: FAIL - pinned hash mismatch. HARD STOP.")
    print("Per PHASE16_PROTOCOL.md section 8, a change to the derived artifact")
    print("INVALIDATES the accumulation period. Do not proceed, do not repair")
    print("silently, and do not re-derive without recording why.")
    print("="*70)
    sys.exit(1)

print("\n1. FULL UNIFIED DIFF")
d=[x for x in difflib.unified_diff(a,b,"executed_baseline","p16_oos_build",lineterm="",n=0)]
for x in d: print("   "+x)
changed=[x for x in d if x.startswith(('+','-')) and not x.startswith(('+++','---'))]
print()
chk(len(changed)==4, f"exactly 2 lines replaced (2 removed + 2 added); saw {len(changed)}")
chk(len(a)==len(b)==602, "line count unchanged at 602")

print("\n2. THE TWO CHANGED LINES ARE BOTH FOLD-SELECTION")
for x in changed:
    body=x[1:]
    isfold = ('foldSel' in body and 'input.int' in body) or body.strip().startswith('inFold =')
    chk(isfold, f"{x[0]} line is fold-selection: {body.strip()[:74]}...")

print("\n3. FOLD CONSTANTS PRESERVED EXACTLY")
for c,v in [("FB","1784160000000"),("FC","1786233600000"),("FE","1788134400000")]:
    la=[l for l in a if l.startswith(f"{c} = ")]; lb=[l for l in b if l.startswith(f"{c} = ")]
    chk(la==lb==[f"{c} = {v}"], f"{c} = {v} unchanged")

print("\n4. EXISTING FOLD OPTIONS 0-4 SEMANTICALLY UNCHANGED")
nb=[l for l in b if l.startswith("inFold = ")][0]
for frag in ["foldSel == 0 ? (time < FB)","foldSel == 1 ? (time >= FB and time < FC)",
             "foldSel == 2 ? (time >= FC and time < FE)","foldSel == 3 ? (time < FC)",
             "foldSel == 4 ? (time < FE)"]:
    chk(frag in nb, f"option preserved: {frag}")
chk(nb.rstrip().endswith(": (time >= FE)"), "new trailing branch is exactly (time >= FE)")

print("\n5. ALL 15 FROZEN INPUTS: ORDER AND VALUES")
ia=[l for l in a if re.match(r'^\w+\s*=\s*input\.', l)]
ib=[l for l in b if re.match(r'^\w+\s*=\s*input\.', l)]
chk(len(ia)==len(ib)==15, f"15 inputs in both (a={len(ia)}, b={len(ib)}) -> in_0..in_14 mapping preserved")
for i,(x,y) in enumerate(zip(ia,ib)):
    if x==y: continue
    chk(i==1, f"only input index 1 (in_1, foldSel) differs; differing index is {i}")
va=re.search(r'input\.int\((\d+),',ia[1]).group(1); vb=re.search(r'input\.int\((\d+),',ib[1]).group(1)
chk(va==vb=="3", "foldSel default still 3")
for i,(x,y) in enumerate(zip(ia,ib)):
    if i!=1: chk(x==y, f"in_{i} byte-identical: {x.split('=')[0].strip()}")

print("\n6. STRATEGY SECTIONS 1-6 BYTE-IDENTICAL BELOW THE FOLD GATE")
cut=lambda s: s[[i for i,l in enumerate(s) if l.startswith("inFold = ")][0]+1:
                 [i for i,l in enumerate(s) if l.startswith("g(i) => str.tostring")][0]]
chk(cut(a)==cut(b), "every line between the fold gate and section 7 is identical")

print("\n7. SECTION 7 OUTPUT LAYER BYTE-IDENTICAL")
tail=lambda s: s[[i for i,l in enumerate(s) if l.startswith("g(i) => str.tostring")][0]:]
chk(tail(a)==tail(b), "output layer identical")

print("\n8. NAMED STRATEGY CONSTRUCTS UNCHANGED (count-for-count)")
for label,pat in [
    ("sweep engine (V49 hitPD/hitAS/hitSW)", r'hit(PD|AS|SW) :='),
    ("pivot detector non-strict-left/strict-right", r'array\.get\(bH, j\) >= hc'),
    ("CHOCH break-on-close", r'brk = isLong \? c > oV : c < oV'),
    ("CHOCH retest, zero tolerance", r'hitR = isLong \? l <= L : h >= L'),
    ("BOS reference w/ CHOCH-pivot exclusion", r'else if not na\(qV\) and qI != array\.get\(cPvI, i\)'),
    ("displacement + close-location clause", r'disp = rng > dispMin \* atr'),
    ("FVG: single-bar association at d+1", r'if ltfN == array\.get\(dBar, i\) \+ 1'),
    ("stop = sweep extreme +/- bufATR*ATR", r'isLong \? low - bufATR \* atr : high \+ bufATR \* atr'),
    ("R-band test", r'if ratio >= minRatr and ratio <= maxRatr'),
    ("target / timeout / adverse-first", r'if adv >= 1\.0'),
    ("cost drag", r'cR = costUSD / \(r \* ptv\)'),
    ("concurrency SP=24", r'^SP = 24$'),
    ("dispWait deadline", r'if bar_index - array\.get\(swB, i\) > dispWait'),
    ("LTF architecture request.security_lower_tf", r'request\.security_lower_tf'),
]:
    ca=len([l for l in a if re.search(pat,l)]); cb=len([l for l in b if re.search(pat,l)])
    chk(ca==cb and ca>0, f"{label}: {ca} occurrence(s), unchanged")

print("\n9. PROHIBITED CONSTRUCTS ABSENT")
chk(not any(re.search(r'request\.security\(',l) for l in b), "no request.security( )")
chk(not any('lookahead' in l for l in b), "no lookahead reference")
chk(len([l for l in b if 'request.security_lower_tf' in l])==5, "exactly 5 LTF fields (O,H,L,C,T) - no ATR/extra field")

print(f"\n{'='*70}\nDERIVATION AUDIT: {'PASS - data-selection change only' if ok else 'FAIL'}\n{'='*70}")
sys.exit(0 if ok else 1)
