# HW5 Part A proposal

Status: mode approved; human label collection in progress. See the 21 September update below for current counts.
Prepared 20 September 2026. No judge batches have run and no HW5 split has been made.

## Recommended mode

Use `irrelevant_response_detail` (HW4 version 3). It has the strongest existing
label coverage and requires contextual judgment: response length or a list of
forbidden fields cannot tell whether information answers the current request.

**Question:** Does the customer-facing final reply contain information that can
be removed without losing anything needed to answer the current request,
identify the requested item, explain the relevant decision, communicate an
action result, or give a necessary next step?

- **Fail (0):** Identify a specific removable passage and explain why it is
  irrelevant or repetitive in this conversation. This can include unnecessary
  order fields, unrelated policy branches, repeated explanations, or internal
  lookup/process descriptions.
- **Pass (1):** No passage meets that failure rule. A detailed reply can pass
  when the user requested the detail or needs it to understand the decision.

The intended behavior is recorded in `SPEC.md` RESP-6, supported by RESP-5.
RESP-6 is an HW4 refinement; it is not a claim that the running agent was
already updated to implement that requirement.

## Boundary and evidence

Use the current user request, the evaluated final reply, relevant earlier
turns, and the tool results or policy passages needed to decide whether the
reply's details were necessary.

Preserve requested calculations, necessary explanations of inconsistent data,
relevant action identifiers and required policy citations (RESP-1). Include a
link only where a verified destination exists; absence of an unavailable link
is not this failure. Length alone is insufficient evidence.

Evaluate customer-facing final replies. Do not count model-only narration as
customer-visible detail. Tool efficiency, correctness, missing information and
other taxonomy categories are separate judgments: a trace can pass this mode
and still fail another. Missing final replies should not be used as easy Pass
examples for a judge of reply relevance.

Human notes, labels and scenario metadata are evidence for collecting labels,
but must not enter the eventual judge inputs. Prompt examples will be chosen
only from training after the split.

## Existing label audit

The read-only audit is saved in `hw5_part_a_audit.json`, including trace IDs,
provenance, exclusions and candidate lists.

| Evidence | Count | Interpretation |
| --- | ---: | --- |
| Saved HW4 labels for this mode | 44 | All failure-present |
| Retained after scenario/session deduplication | 42 | Reusable Fail candidates; close variants still need checking |
| Extra records from already represented scenarios | 2 | Excluded from the preliminary count |
| Prior no-failure reviews agreeing with an existing absent-mode proposal | 26 | Potential Pass cases, not confirmed HW5 labels |
| Other prior no-failure reviews needing boundary reconciliation | 17 | Candidates requiring a mode-specific decision |

The 42 retained cases are distinct scenarios and sessions, but are not yet
certified independent of close scenario variants. Counts may fall after that
check. Existing proposals are not substituted for the student's judgments.

## Next step after mode selection

Reuse the explicit HW4 judgments and review potential Pass cases through the
existing interface. The handout requires at least 30 Pass and 30 Fail from
independent conversations, with approximately 100 total recommended. If all
26 initial Pass candidates are confirmed and remain independent, at least
four additional Pass cases are needed. More may be needed after review.

Export only confirmed eligible labels to
`analysis/state/hw5_labels/irrelevant_response_detail.jsonl`, retaining evidence
and provenance. HW5 uses Pass=1 / Fail=0, the reverse of HW4's failure flag.
Keep the original HW4 files intact. No HW5 labels have been exported yet.

Proceed to Part B only when the label collection is sufficient, or document an
early stop if enough examples cannot be found. No requirement to review every
HW4 trace against every category is introduced by this work.

## Preparation completed

- Merged course upstream and pushed the fork at
  `54aa41229a712dccb50d1b992a16814021590f9e`.
- Read the handout, SPEC and official `write-judge-prompt` and
  `validate-evaluator` skill instructions. Used the instructions directly;
  skill installation was blocked by automatic approval review of the unpinned
  `npx` installer and has not been completed.
- Confirmed DocETL, NumPy and pytest are present in the existing environment.
- Performed a local label/provenance audit only. No live model calls or paid
  batches; no application behavior changed and no test suite run was needed
  for this documentation-only preparation.

## Update — 21 September: mode approved and review queue prepared

The student agreed to the recommended mode. A dedicated **HW5 review** tab is
available in the existing interface. `analysis/state/hw5_review.json` records
selection provenance and the grouping rule. Preparation is reproducible via
`analysis/prepare_hw5_review.py`, which refuses to overwrite existing work.

After excluding two known close variants (the repeated missing-delivery-date
fixture and invalid-product-price fixture), 40 existing human Fail judgments
were exported with Pass=1 / Fail=0 encoding. Original HW4 labels were preserved.
Final semantic independence checking remains pending before Part B.

The unlabelled queue contains 50 candidates: 19 from earlier no-failure reviews
with absent-mode proposals, 12 needing boundary reconciliation, and 19 random
candidates from the supplied helper. Grouping removes repeated fixtures,
orders and substantive non-order scenario variants. No candidate was assigned
an automatic Pass label. Review enough to reach 30 confirmed Pass labels;
there is no requirement to exhaust all candidates. Saved labels remain editable.

Validation: 21 offline review-app tests passed, including HW5 persistence,
revision conflicts, editing history and preservation of HW4 data. JavaScript
syntax and whitespace checks passed. No model calls, paid runs or splits.
