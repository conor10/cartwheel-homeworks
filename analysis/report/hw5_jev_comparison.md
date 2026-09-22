# Optional Jev development comparison

Status: implemented and tested offline; paid run awaiting approval.

- Model pinned to `jev-1.13.0` (TypeSafe documentation checked 21 September 2026).
- Same 33 development IDs and immutable conversation evidence as the required
  gpt-4o-mini judge. Test evaluation is not exposed by this runner.
- One Choice question with Pass/Fail options. The original rubric and the same
  three training examples are retained; instructions requesting generated output
  are removed. This is an adapted-interface comparison, not an identical prompt
  comparison. No extra labels or confidence thresholds are introduced.
- `analysis/prompts/irrelevant_response_detail-jev-v0.json` holds the exact
  request configuration and training-example provenance.
- `analysis/run_jev.py` calls the documented HTTP API using Python's standard
  library. No additional dependency or plugin installation is needed.
- `TYPESAFE_API_KEY` is read locally from `.env`; presence was confirmed without
  printing its value. No credentials are included in request/result artifacts.

The `plan` command performs no API calls:

```sh
uv run python -m analysis.run_jev plan
```

Only after the student approves **jev-1.13.0 on 33 development traces**:

```sh
uv run python -m analysis.run_jev dev --approve-paid-run
```

Successful predictions are saved after each trace in
`analysis/state/comparisons/jev-<fingerprint>.json`. The fingerprint covers the
model, questions, exact input-file hash and development IDs. Rerunning the same
configuration resumes missing predictions; a process lock prevents simultaneous
runs. Network errors are surfaced without automatic retry or synthetic verdicts.
An interrupted request without a saved result may already have been billed.

Each prediction retains the verdict, probabilities, confidence, returned model,
usage and client-measured latency. Critique is explicitly null. Probabilities
and confidence are not substitutes for generated evidence explanations or for
measured accuracy against the human labels. Invalid responses and unexpected
model versions fail validation rather than becoming Pass/Fail labels.

Completed development metrics are saved in
`analysis/report/dev-jev-<fingerprint>.json`, with confusion counts, TPR, TNR,
95% Wilson intervals using the course helper, class counts and disagreements.
These can be compared with `dev-irrelevant_response_detail-v0.json` after the
required GPT run. Different provider interfaces and lack of Jev critiques must
be disclosed in the comparison. No GPT or Jev batch has run yet.

Validation: 26 offline review-app tests passed, including probability validation,
Pass-positive metrics, paid-run gating, caching and interrupted-run recovery.
The original split, evidence export, human labels and GPT prompt are unchanged.

References:
- https://docs.typesafe.ai/api
- https://docs.typesafe.ai/primitives/choice
- https://docs.typesafe.ai/models
- https://raw.githubusercontent.com/typesafe-ai/skills/main/skills/typesafe-ai/SKILL.md


## Run completed

The paid development run was subsequently approved and completed. See
`hw5_development_comparison.md` for observed results. Human disagreement
review is now pending; earlier pending-run statements above describe preparation.
