# Development comparison after revision 1

Both approved live batches completed on the same 33 development traces, with
14 human Pass and 19 human Fail labels. These labels are the reconciled labels
from the student's first review. No further labels were changed in this run.

| Model / version | TPR | 95% Wilson interval | TNR | 95% Wilson interval | Disagreements |
| --- | --- | --- | --- | --- | ---: |
| GPT-4o-mini v0 | 13/14 = 92.9% | 68.5–98.7% | 11/19 = 57.9% | 36.3–76.9% | 9 |
| GPT-4o-mini v1 | 11/14 = 78.6% | 52.4–92.4% | 10/19 = 52.6% | 31.7–72.7% | 12 |
| Jev v0 | 14/14 = 100% | 78.5–100% | 4/19 = 21.1% | 8.5–43.3% | 15 |
| Jev v1 | 14/14 = 100% | 78.5–100% | 10/19 = 52.6% | 31.7–72.7% | 9 |

GPT v1 confusion counts: TP=11, FN=3, TN=10, FP=9.
Jev v1 confusion counts: TP=14, FN=0, TN=10, FP=9.

Revision 1 improves Jev's failure detection on this development set. GPT's
aggregate rates decline. The intervals are wide; this is development evidence,
not proof of a general model ranking or a held-out result. GPT v0 remains the
better of its two versions by both observed rates. No model is frozen yet.

GPT v1 newly flags support-0071 and support-0072 for information such as order
identification or relevant cancellation policy, despite rubric exceptions.
It also rejects the corrected Pass on support-0168. These are priority cases
for human review before deciding whether to use the remaining revision.
Do not revise human labels merely to improve alignment.

The UI defaults to the latest version of each model and offers **Include earlier
judge versions**. Under **Development disagreements**, inspect each current
GPT disagreement and record whether the judge, label or boundary needs fixing.
Jev review remains optional. Previous assessments are preserved under their
original run IDs and are not silently copied to new predictions.

Validation: all 27 offline review-app tests passed; JavaScript syntax and
whitespace checks passed. Every live cache contains exactly the 33 development
IDs. The evidence hash is unchanged. No held-out predictions were produced or
inspected, no further paid calls were made, and no revision 2 was drafted.

## Subsequent clarification

The student clarified three further Pass labels after this review. Figures
above record the earlier label set. See `hw5_revision2_preparation.md` and the
current per-version JSON reports for metrics recalculated on 17 Pass / 16 Fail.
Original metrics remain saved in `*-before-review2.json`.
