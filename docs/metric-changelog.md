# Metric definitions and changelog

Each metric's exact definition, and any change to it.

| ID | Date | Metric / decision | Notebook |
|---|---|---|---|
| M-001 | 2026-08-12 | mean_glucose computed on cgm_mg_dl only, not cbg_mg_dl | 03 |
| M-002 | 2026-08-12 | sd_glucose uses sample SD (ddof=1), not population SD | 03 |
| M-003 | 2026-08-12 | tir_glucose uses 70-180 mg/dl, both boundaries inclusive | 03 |
| M-004 | 2026-08-12 | gmi_glucose uses the Bergenstal 2018 mg/dl formula | 03 |
| M-005 | 2026-08-12 | mage_glucose uses the full classic (Service 1970) algorithm, 1xSD threshold, majority direction | 03 |
| M-006 | 2026-08-12 | mage_glucose treats the first/last reading as explicit boundary turning points | 03 |
| M-007 | 2026-08-12 | mage_glucose averages both directions on a rise/fall count tie | 03 |
| M-008 | 2026-08-12 | excursion_count counts both directions, not just MAGE's majority direction | 03 |
| M-009 | 2026-08-12 | tar_glucose/tbr_glucose use exclusive boundaries, complementing TIR's inclusive 70-180 | 03 |

---

### M-001 — mean_glucose computed on cgm_mg_dl only, not cbg_mg_dl

**Decision.** `mean_glucose` averages `cgm_mg_dl` (the continuous sensor
trace). `cbg_mg_dl` (fingerstick calibration checks) is not included.

**Rationale.** Standard CGM metric definitions (mean glucose, %CV, TIR, GMI,
MAGE — Battelino et al. 2019 consensus) are built on the continuous sensor
trace. `cbg_mg_dl` is a sparse reference check (~4,019 rows cohort-wide vs
128k+ for `cgm_mg_dl`) measured a different way (capillary blood vs
interstitial fluid) — mixing the two would muddy what the number means, not
strengthen it.

**Alternative considered.** Merge both columns into one mean. Rejected — not
standard practice, and the two aren't measuring the same thing.

**Impact.** `mean_glucose` reads only `cgm_mg_dl`. Same reasoning applies to
every other metric in this notebook (SD, %CV, TIR, GMI, MAGE, excursion
count) — they all use `cgm_mg_dl` too, this entry isn't re-argued per metric.

---

### M-002 — sd_glucose uses sample SD (ddof=1), not population SD

**Decision.** `sd_glucose` computes standard deviation with `ddof=1` (divides
the sum of squared deviations by `n-1`, not `n`).

**Rationale.** Each patient-visit's CGM trace is treated as a sample of that
patient's underlying glucose pattern over the monitoring window, not the
complete population of every possible reading that patient could ever have.
`ddof=1` is the standard choice in glycemic-variability literature and is
also pandas' `.std()` default — writing it explicitly (like `skipna=True` in
M-001) makes the assumption visible in the code rather than silently relying
on the default.

**Alternative considered.** `ddof=0`, population SD. Rejected — would treat
the recorded readings as the entire population rather than a sample, not the
conventional framing for this kind of trace data.

**Impact.** `sd_glucose` calls `.std(ddof=1, skipna=True)` on `cgm_mg_dl`.
Feeds into %CV later (SD ÷ mean), so this choice propagates forward.

---

### M-003 — tir_glucose uses 70-180 mg/dl, both boundaries inclusive

**Decision.** Time in Range counts a reading as "in range" if
`70 <= cgm_mg_dl <= 180` (both boundaries inclusive).

**Rationale.** 70-180 mg/dl is the international consensus target range for
TIR in non-pregnant T1DM/T2DM patients (Battelino et al. 2019). The consensus
table treats both boundary values as inside the range, not outside it —
using exclusive boundaries would understate TIR versus the published
definition, and any comparison to literature values needs to match the same
convention.

**Alternative considered.** Exclusive boundaries (`70 < cgm_mg_dl < 180`).
Rejected — not the standard convention, would silently produce a lower TIR
than the definition everyone else is using.

**Impact.** `tir_glucose` uses `>=`/`<=`, not `>`/`<`, when building the
in-range mask.

---

### M-004 — gmi_glucose uses the Bergenstal 2018 mg/dl formula

**Decision.** `gmi_glucose` computes `GMI (%) = 3.31 + (0.02392 × mean_glucose)`,
using `mean_glucose` from `cgm_mg_dl`.

