# Homework 7: monitoring interpretation

Interpretation reviewed and accepted by the student on 29 September 2026. The figures below are observed results; the flagged examples have not been confirmed as failures by a new human review.

## 1. Did the corrected failure estimate move?

No. For `irrelevant_response_detail`, the corrected estimate was **0% in both periods**. The raw judge flag rate increased from **3/9 (33.3%) before** to **5/10 (50%) after**. Both periods contain the same 50 scenarios and use `gpt-5.5-2026-04-23`; the frozen judge is `irrelevant_response_detail-v2` on `gpt-4o-mini`.

The corrected zeros are clamped estimates, not evidence that no failures occurred. The original `support-0187` conversation had no final reply. It remains in the population and random sample, marked not judgeable, with no replacement or invented verdict. This leaves 9 observed random outcomes before and 10 after.

## 2. Do the intervals support a conclusion?

No: **both 95% bootstrap intervals span 0–100%**. The judge's held-out failure sensitivity is 0.55 and pass specificity is approximately 0.4615. Their sum minus one—the correction denominator—is only about 0.01154, making the correction highly unstable. These small samples cannot establish improvement, deterioration, or stability.

The interval accounts for sampling and held-out judge uncertainty, but not possible bias from the missing response. The incomplete original conversation is a disclosed exception to the homework's complete-period requirement.

## 3. What did the risk group reveal beyond the random estimate?

The `policy_lookup` group selected conversations containing `get_policy` or `search_help_center` tool calls. It flagged **8/26 judgeable conversations before** (27 selected, one not judgeable) and **5/25 after**. Of these, **6 before and 3 after were outside the random sample**, providing additional candidates for inspection.

For example, the after-period [support-0077 trace](http://localhost:3000/project/cartwheel-dev/traces/2e818a7aeda6cbb37befc729f73fd81d) was flagged only through the risk selection. Its reply confirms that the order is already cancelled, then explains cancellation policy and reiterates that no further cancellation was submitted. This is a candidate for reviewing unnecessary detail, not a confirmed failure. Risk selections are targeted and overlapping; their flag rates must not be pooled into the prevalence estimate or interpreted as population rates.

## 4. What should happen if the estimate crosses the threshold?

A corrected estimate above the precommitted **15% threshold** should trigger human error analysis of the flagged traces. Review the request, final reply and tool evidence; distinguish actual irrelevant detail from necessary explanations and judge mistakes. Convert confirmed failures into Homework 6 regression cases, then test any proposed fix.

Neither point estimate crossed the threshold here. Given the uninformative intervals, that is not a clean bill of health. Improving and revalidating the evaluator would be a separate exercise; these monitoring results retain the frozen HW5 judge unchanged.

Evidence: [configuration](config.json), [two-period history](history.jsonl), [chart](prevalence.svg), [Langfuse dashboard](http://localhost:3000/project/cartwheel-dev/dashboards/cmuljpqwn0004mp07hht8u10o), and [successful manual GitHub verification](https://github.com/conor10/cartwheel-homeworks/actions/runs/36468869767). The daily workflow is implemented, but recurring execution remains disabled to avoid ongoing costs. Its separate 24-hour verification result is not a third period in the before/after comparison.
