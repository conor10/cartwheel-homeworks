# Final allowed revision — prepared, not run

The student clarified that “Response is fine” means the support agent's reply
is acceptable. Accordingly support-0064, support-0211 and support-0035 are now
Pass. Label changes are append-only; earlier judgments and assessment history
are preserved. Revision-1 assessment selections for these cases were reconciled
with that explicit clarification. No judgments for other traces were changed.

Current development labels: 17 Pass and 16 Fail across the same 33 traces.
Metrics recalculated from the saved predictions are:

| Judge | TP | FN | TN | FP | TPR | TNR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT v0 | 13 | 4 | 8 | 8 | 76.5% | 50.0% |
| GPT v1 | 12 | 5 | 8 | 8 | 70.6% | 50.0% |
| Jev v0 | 17 | 0 | 4 | 12 | 100% | 25.0% |
| Jev v1 | 17 | 0 | 10 | 6 | 100% | 62.5% |

Current JSON reports include 95% Wilson intervals. Pre-correction metrics were
preserved as `*-before-review2.json`; changes in these statistics are label
reconciliation, not evidence of model improvement. The metrics were also
cross-checked directly against the saved GPT predictions with Pass=1.

Version 2 replaces the previous relevance-check section with a clearer decision
procedure. It explicitly protects useful identifiers/dates, concise policy and
action confirmations, and requests for missing information; it distinguishes
those from order inventories, historical dumps and needless calculation/policy
granularity. The original training examples and output section are unchanged.
No development conversation or identifier was added to the prompt.

Drafts:
- `analysis/prompts/irrelevant_response_detail-v2.txt`
- `analysis/prompts/irrelevant_response_detail-jev-v2.json`

This is revision 2, the final revision permitted by the homework. The next
proposed batches are gpt-4o-mini and jev-1.13.0, 33 development traces each.
They require approval and have not run. After comparing all versions, the
student chooses the final judge before freezing/testing. No test predictions
were inspected, no split was changed and no new model calls occurred here.

Offline checks: input hash unchanged, training-example IDs remain in training,
example/output sections unchanged, Jev configuration validates for 33 development
traces, and whitespace validation passes.

## Subsequent execution

The student approved both batches and they completed. See [revision 2 comparison](hw5_revision2_comparison.md) for results and next steps. The preparation status above is historical.
