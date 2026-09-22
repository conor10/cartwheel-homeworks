# Final development revision comparison

Both approved live batches completed: gpt-4o-mini and jev-1.13.0, 33 development traces each. The same saved inputs and corrected human labels were used. No labels or split assignments were changed.

Pass is positive. TPR measures agreement with human Pass; TNR measures detection of human Fail. Intervals below are 95% Wilson.

| Judge | TP | FN | TN | FP | TPR (95% CI) | TNR (95% CI) |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| GPT v0 | 13 | 4 | 8 | 8 | 76.5% (52.7%–90.5%) | 50.0% (28.0%–72.0%) |
| GPT v1 | 12 | 5 | 8 | 8 | 70.6% (46.9%–86.7%) | 50.0% (28.0%–72.0%) |
| GPT v2 | 16 | 1 | 7 | 9 | 94.1% (73.0%–99.0%) | 43.8% (23.1%–66.8%) |
| Jev v0 | 17 | 0 | 4 | 12 | 100.0% (81.6%–100.0%) | 25.0% (10.2%–49.5%) |
| Jev v1 | 17 | 0 | 10 | 6 | 100.0% (81.6%–100.0%) | 62.5% (38.6%–81.5%) |
| Jev v2 | 17 | 0 | 4 | 12 | 100.0% (81.6%–100.0%) | 25.0% (10.2%–49.5%) |

GPT v2 reduces false alarms to 1/17, but misses 9/16 failures. GPT v0 detects one additional failure, at the cost of four false alarms. GPT v1 has the same failure detection as v0 and more false alarms. Jev v1 is the strongest observed Jev version, detecting 10/16 failures with no false alarms; Jev v2 detects only 4/16. These are development estimates with wide uncertainty, not held-out performance.

There is no unambiguous GPT winner across both rates. Provisionally prefer GPT v2 if avoiding false alarms matters most, or v0 if detecting failures matters more. Prefer Jev v1 for the optional comparison. The student makes the final choice. No version has been frozen in this step.

The latest versions disagree with human labels on 14 distinct traces (GPT: 10; Jev: 12). The HW5 Development disagreements filter shows these automatically; earlier assessments are preserved. Review the latest decisions as needed to choose final versions. No further prompt revisions are permitted: v2 is the second revision.

Next: choose and freeze the required GPT judge, then approve its held-out test batch separately. Jev remains an optional comparison; its current runner only supports development. Test predictions remain untouched.

Validation: both processes exited successfully, 33 predictions per new run, confusion counts checked against 17 Pass / 16 Fail, saved input hash unchanged, and no GPT test predictions present. No runtime code changed; no additional model calls beyond the approved batches were made.

## Final human review

These figures predate the final label corrections. See [final development review](hw5_final_development_review.md) for the current metrics and recommendation.
