# Phase P-10A — "V4 Gold DEBUG" Recovery

## 1. Executive conclusion

## **AMBIGUOUS — NOTHING RESTORED, NOTHING LOST**

No restoration was performed, and none should be performed without a decision from the owner.

The investigation found that **the premise of P-10A is not quite right**, in a way that matters:

1. **"V4 Gold DEBUG" is not a preserved user script — it is the account's single saved-script
   slot**, and its `name` field has been frozen since version 1 while its *contents* have been
   replaced ~143 times by this project's own experiments.
2. **The version P-9 overwrote (142) was not V4 Gold DEBUG.** It was a
   `V53 LTF SEQUENCE LEDGER` build — specifically, and byte-identically, the committed repository
   file `trader_v2/p15/exec_arms/V53_EXEC_P15_G1_first_choch_pivot.pine`.
3. **TradingView retained the entire version history.** Versions 1 through 143 are all fetchable.
   Nothing was destroyed by P-9 — not V4 Gold DEBUG, not the V53 build.

Because two materially different "correct previous versions" exist — v1 (the script actually named
V4 Gold DEBUG) and v142 (what P-9 displaced) — §2 and §5 of the task require a stop rather than a
guess. **STOP — VERSION AMBIGUITY.**

---

## 2. Incident

| | |
|---|---|
| date | **2026-09-07 09:29:58 UTC** (`modified` = 1788773398) |
| phase | P-9, commit `e03385b` |
| cause | `pine_smart_compile` selected the editor's **Pine Save** button while the editor held the account's saved-script slot. The tool chooses its own button; the slot's contents were not checked before injection |
| slot | `USER;b798deb2c9084500a1c38b14775961da` |
| slot `name` | `V4 Gold DEBUG` |
| version written | **143.0** |
| version displaced | **142.0** |

---

## 3. Evidence

All read-only, via TradingView's own `pine-facade` REST API with session credentials. No script was
executed. No source was modified.

### 3.1 The slot

`pine_list_scripts` returns exactly **one** saved script:

```
id       USER;b798deb2c9084500a1c38b14775961da
name     V4 Gold DEBUG          <- fixed slot label, set at v1
title    P9 LTF EXTRACTION      <- tracks whatever script is currently saved
version  143.0
modified 1788773398  = 2026-09-07 09:29:58 UTC
```

`name` and `title` are separate fields. The **name is a stale label**; the **title** follows the
current contents. This is why the slot still reads "V4 Gold DEBUG" while holding entirely unrelated
scripts.

### 3.2 Version 143 is the P-9 probe — **VERIFIED** (§4)

```
scriptName  V4 Gold DEBUG
scriptTitle P9 LTF EXTRACTION
version     143.0
source      //@version=6
            // P-9 LTF EXTRACTION PROBE -- DATA EXTRACTION ONLY.
            // Contains no strategy logic: no ATR, no pivots, no sweep, no CHOCH, no BOS, ...
```

2,872 characters, `request.security_lower_tf`, timestamp/OHLC plots. Unambiguously the P-9 probe.
Its source is also committed as `docs/p9_extraction_probe.pine`.

### 3.3 Version 142 is **not** V4 Gold DEBUG — **VERIFICATION FAILED** (§5)

```
version 142.0
source  //@version=6
        // V53 LTF SEQUENCE LEDGER  --  frozen Phase 13D hypothesis + measurement layer.
```

28,210 raw characters (CRLF), 27,603 LF-normalised.

**It is byte-identical to a committed repository file.** Scanning all 41 `.pine` files in the
repository under LF normalisation:

```
byte-identical match to TradingView v142:
  trader_v2/p15/exec_arms/V53_EXEC_P15_G1_first_choch_pivot.pine
```

This is consistent with the P-6 observation that the research chart carries the Phase 15 G1 build.

**So v142 is a V53 Phase-15 arm, not V4 Gold DEBUG.** Per §5 this is `STOP — VERSION AMBIGUITY`,
not `RESTORE CANDIDATE VERIFIED`.

### 3.4 The slot's actual history

Sampled read-only across the range:

| version | identity (first source line) | size |
|---|---|---|
| **1** | `strategy("V4 Gold DEBUG", overlay=true, initial_capital=50000)` | 1,718 |
| 50 | (unnamed header block) | 22,609 |
| 100 | `// V35 FADE PROD -- the V33 finding, executed under LucidFlex rules.` | 8,046 |
| 120 | `// V47 PHASE-4 ABLATION -- spec: PHASE2_PROTOCOL.md sec 4.` | 11,503 |
| 130 | `indicator("LTF DATA PROBE", overlay=true)` | 2,462 |
| 133 | `indicator("LTF DATA PROBE", overlay=true)` | 2,182 |
| 135 | `// PIVOT RULE DIAGNOSTIC -- read-only.` | 3,659 |
| 138 | `// V53 LTF SEQUENCE LEDGER` | 28,168 |
| 140 | `// V53 LTF SEQUENCE LEDGER` | 28,157 |
| 141 | `// V53 LTF SEQUENCE LEDGER` | 27,862 |
| **142** | `// V53 LTF SEQUENCE LEDGER` | 28,210 |
| **143** | `// P-9 LTF EXTRACTION PROBE` | 2,872 |

**Only version 1 contains the script named V4 Gold DEBUG.** Everything after it is a different
experiment reusing the same slot.

