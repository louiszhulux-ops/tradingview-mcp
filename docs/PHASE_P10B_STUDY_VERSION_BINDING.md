# Phase P-10B — Study Version Binding on `2d43Iesr`

## 1. Executive conclusion

## **RESOLVED — PINNED, and the pin was rewritten to v143**

**The V53 LTF SEQUENCE study on the protected chart is gone. Study `0f0OTQ` is now bound to
version 143.0 — the P-9 extraction probe.**

TradingView studies *do* carry an explicit, persisted version pin (`pine: {digest, version}`), and
that pin normally survives later saves to the same slot. This chart proves it: a second study on
the same chart, bound to the same slot, still holds **version 48.0** after roughly 95 subsequent
slot saves. So this is not dynamic latest-version resolution — pins persist.

Which means the P-9 `Pine Save` did not merely overwrite a scratch slot. **It rewrote the source
binding of a study on the protected research chart.**

### A correction I have to make plainly

In P-9 I wrote that the incident affected "no repository file, frozen artifact or research chart".
In P-10A I repeated that `2d43Iesr` was unaffected. **Both statements were wrong.** The research
chart *was* affected: its V53 study now runs my extraction probe. I did not verify this at the time
— in P-9 I checked only the tab's CDP target id, and in P-10A the task forbade opening the chart.
Flagging it as an open risk at the end of P-10A was right; asserting "unaffected" earlier was not.

**What is not affected**, verified rather than assumed: every frozen repository artifact. All eight
hashes unchanged. The committed V53 sources, the Phase 16 artifacts, the frozen datasets and all
recorded research results are intact.

---

## 2. Question

Does the study attached to `2d43Iesr` pin a specific Pine version, or follow the saved-script slot's
current version?

---

## 3. Chart and study identity

Chart `2d43Iesr`, CDP target `8D794F5A7058D49DD9AFCF35918D15DA` — the same target id recorded at the
end of P-9 and at the start of P-10B.

| | |
|---|---|
| symbol | `CME_MINI_DL:MNQ1!` |
| resolution | `5` |
| chart type | `1` |
| user studies | `0f0OTQ`, `gNx1DZ`, `V8L5rU` (plus 4 built-in `ESD$TV_*` sources) |

**The study in question:**

| field | value |
|---|---|
| study instance id | **`0f0OTQ`** — unchanged since P-6 |
| displayed name in P-6 (pre-P-9) | **`V53 LTF SEQUENCE`** |
| displayed name now | **`P9 LTF EXTRACTION (1, false, false)`** |
| `metaInfo.id` | `Script$USER;b798deb2c9084500a1c38b14775961da@tv-scripting` |
| `metaInfo.fullId` | `Script$USER;b798deb2c9084500a1c38b14775961da@tv-scripting-101` |
| `metaInfo.scriptIdPart` | `USER;b798deb2c9084500a1c38b14775961da` |
| **`metaInfo.pine`** | **`{"digest":"b297606aaf555641335ee8429382135fa698ce6d","version":"143.0"}`** |
| `metaInfo.description` | `P9 LTF EXTRACTION` |
| `metaInfo.version` | `101` (the *metainfo schema* version, not the script version) |
| `useVersionFromMetaInfo` | `false` |

**The study entity id never changed.** No study was added, removed or replaced. What changed is the
Pine source that instance resolves to.

---

## 4. Evidence: the pin is explicit and persisted

`study.state()` — the descriptor the layout serialises — contains the version directly:

```
type      : "Study"
id        : "0f0OTQ"
metaInfo  :
  scriptIdPart : "USER;b798deb2c9084500a1c38b14775961da"
  pine         : { digest: "b297606aaf555641335ee8429382135fa698ce6d", version: "143.0" }
  version      : 101
  description  : "P9 LTF EXTRACTION"
state     : { parentSources: … }        <- no pine fields here
```

Per §2 this is an **explicit immutable version reference**: a version number *and* a content digest.
Classification: **PINNED**.

### The control that rules out dynamic resolution

The same chart carries a second Pine study bound to the **same slot**:

| study | id | `pine.version` | `pine.digest` |
|---|---|---|---|
| `V8.3 XAU - Trend + Range (cost-hardened)` | `gNx1DZ` | **`48.0`** | `affadef49c2ea25c4451008cb61ff3b811328eb5` |
| (was `V53 LTF SEQUENCE`) | `0f0OTQ` | **`143.0`** | `b297606aaf555641335ee8429382135fa698ce6d` |

Both carry `scriptIdPart = USER;b798deb2c9084500a1c38b14775961da`. **Two studies, one slot, two
different pinned versions.**

`gNx1DZ` has held **v48** through roughly 95 subsequent saves to that slot. If chart studies
resolved the slot's latest version at load time, it would read 143.0 as well. It does not.