**Rationale.** This is the published formula for glucose in mg/dl (Bergenstal
et al. 2018, "Glucose Management Indicator (GMI): A New Term for Estimating
A1C From Continuous Glucose Monitoring"). A separate formula with different
constants exists for mmol/L data — doesn't apply, `cgm_mg_dl` is already
confirmed mg/dl (D-010). Reuses `mean_glucose` rather than recomputing the
mean independently, same reasoning as `cv_glucose` reusing `mean_glucose`/
`std_glucose` (M-001/M-002) — guarantees GMI always agrees with whatever
`mean_glucose` actually does, including its gap-handling.

**Alternative considered.** None — this is a fixed external formula, not a
judgment call between competing conventions like M-002/M-003.

**Impact.** `gmi_glucose` calls `mean_glucose(df)` internally, applies the
formula, returns a percentage.

---

### M-005 — mage_glucose uses the full classic (Service 1970) algorithm, 1xSD threshold, majority direction

**Decision.** `mage_glucose` implements the original Service et al. 1970
definition: find turning points (local peaks/troughs) in the trace, keep
only swings whose amplitude exceeds 1×SD (reuses `std_glucose`), classify
each surviving swing as a rise or a fall, keep only the majority direction
(whichever has more qualifying swings), average that direction's amplitudes.

**Rationale.** This is the textbook-exact definition, not an approximation —
the number is defensible as "MAGE" without a caveat. The alternative
(simplified: skip the majority-direction step, average all qualifying swings
regardless of direction) shares the same turning-point-detection groundwork,
so the extra rigor is a bounded addition, not a different algorithm.

**Alternative considered.** Simplified version (no majority-direction
filtering). Rejected — the extra two steps (direction labeling, majority
selection) are small relative to the shared groundwork (turning-point
detection), and the classic version is the one actually named in the CGM
literature.

**Impact.** `mage_glucose` is built in stages (turning-point detection →
1xSD filter → direction labeling → majority selection → average) rather than
one line, unlike every other metric in this notebook so far.

---

### M-006 — mage_glucose treats the first/last reading as explicit boundary turning points

**Decision.** The first and last readings of a patient-visit's trace are
deliberately marked as turning points, not left as a side effect of
comparing against `NaN`.

**Rationale.** While computing `diff_sign != diff_sign.shift(-1)` (M-005's
turning-point step), the first and last rows came back `True` — but by
accident, not by design: both rows compare against a missing `diff_sign`
value, and `!=` against `NaN` always returns `True` regardless of the real
values involved (the one exception to the "NaN comparisons return False"
rule from M-003/TIR). The result happens to match the correct behavior — an
excursion needs a defined start and end, so the trace's first and last
readings should bound the first and last excursion — but "it happened to
come out right because of how NaN comparison works" isn't a defensible
reason on its own. Made explicit instead: interior turning points computed
cleanly (edge comparisons treated as `False`), then row 0 and the last row
set to `True` deliberately, with the real reason stated in code.

**Alternative considered.** Leave the `NaN`-coincidence result as-is (same
output, undocumented reason) — rejected, not defensible. Exclude endpoints
entirely — rejected, risks missing a real excursion that starts or ends at
the edge of the trace.

**Impact.** `mage_glucose`'s turning-point mask no longer depends on `NaN`
comparison behavior; the boundary inclusion is a deliberate two-line
assignment, not an implicit side effect.

---

### M-007 — mage_glucose averages both directions on a rise/fall count tie

**Decision.** If the count of qualifying rise excursions equals the count of
qualifying fall excursions, `mage_glucose` averages **all** qualifying
swings, rises and falls combined, instead of picking one direction.

**Rationale.** The majority-direction rule (M-005) exists to pick the
direction that actually dominates the trace. On a tie, neither direction
dominates — so forcing a pick (rises, or falls) would assert a "majority"
that doesn't exist. Treating a tie as "no clear majority, use everything
qualifying" is a principled reading of what the rule is for, not an
arbitrary coin flip.

**Alternative considered.** Default to rises on a tie (or default to falls)
— both rejected as arbitrary: neither direction has a clinical reason to
win, so picking either one asserts a majority that isn't there.

**Impact.** `mage_glucose` compares `len(rises)` to `len(falls)`: strictly
greater picks that direction, strictly fewer picks the other, and equal
counts fall through to averaging `qualifying` as a whole.

---

### M-008 — excursion_count counts both directions, not just MAGE's majority direction

**Decision.** `excursion_count` counts every turning-point swing exceeding
1×SD, rises and falls combined — not just whichever direction
`mage_glucose` ended up averaging.

**Rationale.** MAGE's majority-direction restriction (M-005/M-007) is
specific to how *that metric's average* is computed — it's not a claim that
the minority-direction swings weren't real excursions. As a standalone
descriptive count ("how many significant glycemic swings happened this
visit"), there's no reason to discard half the qualifying swings just
because MAGE does for its own purposes.

**Alternative considered.** Match `mage_glucose` exactly (majority direction
only). Rejected — would undercount real excursions and tie the two metrics
together for a reason that doesn't actually apply to a plain count.

**Impact.** `excursion_count` counts the full `qualifying` set (both
directions) — the same swings `mage_glucose` computes before it splits them
into rises/falls.

---

### M-009 — tar_glucose/tbr_glucose use exclusive boundaries, complementing TIR's inclusive 70-180

**Decision.** `tar_glucose` counts `cgm_mg_dl > 180`. `tbr_glucose` counts
`cgm_mg_dl < 70`. Neither reuses the `>=`/`<=` boundary `tir_glucose` claims.

**Rationale.** M-003 already claims `70` and `180` as part of the target
range (inclusive both ends). If TAR/TBR used the same inclusive boundaries,
a reading of exactly `70` or `180` would be double-counted in two bands at
once, and TIR + TAR + TBR would sum to over 100% — not defensible. Exclusive
boundaries here mean every real reading falls into exactly one of the three
bands, so they sum to exactly 100%, matching the Battelino et al. 2019
consensus convention and giving a built-in correctness check.

**Alternative considered.** Inclusive boundaries on all three. Rejected —
double-counts boundary readings, breaks the 100% sum.

**Impact.** `tar_glucose` uses `>`, `tbr_glucose` uses `<`, both strict —
the plan's Phase 2 list (mean, SD, %CV, TIR, **TAR, TBR**, GMI, MAGE,
excursion count) is now fully covered.
