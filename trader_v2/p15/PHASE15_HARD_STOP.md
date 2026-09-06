# Phase 15 — HARD STOP after Experiment B

**Raised at:** start of Experiment C1 (CHOCH retest tolerance), before any C1 run.
**Nothing has been repaired.** No file was edited to resolve this, no source was injected into
the chart, and no C1–G1 run was executed. The chart still carries the same build that produced
every Phase 15 number so far.

---

## 1. The discrepancy

The Pine build actually executing on the chart is **not** the file the Phase 15 manifest names
as the baseline.

| | file | sha256 |
|---|---|---|
| manifest baseline | `trader_v2/V53_ltf_sequence.pine` | `7490766b6e3de062989a8e7f10939869cc6b679d253ce584f223064aa5797ef5` |
| build actually executing | *(was not in the repository)* | now preserved as `trader_v2/p15/executed/V53_EXECUTED_BUILD.pine`, `2dafbafd5f6731e93c6fc4a2d55048bb32d5c0d75581ed7fffd877a0cf58efe6` |

### How it was found

`data_get_pine_tables` returns an audit table headed `FUNNEL L ALL 1m` with 20 rows, including a
single collapsed row `ASSERTS 21-27,32 | 0/0/0/0/0/0/0/0`. `V53_ltf_sequence.pine` emits a
37-row table headed `V53 LONG ALL 1m` with eight separate assertion rows plus rows
`LTF pivots confirmed`, `4 reference rolls`, `5 wick thru, no close`, `7 near-miss no retest`,
`19 same-bar fill diag` and `D33/D34/D35`. The two cannot be the same program.

The executed source was then read back with `pine_get_source` (602 lines, 27,240 chars) and
written to disk. The captured file is 602 lines / 27,241 bytes — byte-exact against the reported
length, modulo the trailing newline.

### How large the difference is

Strategy sections 1–6 of both files, with comments and blank lines stripped, differ in
**exactly three places**, all inside section 6 (detector verification):

```
<     bool tie = false                      (+ the loop that sets it)
<         if na(pv3H) ... array.set(K, 34/33, ...)   ; if tie -> array.set(K, 35, ...)
<         if na(pv3L) ... array.set(K, 34/33, ...)   ; if tie -> array.set(K, 35, ...)
```

`K33`, `K34`, `K35` and `tie` are **write-only diagnostics**. They are never read by any
decision in the program; the disk build only displays them as table rows D33/D34/D35. Every
strategy-bearing line — the 5m sweep engine, the LTF pivot detector, CHOCH, the zero-tolerance
CHOCH retest, BOS + displacement with CHOCH-pivot exclusion, FVG selection, the fill/R-band
test, the outcome model, the arm block, `SP`, `RB`, and the fold boundaries `FB/FC/FE` — is
identical, as are all fifteen inputs in the same order (so the `in_0 … in_14` mapping is
preserved).

Beyond that, the two files differ only in comments and in section 7 (the output tables).

---

## 2. What this does and does not invalidate

**Does not invalidate the results collected so far.** The executed build was constant across the
frozen-baseline control arm, all three Experiment A arms and all three Experiment B arms — only
indicator *inputs* were changed between cells, never the source. Every within-study comparison
in `EXPERIMENT_A_swLen.md` and `EXPERIMENT_B_displacement.md` is therefore between runs of one
and the same program, and the pooled-design verification against the Phase 13F/14 results still
holds. Those results stand as recorded.

**Does invalidate the manifest's identification of the baseline artifact.**
`phase15_manifest.json` records `sha256 7490766b…` for the baseline and for the A and B arm
files ("byte-identical to baseline"). That hash does not identify the program that produced the
data. The claim "the arm file is byte-identical to V53" was true of the file on disk and
irrelevant to what ran.

**Blocks experiments C1 through G1 as currently packaged.** Each of those five arm files is a
hand-edit of `V53_ltf_sequence.pine`. Injecting one would apply, in a single step:

1. the intended single rule change (e.g. the 0.10 × LTF-ATR retest band for C1), **and**
2. reinstatement of the K33/K34/K35 diagnostic block, **and**
3. replacement of the whole section-7 output layer with the 37-row/verbose-ledger format.

(2) is behaviourally inert and (3) is measurement only, but together they mean the C1–G1 arms
would not be running the same artifact as the baseline, A and B arms. That fails the Phase 15
requirement that each experiment change exactly one predefined hypothesis component, and it
fails the manifest check. The reporting change would also silently break the run-capture
workflow that every recorded cell so far depends on.

---

## 3. Hard-stop conditions met

From the Phase 15 brief:

- *"STOP if … an experimental arm differs from its manifest."* — The baseline and the A/B arm
  entries name a file that is not the executed build.
- *"STOP if … an experiment cannot be implemented deterministically."* — C1–G1 cannot be applied
  as one controlled change to the artifact that generated the baseline.

Actions taken, per the brief:

1. **Preserve the files** — the executed build is now committed at
   `trader_v2/p15/executed/V53_EXECUTED_BUILD.pine`. `V53_ltf_sequence.pine` is untouched
   (hash unchanged, `7490766b…`). All seven arm files are untouched. All run data is untouched.
2. **Document the exact discrepancy** — this file.
3. **Do NOT repair it silently** — no file has been reconciled, no manifest entry rewritten, no
   source injected into the chart.
4. **Do NOT continue to subsequent experiments** — C1, D1, E1, F1 and G1 have not been run.

---

## 4. State at the stop

- Chart: `MNQ1!`, 5m. Study `V53 LTF SEQUENCE` (`USER;b798deb2c9084500a1c38b14775961da`,
  version 137.0) — **unchanged**; no compile or save was performed.
- Inputs restored to the frozen baseline: `in_0 = 1` (long), `in_1 = 4` (fold ALL),
  `in_2 = 1` (1m), `in_6 = 1.50` (dispMin), `in_14 = 3` (lSw). All other frozen inputs at their
  frozen values.
- The Pine editor panel was opened in order to read the source. Nothing was typed into it.
- Completed and committed: frozen-baseline control arm (8 cells), Experiment A (3 arms,
  24 cells), Experiment B (3 arms, 24 cells). 56 of 88 planned runs.
- Not run: C1, D1, E1, F1, G1 (40 runs).

---

## 5. Decisions required before Phase 15 can resume

These are not mine to make. Each changes what the remaining study measures.

1. **Which artifact is the baseline of record** — the executed build
   (`2dafbafd…`, which generated all existing data), or `V53_ltf_sequence.pine`
   (`7490766b…`, which the manifest names and which Phase 13E audited)?
2. **Whether the five remaining arm files should be re-derived** against whichever build is
   chosen, so that each once again differs from the baseline by exactly one rule and nothing
   else. If so, they must be re-derived and re-hashed, not patched in place.
3. **Whether Experiments A and B need re-running** under a reconciled artifact. On the evidence
   above they do not — the two builds are behaviourally identical and the arms were run against a
   single constant build — but that is a judgement about acceptable provenance, not a mechanical
   fact, and it belongs to the study owner.
4. **How `phase15_manifest.json` should record the correction**, given that its baseline hash is
   currently wrong about what ran.

Until these are settled, Phase 15 remains stopped after Experiment B.
