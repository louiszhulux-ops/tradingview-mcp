# Phase P-10C — Restore the V53 Study Binding on `2d43Iesr`

## 1. Executive conclusion

## **BLOCKED — target version PROVEN, but no supported mechanism exists**

The restoration target is **not** in doubt. It is **v142.0**, and that is proven from committed
evidence rather than inferred — including one record inside a **frozen-hash-protected file**.

What blocks restoration is §5: **TradingView provides no supported mechanism to re-point an existing
study instance to a different script version.** The only two routes available are the ones §5
explicitly forbids without escalation:

| route | why it is blocked |
|---|---|
| `gateway.modifyStudy(...)` with a hand-built v142 metaInfo | an internal protocol call, not a supported mechanism. Constructing a study descriptor by hand and firing it at the **protected** chart is improvisation, which §5 forbids |
| open v142 in the editor → **Add to chart** → remove `0f0OTQ` | **delete-and-recreate.** §5 requires a STOP rather than this. It also allocates a new study id, and it re-enters the exact editor sequence that caused the incident |

**No mutation was performed.** The chart is byte-for-byte as found.

---

## 2. Incident recap

P-9's `Pine Save` re-pointed study `0f0OTQ` on `2d43Iesr` from the Phase 15 G1 V53 build
(**v142.0**) to **v143.0**, the P-9 extraction probe. Established in P-10B; the pin is persisted
(`_hasChanges = false`), so a reload will not undo it.

---

## 3. Read-only precheck (§1) — expected state confirmed

| field | value |
|---|---|
| chart id | `2d43Iesr` |
| CDP target id | `8D794F5A7058D49DD9AFCF35918D15DA` |
| symbol | `CME_MINI_DL:MNQ1!` |
| resolution | `5` |
| chart type / style | `1` |
| total data sources | 13 (3 user studies + series, crosshair and 8 built-ins) |
| **V53 study id** | **`0f0OTQ`** |
| **current binding** | **`{"digest":"b297606aaf555641335ee8429382135fa698ce6d","version":"143.0"}`** |
| slot | `USER;b798deb2c9084500a1c38b14775961da` |
| inputs | `(1, false, false)` — the probe's `ltfStr`/plot defaults |
| control study | `gNx1DZ` @ `48.0`, digest `affadef4…` |
| `_hasChanges` | `false` |

Current binding **is v143**, so the §1 gate passes and the state is as expected.

The chart legend renders it directly: `P9 LTF EXTRACTION · 143.0` alongside
`V8.3 XAU - Trend + Range (cost-hardened) · 48.0`.

---

## 4. Target version — **PROVEN, not assumed** (§2)

The brief warned against assuming v142. The assumption is unnecessary: the version is **recorded in
writing, contemporaneously, in four committed places.**

### 4.1 Documentary evidence

**`trader_v2/p16/PHASE16_PROTOCOL.md:356-357`** — this file is one of the eight frozen hashes
(`c5b6c85315ee48be407786644d7e310857ad6a98985587b6b3a9c1cc85bbf3d3`), verified unchanged before and
after this phase. It was written before P-9, and is tamper-evident:

> *"Restore the chart: inject the Phase 16 artifact and compile. (At protocol time the chart
> carries the Phase 15 G1 experimental build, `pineVersion 142.0`; it must be replaced.)"*

**`trader_v2/p15/PROGRESS.md:177-178`**

> *"NO STRATEGY RUN HAS OCCURRED. Nothing injected into TradingView. The chart still carries the
> Phase 15 G1 build (pineVersion 142.0), to be replaced at the boundary."*

**`trader_v2/p15/PROGRESS.md:195-196`**

> *"The chart intentionally retains the Phase 15 G1 build (pineVersion 142.0) for the duration; it
> is replaced only at the boundary."*

**`trader_v2/p15/PROGRESS.md:143-146`**

> *"OUTSTANDING HOUSEKEEPING: the TradingView cloud script
> USER;b798deb2c9084500a1c38b14775961da currently holds the G1 source at pineVersion 142.0."*

### 4.2 Independent content corroboration

The documentary record is confirmed by byte-identity, so the two chains are independent:

- TradingView **v142** source, LF-normalised with trailing newline → sha256
  `ef56c15f47988307e0ea47bdc2a18923d2125d712b152ffd56931c5711bf3c11` (established in P-10A).
- `trader_v2/p15/exec_arms/V53_EXEC_P15_G1_first_choch_pivot.pine` → **the same sha256**.
- That hash is itself recorded independently in `p15/EXPERIMENT_G1_choch_selection.md:18` and
  `p15/PHASE15_PROVENANCE_CORRECTION.md:127`.

### 4.3 Why the name alone would not have sufficed

v138, v140, v141 and v142 **all** identify as `V53 LTF SEQUENCE LEDGER`. The P-6 observation of the
display name `V53 LTF SEQUENCE` therefore does **not** discriminate between them, and would not have
been adequate evidence on its own. Only the explicit `pineVersion 142.0` records, plus the
size/digest match isolating v142 as the sole G1-content version, establish the target.

**RESTORE TARGET = v142.0**, digest = sha256 of the G1 source above.

---

## 5. Why restoration is blocked (§5)

### 5.1 No supported in-place mechanism

Inspection of the live study object and the gateway found nothing that re-points a study's source:

- **Study prototype** — `restart`, `replaceData`, `metaInfo`, `originalMetaInfo`, `isPine`,
  `pineSourceCodeModel`, `_changeInputsImpl`, `_getStudyIdWithLatestVersion`, … There is **no**
  public method to set the pine version or swap the bound source. `replaceData` replaces *data*, not
  the source binding. `_getStudyIdWithLatestVersion` is private and moves toward *latest*, which is
  the wrong direction.
