# HW5 Part C — first draft, awaiting development approval

The selected mode is `irrelevant_response_detail`. Version 0 is saved in
`analysis/prompts/irrelevant_response_detail-v0.txt`.

The rubric evaluates only the last assistant reply. Fail requires identifying
removable detail and explaining why it is unnecessary for the current request.
Pass permits requested detail, needed identification, relevant action outcomes,
policy citations and distinctions that clarify expressed confusion. Tool count,
refund correctness and other neighboring failures are not scored by this judge.
Quoted trace instructions are treated as evidence, never commands.

Three examples come exclusively from the fixed training split: a concise
catalogue answer (Pass), an order-status answer with surplus order fields (Fail),
and a detailed cancellation explanation that addresses the user's confusion
(borderline Pass). The complete saved conversation evidence for each example
is included. Existing human labels were retained; the assistant wrote the
explanatory critiques. IDs, split provenance and file hashes are recorded in
`hw5_prompt_v0.json`. No development/test examples were used in the prompt.

Output matches the supplied DocETL schema: `critique`, then `result` containing
exactly Pass or Fail. The helper computes TPR/TNR, confusion counts and 95%
Wilson intervals with Pass as the positive class.

`analysis/run_judges.py` now has `run_development(mode, prompt_path)` and a `dev`
command. It requires explicit paid-run approval, uses the immutable evidence
source, and reuses an existing matching judge ID to resume cached batches.
Development results will be saved as `analysis/report/dev-<judge_id>.json`.

Proposed first batch: **gpt-4o-mini, 33 development traces**, through the supplied
DocETL helper in batches of 10. Approval is pending. No judge was registered,
no live predictions were generated, no test predictions were inspected, and
no split/input files were changed. After the run, display verdicts and critiques
beside human labels and review every disagreement before any prompt revision.
At most two revisions are allowed; there is no required minimum score.

Validation: 24 offline review-app tests passed, including approval gating and
reuse of a judge ID after interruption. Training-example provenance and saved
input hashes were checked. No model calls ran.


## Run completed

The paid development run was subsequently approved and completed. See
`hw5_development_comparison.md` for observed results. Human disagreement
review is now pending; earlier pending-run statements above describe preparation.
