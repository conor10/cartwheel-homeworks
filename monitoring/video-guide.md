# HW7 video guide — files to show in order

Aim for 4½ minutes. Open these files and the two linked browser pages before recording. Use saved results: no new agent or judge runs are needed. Paths below are relative to the repository root.

| Stage | Files to open | What to show |
| --- | --- | --- |
| A — comparable periods | `monitoring/config.json`; `scenarios/monitoring_scenarios.jsonl`; `scenarios/hw7-after-results.jsonl` | Model, date windows, shared inputs and recorded new outputs |
| B — sampling | `monitoring/sample.py` | Random selection, chosen risk group and deduplication |
| C — estimates | `monitoring/prevalence.svg`; results table below | Raw rate, corrected rate, interval and threshold |
| D — scores and dashboard | `monitoring/write_scores.py`; Langfuse dashboard | Separate random/risk scores and actual published results |
| D — automation | `.github/workflows/monitor.yml`; successful GitHub run | Schedule, monitoring command, artifact upload and proof it ran |
| E — interpretation | `monitoring/README.md` | Conclusions and action after a threshold crossing |

## 1. Part A — inputs and periods (0:00–0:45)

**Open [monitoring/config.json](config.json).** Show the top fields and `periods`: the judge, failure mode, Cartwheel model, and before/after dates. Point out `not_judgeable` for original `support-0187`.

**Briefly open [scenarios/monitoring_scenarios.jsonl](../scenarios/monitoring_scenarios.jsonl), then [scenarios/hw7-after-results.jsonl](../scenarios/hw7-after-results.jsonl).** Search for `support-0077` in each to show a shared scenario and its recorded new result. You need not read the long JSON records aloud.

Explain in your own words:

- We compare the original 15 September run with one new run on 28 September, using the same 50 scenarios and Cartwheel model, `gpt-5.5-2026-04-23`.
- Each period has 74 turn-level traces grouped into 50 conversations. All 50 new scenario runs completed.
- Original `support-0187` ended without a final reply. We retained it in the population but marked it not judgeable, without substituting a retry. This is a disclosed limitation.

## 2. Part B — sample selection (0:45–1:25)

**Open [monitoring/sample.py](sample.py), lines 51–75.** Search for `sampled =` and keep `DEFAULT_RISK_GROUPS` visible below it.

Point to three pieces:

1. `random.Random(seed).sample(...)`: uniform random selection. The configured 20% selects ten of the 50 conversations, using seed 7.
2. `policy_lookup`: selects conversations containing `get_policy` or `search_help_center`. We chose this group because policy explanations may contain unnecessary detail.
3. `unique`: combines the selections so a conversation in both groups is judged once.

Only the random sample estimates the overall rate. The risk group supplies extra examples to inspect. Before has ten random selections but only nine judgeable responses; after has ten judgeable responses.

Supporting implementation, if needed: [monitoring/run.py](run.py), search `evaluate_plan`, shows the judge call and the separate saved random/risk verdicts. You do not need another code walkthrough during the recording.

## 3. Part C — saved estimates (1:25–2:15)

**Open [monitoring/prevalence.svg](prevalence.svg) as an image preview.** Show both corrected estimates, the interval bars and the 15% threshold. Then show this table in the guide's Markdown preview for the raw rates:

| Period | Random flags / judged | Raw flag rate | Corrected estimate | 95% interval |
| --- | ---: | ---: | ---: | ---: |
| Before | 3 / 9 | 33.3% | 0% | 0–100% |
| After | 5 / 10 | 50.0% | 0% | 0–100% |

The table presents the saved values in [monitoring/history.jsonl](history.jsonl). Its first record is before and second is after. There is no need to scroll through all the verdict IDs in that file during the video.

Explain that the raw rate rose, but the correction is unstable because the frozen judge barely discriminates between failures and passes. The corrected zeros are clamped estimates, not proof of zero failures. Both intervals cover the whole range, so we cannot conclude improvement, deterioration or stability. Missing-response bias is an additional limitation.

If you want to show the calculation code, open [monitoring/correct.py](correct.py), search `corrected_mode_prevalence`. In [monitoring/run.py](run.py), search `estimate = corrected_mode_prevalence` to show that only `random_verdicts` enter the calculation.

## 4. Part D — scores and dashboard (2:15–3:05)

**Open [monitoring/write_scores.py](write_scores.py), lines 74–83.** Search for `for kind, verdicts`. Point out the separate `verdict` and `risk_verdict` scores and `_stable_id`: rerunning updates the same scores rather than adding duplicates.

**Switch to the [Langfuse dashboard](http://localhost:3000/project/cartwheel-dev/dashboards/cmuljpqwn0004mp07hht8u10o?dateRange=7d).** Choose a date window including 28 September 2026. Show:

- Random sample flag rate.
- Risk sample flag rate.
- Traces flagged by either sample.

The dashboard is required visual evidence; the Python file alone does not show that scores reached Langfuse. It plots score creation time and includes the daily verification scores. Use the SVG for the historical before/after comparison. A flagged-trace count of two means both sample memberships flagged it, not two independent failures.

Optional example if time allows: [support-0077](http://localhost:3000/project/cartwheel-dev/traces/2e818a7aeda6cbb37befc729f73fd81d). This risk-only flag concerns an already-cancelled order whose reply adds policy explanation and repeats that no action was taken. It is a candidate for inspection, not a newly confirmed failure. Risk sampling added six flagged candidates before and three after outside the random samples.

## 5. Part D — automation and proof it ran (3:05–3:50)

**Open [.github/workflows/monitor.yml](../.github/workflows/monitor.yml).** Show `schedule` and `workflow_dispatch` at the top. Then search `Run previous 24 hours` and show that step plus `Upload monitoring evidence` below it. The upload uses `if: always()` so evidence is retained even after a failed job.

**Switch to [successful GitHub run 36468869767](https://github.com/conor10/cartwheel-homeworks/actions/runs/36468869767).** Open the `monitor` job and its `Run previous 24 hours` step. Show the successful result and the `hw7-monitor-36468869767` artifact on the run summary.

Explain:

- This was a successful manual invocation of the workflow that defines the daily schedule, not a cron-triggered run.
- It processed 50 conversations grouped by session, reused 25 verdicts, made four new judge evaluations, and verified 36 scores.
- Recurring execution is disabled to avoid ongoing costs. There are no push/PR triggers, and the temporary local runner was removed.

Saved verification details are also in [monitoring/config.json](config.json), under `workflow_verification`. This daily verification is separate from the two-period comparison.

## 6. Part E — interpretation and action (3:50–4:30)

**Open [monitoring/README.md](README.md).** Briefly show the four question headings, then focus on question 4, “What should happen if the estimate crosses the threshold?”

Explain that a corrected rate above 15% starts human error analysis. Inspect flagged requests, replies and tool evidence, confirm real failures, then add them to the HW6 regression suite and test any fix.

Neither point estimate crossed the threshold here, but the wide intervals prevent treating that as evidence everything is fine. We preserved the frozen HW5 judge; improving it would require separate validation.
