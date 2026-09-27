# HW6 Part A case proposal

These 10 cases are grounded in reviewed Homework 4 conversations and the deterministic course seed. They are drafts for student review. All are unclassified: five observed baseline trials must determine `kind` and any `baseline_pass_rate`.

| IDs | Failure mode | Count | Evidence/check method |
| --- | --- | ---: | --- |
| e-001–e-005 | `irrelevant_response_detail` | 5 | Frozen accepted HW5 GPT v2 judge; each expects Pass on a concise order-status answer. |
| e-006–e-007 | `account_change_not_escalated` | 2 | Exact `escalate_to_human` call check. |
| e-008–e-010 | `unresolved_data_not_escalated` | 3 | Seeded damaged records; exact `escalate_to_human` call check. |

The response-detail cases come from reviewed order-status examples where unnecessary detail was labelled present. The other cases use the account-change and data-quality behaviors already reviewed in HW4. No case has a `kind` or `baseline_pass_rate` yet.

The semantic response-detail check uses the frozen judge accepted in HW5 (`irrelevant_response_detail-v2`, gpt-4o-mini). Its held-out TPR/TNR were 46.2%/55.0%; therefore those five cases rely on a weak judge and may be noisy. The exact tool-call cases do not use a judge.

## Baseline run estimate

The selected agent model is `gpt-5.5`, matching the model recorded in the HW4 traces and `.env`. Five runs per case require **50 agent runs**, plus **25 judge calls** across the five response-detail cases. No runs have been started.

Harbor 0.23.0 is installed. Docker is installed, but its daemon is not reachable yet; start Docker before the first baseline as described in the HW6 handout. The agent and judge API keys remain local in `.env`; no values are shown here.

Source case records are in `eval_cases/cases.jsonl`. The student should review whether these prompts and expected behaviors are appropriate before baseline execution.