**Therefore: DYNAMIC LATEST-VERSION RESOLUTION IS DISPROVEN.** Pins persist across slot saves.

### What this implies about the cause

Since loads do not re-resolve, the only event that could have moved `0f0OTQ` from a V53 version to
143.0 is **the P-9 `Pine Save` itself**, which re-pointed the study instance that corresponded to
the script being edited. The chart's layout reports `_hasChanges = false`, meaning the v143 binding
is the **saved** state, not a transient in-memory difference — reloading the chart will not bring
V53 back.

**Stated at its evidential limit:** that the save is the cause is a strong inference from (a) the
pin's persistence, (b) the one-version step from 142→143, and (c) the timing. It is not directly
observed, because observing it would require repeating the save — which §5 forbids and which I would
not do regardless.

---

## 5. Reference chain (§4)

```
chart 2d43Iesr
  └─ study instance  0f0OTQ                      (id stable since P-6)
       └─ metaInfo.scriptIdPart  USER;b798deb2c9084500a1c38b14775961da   (slot)
            └─ metaInfo.pine     { version: "143.0", digest: "b297606a…" }   (immutable ref)
```

This is **option A** in §4: slot ID **plus** an immutable version ID. Both nodes are present, and
the terminal node is a specific version with a content digest.

---

## 6. Relationship to v142 and v143

| | |
|---|---|
| **v142** (`V53 LTF SEQUENCE LEDGER`, byte-identical to `trader_v2/p15/exec_arms/V53_EXEC_P15_G1_first_choch_pivot.pine`) | **The study does NOT point at v142.** Given the P-6 display name it almost certainly did before P-9; it does not now |
| **v143** (P-9 extraction probe) | **The study points at v143**, confirmed by both version number and digest |

---

## 7. Chart integrity

**Unchanged by P-10B.** Every operation in this phase was a read.

| check | baseline | after | result |
|---|---|---|---|
| chart id | `2d43Iesr` | `2d43Iesr` | same |
| CDP target id | `8D794F5A7058D49DD9AFCF35918D15DA` | same | same |
| symbol | `CME_MINI_DL:MNQ1!` | same | same |
| resolution | `5` | same | same |
| chart type | `1` | same | same |
| user study ids | `0f0OTQ`, `gNx1DZ`, `V8L5rU` | same | same |
| study count | 3 user + 4 built-in | same | same |
| `_hasChanges` | `false` | `false` | no unsaved modification introduced |
| studies added / removed / modified | — | none | — |
| Pine Save / compile / execute | — | none | — |

No V53 output was read: no FUNNEL, no signals, no ledger, no OOS values. Only identity and
provenance metadata was inspected. The study's *displayed name* was observed, which is metadata, not
strategy output — and it is in any case no longer a V53 study.

**The binding change predates P-10B.** It is persisted (`_hasChanges = false`), so it was already
saved before this phase attached, and a read cannot rewrite a persisted pin.

---

## 8. What this means, and what it does not

**It does not compromise the research.** The Phase 13F/14/15 runs were captured on 2026-09-06 and
committed; a later change to the chart's study binding cannot retroactively alter recorded results.
The canonical V53 sources, the Phase 16 protocol and OOS build, the frozen datasets and the roll
calendar are all hash-verified unchanged.

**It does cost the chart's readiness.** `2d43Iesr` no longer has a V53 study loaded. Anyone opening
it expecting the research build will find the extraction probe.

**It matters for Phase 16.** `PHASE16_PROTOCOL.md` requires the P16 OOS artifact to be deployed to
the chart *at the boundary*. That deployment now has to start from a chart with no V53/P16 study
attached. This is a logistics change, not a protocol violation — the P16 artifact is committed and
hash-verified (`5c21acfa…`), and nothing about the accumulation window is affected.

**Restoration is straightforward but is a mutation, and is not mine to perform.** Options, for the
owner: re-add the V53 build from the committed source, or restore slot v142 and re-add. Either
creates a new slot version and modifies the chart, so both need explicit authorisation.

**The generalisable lesson:** a Pine Save can silently re-point an on-chart study instance on a
*different* chart from the one in view. Slot-safety and chart-safety are not the same property, and
checking the tab's target id — which is what I did in P-9 — does not detect this class of change.
Any future Pine Save in this project should be preceded by recording the slot's current version and
followed by verifying the study bindings of every chart that matters.

---

## 9. Classification

**PINNED — VERSION 143.0** (digest `b297606aaf555641335ee8429382135fa698ce6d`).

The pin mechanism is explicit and persistent; **dynamic latest-version resolution is disproven** by
the `gNx1DZ` control at v48.0. The pin's *current value* is v143 because the P-9 save rewrote it.

---

## 10. Repository

All eight frozen hashes verified unchanged before and after. Guards PASS, 299 bot tests OK,
43 analyser tests OK, `verify_p16_oos.py` PASS. Only this document was created.