- **Gateway** — `createStudy`, `modifyStudy`, `notifyStudy`, `removeStudy`. `modifyStudy` is the
  raw protocol call, not a user-facing mechanism.
- **UI** — the study legend shows the version (`· 143.0`) but exposes no selector. A DOM sweep for
  version controls and update badges (`[class*="update"]`, `[title*=version]`,
  `[aria-label*=version]`) returned **nothing**. TradingView's study settings dialog has inputs,
  style and visibility — no version control.

### 5.2 The two possible routes, and why each is out of scope

**Route A — `modifyStudy` with a synthesised v142 descriptor.** Would require hand-constructing a
metaInfo (digest, version, plots, inputs, styles) and sending it to the server for the study on the
**protected** chart. A malformed descriptor could break the study, drop it, or leave the chart in a
state neither v142 nor v143. §5's "do not improvise" rules this out, and I would not do it on this
chart regardless.

**Route B — add v142 from the editor, remove `0f0OTQ`.** This is delete-and-recreate: §5 requires a
STOP rather than performing it. It would also allocate a **new study id**, so the §7 check "same
study IDs" could not pass, and it re-enters the editor flow that caused the original incident —
a mis-click on *Pine Save* there would create v144 and compound the problem.

### 5.3 What I did not do

No mutation of any kind: no study added, removed or modified; no Pine Save; no compile; no new
script version; no input change; no symbol, resolution, chart-type, session or range change; no
deletion. Every operation in P-10C was a read.

---

## 6. Context that bears on whether restoration is even wanted

Two things surfaced in the §2 evidence that the owner should weigh before authorising a broader
mutation.

**1. The G1 build was already scheduled for replacement.** `PHASE16_PROTOCOL.md:356-357` — the same
frozen line that proves the target — states the G1 build *"must be replaced"* at the boundary, and
step 3 of the boundary procedure is *"inject the Phase 16 artifact and compile."* The chart's V53
study was never intended to survive; the protocol overwrites whatever is attached. In that sense the
P-9 damage is **already scheduled to be undone** by the boundary procedure itself.

**2. The slot state was already flagged as outstanding housekeeping.** `PROGRESS.md:143-146` records
that the slot held the *G1 arm* rather than the executed baseline, and that the baseline
*"should be re-injected and recompiled to restore the cloud script when convenient."* That
housekeeping item predates P-9 and is unrelated to it.

**This does not make restoration pointless.** Anyone following the protocol at the boundary will
find `P9 LTF EXTRACTION · 143.0` where the protocol's parenthetical says to expect
`pineVersion 142.0`. Without this document that mismatch would look alarming. With it, the
discrepancy is explained and the boundary procedure can proceed unchanged.

**Note:** `PHASE16_PROTOCOL.md` is frozen and was **not** edited to reflect the new state. Its
parenthetical is now historically accurate but currently stale, and that is the correct outcome —
the protocol is a frozen artifact, and this document carries the correction instead.

---

## 7. Recommendation

**Do nothing to the chart until the Phase 16 boundary**, and let the boundary procedure's own
"inject the Phase 16 artifact and compile" step establish the correct study. This requires no extra
mutation, no delete-and-recreate, and no new script version.

If the owner nevertheless wants v142 back on the chart before then, the authorisation should be
explicit that it permits **delete-and-recreate**, and should carry these constraints:

1. Target **v142.0** only, verified by digest `ef56c15f…` before adding.
2. **Never click Pine Save** — open the version, *Add to chart*, nothing else.
3. Expect and accept a **new study id**; `0f0OTQ` cannot be preserved by this route.
4. Remove the v143-bound study only *after* the v142-bound study is confirmed present.
5. Re-verify symbol, resolution, chart type, the `gNx1DZ` control at v48.0, and that the slot is
   still at v143 (the slot must **not** be restored — §3 of the brief).

---

## 8. Verification

### Chart state — unchanged (0 mutations)

| check | before | after |
|---|---|---|
| chart id | `2d43Iesr` | `2d43Iesr` |
| CDP target id | `8D794F5A7058D49DD9AFCF35918D15DA` | same |
| symbol | `CME_MINI_DL:MNQ1!` | same |
| resolution | `5` | same |
| chart type | `1` | same |
| data-source count | 13 | 13 |
| study ids | `0f0OTQ`, `gNx1DZ`, `V8L5rU` + built-ins | same |
| `0f0OTQ` binding | `143.0` / `b297606a…` | `143.0` / `b297606a…` |
| `gNx1DZ` binding | `48.0` / `affadef4…` | `48.0` / `affadef4…` |
| study inputs | `(1, false, false)` | unchanged |
| `_hasChanges` | `false` | `false` |

### Safety confirmations

- **No other study changed** — `gNx1DZ` and `V8L5rU` identical, all built-in sources identical.
- **No other chart changed** — `P2NtY6fg` untouched in this phase; no other chart opened.
- **No Pine Save occurred** — the editor was never opened in P-10C.
- **No new script version created** — the slot remains at **v143.0**, as §3 and the
  non-negotiable rule require. The slot was deliberately **not** restored.
- **No repository research artifact changed** — all eight frozen hashes verified unchanged before
  and after.
- **No V53 output read** — no FUNNEL, signals, ledger or OOS values. The study is not a V53 study
  in any case.

### Repository

Guards PASS · 299 bot tests OK · 43 analyser tests OK · `verify_p16_oos.py` PASS · all eight frozen
hashes unchanged. Only this document was created.

---

## 9. Status

**BLOCKED — restoration requires a broader mutation than P-10C authorises.**

Target version proven (**v142.0**). Mechanism unavailable within scope. Chart left exactly as found.
