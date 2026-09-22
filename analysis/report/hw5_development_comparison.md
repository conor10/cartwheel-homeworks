# HW5 development results — first versions

Both approved live batches completed on the same 33 development conversations
(13 human Pass, 20 human Fail). Inputs and split are unchanged. No test
predictions were generated or inspected.

| Judge | TPR: agrees with Pass | 95% Wilson CI | TNR: detects Fail | 95% Wilson CI | Disagreements |
| --- | ---: | --- | ---: | --- | ---: |
| gpt-4o-mini | 9/13 (69.2%) | 42.4–87.3% | 8/20 (40.0%) | 21.9–61.3% | 16 |
| jev-1.13.0 | 12/13 (92.3%) | 66.7–98.6% | 3/20 (15.0%) | 5.2–36.0% | 18 |

GPT confusion counts: TP=9, FN=4, TN=8, FP=12.
Jev confusion counts: TP=12, FN=1, TN=3, FP=17.
Both miss many human-labeled failures. Jev more often predicts Pass. This small
sample does not establish a reliable general ranking; intervals are wide.
Jev has probabilities but no written critiques. The models use the same
training evidence and rubric with provider-specific output instructions.

There are 22 distinct conversations where at least one model disagrees.
Use **HW5 review → Development disagreements** to inspect the recorded reply,
your label, GPT's critique and Jev's verdict/probabilities. Record whether the
judge is wrong, your label needs correcting or the boundary needs clarification.
Saving an assessment does not silently relabel a trace. If correcting a label,
use the human label editor too, then recalculate metrics before prompt revision.
GPT's 16 disagreements are required for the main homework; Jev's additional
cases are part of the optional comparison.

Assessments are saved in `analysis/state/hw5_disagreement_reviews.json` when
submitted. Current human labels, both model caches, and prior evidence are
preserved. No revised prompts or further paid runs have been started.

All 27 offline review-app tests pass, including protection against exposing
test predictions through the development UI. Live observations here are from
the two approved batches, not the offline test stubs.

## After student review — 22 September 2026

All original disagreements have been reviewed, including support-0074's direct
label correction. Six additional labels were reconciled from explicit
`human_label_wrong` assessments. These are student judgments, not inferred
relabels to improve model scores. Prior label history and original metrics are
preserved in the label log and `*-before-review.json` reports.

The unchanged development split now contains 14 Pass and 19 Fail labels.
Recalculation from the same cached predictions gives:

| Judge | TPR | 95% Wilson CI | TNR | 95% Wilson CI | Remaining disagreements |
| --- | --- | --- | --- | --- | ---: |
| gpt-4o-mini v0 | 13/14 (92.9%) | 68.5–98.7% | 11/19 (57.9%) | 36.3–76.9% | 9 |
| jev-1.13.0 v0 | 14/14 (100%) | 78.5–100% | 4/19 (21.1%) | 8.5–43.3% | 15 |

These changes reflect corrected human labels, not model improvement. No new
model calls occurred during recalculation. The figures earlier in this document
record the pre-review baseline; the JSON metrics now reflect current labels.

Revision 1 has been drafted for both providers. It clarifies the difference
between broadly related facts and useful detail, excessive order inventories,
policy granularity, focused clarification, unnecessary history and premature
refund mechanics. It preserves requested calculation detail and concise ticket
or data-limitation explanations. The same three training examples remain; no
development examples or identifiers have been added to either prompt.

Files: `analysis/prompts/irrelevant_response_detail-v1.txt` and
`analysis/prompts/irrelevant_response_detail-jev-v1.json`.
The next proposed paid runs are 33 development traces each on gpt-4o-mini and
jev-1.13.0. Approval is pending. This is the first of at most two revisions.
The held-out test predictions remain untouched. Input and original-prompt
hashes and training-only provenance were checked offline. All remaining GPT
disagreements have assessments. The label corrections create two additional
Jev disagreements (support-0064 and support-0211) that had previously agreed
with the old labels; no separate Jev assessment was invented for those cases.
