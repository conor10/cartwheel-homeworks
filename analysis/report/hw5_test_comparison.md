# HW5 held-out results

Both student-approved live batches completed on the same 33 held-out traces: 13 human Pass and 20 human Fail. The selected versions were frozen before either run: GPT v2 (gpt-4o-mini) and optional Jev v1 (jev-1.13.0).

| Judge | TP | FN | TN | FP | Pass recognition / TPR (95% CI) | Failure detection / TNR (95% CI) |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| GPT v2 | 6 | 7 | 11 | 9 | 46.2% (23.2%–70.9%) | 55.0% (34.2%–74.2%) |
| Jev v1 | 10 | 3 | 14 | 6 | 76.9% (49.7%–91.8%) | 70.0% (48.1%–85.5%) |

Pass is the positive class. FN means an acceptable response incorrectly flagged; FP means a missed failure. Intervals are 95% Wilson.

## Interpretation

GPT incorrectly flagged 7 of 13 acceptable responses and missed 9 of 20 failures. My recommendation is not to use this judge as an automatic acceptance gate. It could supply review suggestions, but human review remains necessary. Jev incorrectly flagged 3 acceptable responses and missed 6 failures: better observed performance on both rates, but the sample is small, intervals are wide, and this does not establish statistical superiority. Jev provides structured decisions without written critiques; GPT supplies evidence-based critiques. The student should make their own final assessment for the video.

The two allowed prompt revisions are complete. Do not revise or select new prompts using these held-out results. No additional labeling or test-disagreement review is required to complete this evaluation.

## Validation

Both live processes exited successfully. Predictions cover all 33 test IDs per model. Confusion counts were independently checked against cached predictions; Jev rates and intervals were recalculated, and GPT metrics were reproduced with the course helper. Frozen file checks confirm unchanged prompts, labels, split assignment and input evidence. Prior preparation passed 29 offline tests.

## Remaining submission steps

Record the video (up to five minutes), covering the failure mode, one development disagreement and the response to it, test TPR/TNR with uncertainty, and your own decision about using the judge. Recalculate the required GPT metrics live from saved predictions with this offline command; it makes no model calls:

```bash
.venv/bin/python -c 'import json; from analysis.helpers import judge_alignment; print(json.dumps(judge_alignment("irrelevant_response_detail-v2", "test"), indent=2))'
```

Commit the HW5 work when ready. No commit or push was made as part of this test run.
