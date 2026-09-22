# HW5 Part B — prepared inputs and fixed split

The 90 saved human judgments contain 39 Pass and 51 Fail labels. The final
close-variant review excludes eight additional records from evaluation, leaving
**82 eligible conversations: 32 Pass and 50 Fail**. All 90 human judgments and
their evidence remain intact. The HW5 UI still shows the full review collection;
the evaluation uses the eligible subset.

The excluded cases repeat general account-security, return-date and
store-override questions, or catalogue requests with entity/price substitutions.
One representative per group was selected by lowest scenario ID, without using
the label. The exact exclusions and rationale are in
`analysis/state/hw5_input_manifest.json`. Shared intents alone are not treated
as duplicates: distinct recorded states, required decisions and authorization
boundaries remain eligible.

| Split | Pass | Fail | Total |
| --- | ---: | ---: | ---: |
| Training | 6 | 10 | 16 |
| Development | 13 | 20 | 33 |
| Test | 13 | 20 | 33 |
| Total | 32 | 50 | 82 |

`analysis/run_judges.py` implements `prepare_inputs()` and `split_data(mode)`.
The supplied `split_labels` helper created the assignment using 20/40/40,
seed 7 and minimum 10 per class in development/test. Integer rounding accounts
for the exact counts. Unrelated existing splits were preserved. Re-running
preparation verifies and reuses the existing inputs and split, rather than
reshuffling or overwriting inputs.

`analysis/state/hw5_trace_inputs.json` contains one record per eligible
conversation, retaining the original target trace ID. Each message list ends
with the reply to evaluate. It includes earlier user/final-assistant turns,
all observed tool arguments and results through that reply, and retrieved
policy text. Later turns, model-only narration, repeated model request history,
system prompts, labels, scores, reviewer notes and scenario metadata are omitted.
Tool payloads retain the original application data; the exclusion concerns
review/trace metadata, not facts needed to judge the response.

The input SHA-256 is
`0d439e18f63330f62dc8e828923001c6e10cb222a144d98d22713a7892097bcb`.
Keep these inputs unchanged for every judge version. The preparation functions
set `CARTWHEEL_JUDGE_TRACE_SOURCE` within their process. When invoking helpers
from another shell/process, set it explicitly:

```sh
export CARTWHEEL_JUDGE_TRACE_SOURCE="$PWD/analysis/state/hw5_trace_inputs.json"
```

Validation: 23 offline review-app tests passed. Tests cover preservation of
prior context and tool/policy evidence, omission of metadata and future turns,
immutable inputs, split reuse and preservation of unrelated split records.
The real export was checked for its allowlisted structure, 82 unique records,
and byte-for-byte stability on rerun. No live model calls or predictions ran.

Next: Part C drafts the judge using training examples only. Development and
test examples must not be inserted into the prompt. Before a paid development
batch, show the student the model (`gpt-4o-mini`) and trace count (33), and wait
for approval. Do not inspect test predictions before the final judge is frozen.