### 3.5 Corroboration already in the repository

`trader_v2/PHASE13B_LTF_CONTINUATION_AUDIT.md:72-75`, written long before P-9:

> "`pine_list_scripts` returns a **single** saved script slot (`V4 Gold DEBUG`, version 133), which
> every experiment since has overwritten."

The slot-reuse pattern was therefore known and documented in this project before the incident. P-9
was the tenth such overwrite since that audit, not a novel event.

That audit also assumed the displaced content was "not recoverable". **That assumption is now shown
to be wrong** — the pine-facade `get/<id>/<version>` endpoint returns arbitrary historical versions,
including version 1.

---

## 4. Why nothing was restored

§2: *"If the version history shows another plausible candidate: STOP and report the ambiguity. Do
not guess."* §5: *"If not: STOP — VERSION AMBIGUITY."*

Two defensible readings of "restore V4 Gold DEBUG" exist, and they are not close:

| reading | target | consequence |
|---|---|---|
| restore the script **named** V4 Gold DEBUG | **v1** — a 1,718-char V4-era strategy predating essentially all current work | would replace the working slot with a years-stale script |
| undo **what P-9 displaced** | **v142** — the Phase 15 G1 V53 arm | would restore a V53 research build into the working slot |

Restoring either would itself create version 144 and displace the other. Since the correct
intention cannot be established from evidence, no restore was performed.

---

## 5. Impact

| | |
|---|---|
| repository files | **unaffected** — working tree clean throughout |
| frozen Phase C datasets | **unaffected** — hashes verified before and after |
| all eight frozen hashes | **unchanged** |
| `2d43Iesr` | **unaffected by P-10A** — never opened, attached to or read (see §7) |
| V53 canonical artifacts | **unaffected** — `V53_ltf_sequence.pine` `7490766b…`, `V53_EXECUTED_BUILD.pine` `2dafbafd…` both verified |
| Phase 16 | **unaffected** — protocol, OOS build and analyser hashes verified |
| **data loss** | **NONE.** v142's exact bytes exist in the repository as `V53_EXEC_P15_G1_first_choch_pivot.pine`; v143 exists as `docs/p9_extraction_probe.pine`; v1 and every intermediate version remain retrievable from TradingView |

**Version 143 was not deleted** (§9). The entire history is intact.

### Correcting my own P-9 disclosure

The P-9 document described the overwrite as hitting "an existing saved user script", which implied
a preserved user artifact was damaged. That was **overstated in one direction and understated in
another**:

- **Overstated:** no preserved user script was harmed. The slot is scratch space this project has
  overwritten continuously, as its own Phase 13B audit records.
- **Understated:** the displaced version was not "V4 Gold DEBUG" but a **V53 Phase-15 build** —
  research-adjacent content, and a more notable thing to have overwritten than the name suggested.

Both corrections point the same way on impact: nothing was lost, because that build is committed.

---

## 6. Options for the owner

No action is required — nothing is lost. If the slot should be tidied, the choices are:

1. **Leave it.** The slot is working scratch space; v143 is as valid an occupant as v142 was.
2. **Restore v142** to put the Phase 15 G1 build back in the slot. Use TradingView's native version
   history in the Pine editor. This creates v144.
3. **Restore v1** if the original V4 Gold DEBUG strategy is genuinely wanted back. Also creates
   v144, and displaces the V53 build from the slot.
4. **Rename the slot** so the stale "V4 Gold DEBUG" label stops implying content it has not held
   since version 1.

**Recommended, if anything is done: option 4 plus option 1.** The recurring hazard is the misleading
name, not the contents.

### Preventing recurrence

`pine_smart_compile` picks its own button and clicked *Pine Save* rather than *Add to chart*. Any
future Pine work in this project should read the slot's current `title` and `version` **before**
injecting source, so the operator knows what is about to be displaced. That check costs one
`pine_list_scripts` call.

---

## 7. An unverified risk, flagged not investigated

The protected chart `2d43Iesr` carries a study named `V53 LTF SEQUENCE` (entity `0f0OTQ`, observed
in P-6). Whether a TradingView chart study pins the script version it was added at, or follows the
saved script's latest version, **was not determined**. If it follows the latest, that study could
now be bound to v143 — the P-9 probe — rather than a V53 build.

**This was deliberately not checked.** §6 of this task forbids opening `2d43Iesr`, and answering the
question requires attaching to it and reading its study state.

Assessment, offered as reasoning rather than evidence: P-9's "Add to chart" created a *new* study
instance on the disposable layout `P2NtY6fg` and did not touch the protected chart, and the
protected chart's tab held the same CDP target id before and after P-9. Nothing observed suggests
its study changed. But the binding question itself is genuinely open.

**Recommendation:** a narrow, separately authorised, read-only check of `2d43Iesr`'s study list and
pine version — nothing else — would close it. It should be authorised explicitly rather than folded
into another phase.

---

## 8. Final state

**`V4 Gold DEBUG` (the slot) currently holds version 143 — the P-9 extraction probe. It was not
restored, by design.** Version 142 (the Phase 15 G1 V53 arm), version 1 (the original V4 Gold DEBUG
strategy) and every intermediate version remain fully retrievable from TradingView's version
history.

Verification run after the investigation: guards PASS, 299 bot tests OK, 43 analyser tests OK,
`verify_p16_oos.py` PASS, all eight frozen hashes unchanged.
