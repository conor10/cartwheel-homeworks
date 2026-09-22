# Frozen held-out test plan

The student confirmed GPT v2 and Jev v1 after development review. GPT was frozen with the course helper. The optional Jev configuration and both input/split identities are locked in `analysis/state/hw5_final_selection.json` together with current human labels. No held-out predictions have been generated or inspected.

Planned live batches: gpt-4o-mini on 33 test traces and jev-1.13.0 on the same 33 traces. Each requires paid-run approval; none has been requested from the APIs at this stage.

After approval, run from the repository root:

```bash
.venv/bin/python -m analysis.run_judges test --judge-id irrelevant_response_detail-v2 --approve-paid-run
.venv/bin/python -m analysis.run_jev test --config analysis/prompts/irrelevant_response_detail-jev-v1.json --approve-paid-run
```

Resume with the same commands after interruption. Existing GPT predictions and successful Jev responses are reused; do not register, split or freeze again. Test metrics are saved under `analysis/report/test-*.json`. Do not revise prompts based on held-out results.

Offline validation: 29 review/evaluation tests passed, including approval gates, frozen identity checks, distinct test cache identity and cached-response resume behavior. No new model calls were made during preparation.

## Execution completed

Both planned batches were subsequently approved and completed. See [held-out results](hw5_test_comparison.md).
