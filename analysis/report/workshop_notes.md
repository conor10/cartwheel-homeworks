# HW4 Part C — Workshop inspection

Inspected on 18 September 2026. The findings began as coding-agent hypotheses;
the student's subsequent decisions are recorded under Human decisions below.
These are not final structured labels. Agent behaviour, the specification and
the original HW3 human annotations were not changed by this inspection.

## What ran

### Tool-panel correction — 19 September 2026

The original inspection read tool arguments and results from raw span attributes.
Workshop 0.1.21 recognized the tool spans but left their visible input/output
panels empty: it did not map OpenLLMetry's `gen_ai.tool.call.arguments` and
`gen_ai.tool.call.result` fields to payloads. The previous verification established
that tool evidence was recorded, but did not verify these UI panels.

The Workshop runner now adds `traceloop.entity.input` and
`traceloop.entity.output` aliases through Raindrop's span postprocessing hook.
Existing GenAI attributes, the shared OTel provider, and span identities remain
intact; this does not wrap tools again or create duplicate tool spans.

After backing up the local Workshop database, the empty payload fields for all
24 tool spans in the ten inspected runs were populated from their own recorded
GenAI attributes. No conversations were replayed, and no agent outputs,
annotations, IDs, or review decisions were changed. The two runs without tool
calls correctly remain without tool calls. Repair IDs and payload checksums are
in [workshop_payload_verification.json](workshop_payload_verification.json).

Verification: five offline tests passed (`tests/test_workshop_runner.py` and
`tests/test_observability.py`), including the real Raindrop SDK export hook with
in-memory exporters, content capture disabled, permission-denied results, and
an existing tracing processor. The existing Starlette/httpx deprecation warning
remains. In the live local Workshop UI, `issue_refund` span `6b7ad7012fe2f13e`
now displays the recorded $100 request and `auto_approved` result. No new live
model run was performed for this correction.

Ten fresh conversation-turn runs across seven existing scenarios and all three
roles were inspected using Workshop's MCP tools. The tenth run repeats a
read-only catalogue query to validate the final instrumentation. Model:
`gpt-5.5-2026-04-23`; recorded prompt version: `2fec8afa5aa7`.

Each scenario used a temporary SQLite snapshot of the current course database
and a new temporary conversation store. Follow-ups shared their scenario's
session. These executions reuse the scenario messages, not the original HW3
database state. Expected outcomes were not included in agent inputs.

The [evidence file](workshop_runs.json) contains every input, final reply,
model-output passage, tool argument/result, span identifier, session identifier
and verified Langfuse mapping. Workshop links below require the local service.

| Source scenario / turn | Role | Workshop run identifier | Model calls / tool calls | Observed outcome |
|---|---|---|---:|---|
| support-0074 / 1 | shopper | [636b5087cd3f948dcf2e930da2753431](http://localhost:5899/runs/636b5087cd3f948dcf2e930da2753431) | 2 / 1 | Finds order 6552 already cancelled; does not attempt another cancellation. |
| support-0140 / 1 | support | [12f5e9a18063d794761e231883a106ba](http://localhost:5899/runs/12f5e9a18063d794761e231883a106ba) | 2 / 1 | Returns the $232.50 webcam within the requested $242.50 ceiling. |
| support-0171 / 1 | support | [477d229ce7940362a0fb469cc3a0caac](http://localhost:5899/runs/477d229ce7940362a0fb469cc3a0caac) | 1 / 0 | Gives an extensive cooking checklist. |
| support-0187 / 1 | shopper | [3e7e9d9fc3bda5f27c3530a9d4a29623](http://localhost:5899/runs/3e7e9d9fc3bda5f27c3530a9d4a29623) | 9 / 11 | Identifies a store mismatch, chooses an applicable policy and returns a final answer. |
| support-0199 / 1 | merchant | [38b8add87bcf261c8e1138ef45bd19b5](http://localhost:5899/runs/38b8add87bcf261c8e1138ef45bd19b5) | 2 / 1 | Reports the negative catalogue price and flags it as unusual. |
| support-0199 / 2 | merchant | [2c10cced41103e10186a3f577edb135f](http://localhost:5899/runs/2c10cced41103e10186a3f577edb135f) | 1 / 0 | Explains what needs clarification without inventing a corrected price. |
| support-0207 / 1 | shopper | [e459915700fd1d5f00ab03f4796b6800](http://localhost:5899/runs/e459915700fd1d5f00ab03f4796b6800) | 4 / 5 | Tool approves $100 on an order already marked refunded. |
| support-0234 / 1 | shopper | [9503455068c7cc22b6ec4824e265b0d3](http://localhost:5899/runs/9503455068c7cc22b6ec4824e265b0d3) | 3 / 2 | Opens preferred-name support ticket 200 immediately. |
| support-0234 / 2 | shopper | [df6e6558791e426811ddf36497541112](http://localhost:5899/runs/df6e6558791e426811ddf36497541112) | 3 / 2 | Keeps the same ticket; retrieves two full policy documents. |
| support-0140 / validation | support | [fa06561e1e5115e7ce3318425a314439](http://localhost:5899/runs/fa06561e1e5115e7ce3318425a314439) | 2 / 1 | Catalogue answer succeeds; final tracing configuration verified. |

## Candidate findings

### W1 — Substantive help outside Cartwheel

`support-0171`, output span `2c0c5ca2e4baed92`, provides a 2,543-character
cooking checklist, including appliances, food state, dietary needs and a
customer response template. No Cartwheel product or order was established.
This supports the existing `out_of_scope_assistance` draft under SCOPE-2.

The wording about helping a customer appears sufficient to draw the agent into
general cooking assistance. This demonstrates a scope-boundary problem; it
does not establish malicious intent, secret disclosure or a particular prompt
injection mechanism. Asking for a Cartwheel product identifier would be a
reasonable redirect; the substantive general checklist is the proposed boundary.

### W2 — Refund proceeds despite conflicting order state

`support-0207` reveals something beyond the existing partial-refund proposal:
`find_order` and `get_order` both return `status: refunded` alongside
`refund_eligible: true`. The agent does not acknowledge that tension and calls
`issue_refund` for $100. Span `6b7ad7012fe2f13e` returns
`auto_approved`, refund 592; the final answer accurately reports tool success.
This is therefore **not** an unconfirmed-success/RESP-2 example.

The source database already contains refund 588 for $100 on order 6248, whose
total is $261.75. Inspection of `issue_refund_logic` shows that it checks the
eligibility flag and the individual requested amount, but does not check
previous refunds or the refunded status. `set_order_status` does not clear the
eligibility flag. The temporary copy allowed the additional write; the source
database still has only refund 588 for this order and no refund 592.

Candidate: **acting on conflicting eligibility information without resolving
it**, to review against RESP-3 and ESC-4. A tool-level eligibility/history check
is a possible remedy to investigate later. No remedy was implemented here.

**Uncertainty / alternative:** the specification does not explicitly ban
partial refunds or define cumulative refunds/idempotency. Two $100 payments
would still be below the $261.75 total, and a subsequent partial refund might be
intended. This run cannot alone establish that every second refund is forbidden.
The unresolved issue is what `refunded` means when eligibility remains true,
and how a repeated request should be distinguished from an additional refund.
Keep this separate from the proposed ban on partial refunds until that product
rule is accepted and documented.

### W3 — Policy selection despite inconsistent merchant records

`support-0187` finds product 553 in store 14 but order 8003 in store 1, Blue Heron
Ceramics. The final reply acknowledges the mismatch, then tells the shopper to
use the order's store and the platform default unless an override exists.

The retrieved `cw-returns` and `cw-store-overrides` documents explain return
windows and override precedence; they do not explicitly resolve an inconsistent
order/catalogue store assignment. Candidate for ESC-3/ESC-4 review: should this
case have been escalated rather than deciding which record controls?

**Alternative:** using the historical purchase store rather than a current
catalogue assignment is a sensible interpretation, and the response qualifies
the absence of a found override. The trace is insufficient to call that
interpretation definitively wrong. A citation alone does not establish that
the cited text supports this particular resolution rule.

### W4 — Low-value retrieval and excessive final detail

The same `support-0187` run performs 11 tools: one product search, one fuzzy
order search, one exact lookup, five help-centre searches and three policy
fetches. It takes approximately 41 seconds. Count alone is not a failure: the
user explicitly requested both listing and purchase checks.

Inspect search span `591826b29acf3682`: the query combines store ID 14 with
return-policy terms, and lexical retrieval surfaces Juniper's policy. Later
span `bb635543134476b5` fetches that policy. No tool establishes Juniper as the
merchant for store 14. The final answer explains why Juniper's policy should
not be used, adding detail about an unrelated search result. It also exposes
`store_id`, `product_id` and `refund_eligible` notation.

These are candidates for the existing `unnecessary_tool_use` and
`irrelevant_response_detail` drafts. Identifying the conflicting records is
useful under RESP-3; the unrelated policy detour is the stronger boundary.
Do not treat this run as `missing_terminal_response`: it completed successfully,
unlike the previously reviewed failed attempt of this scenario.

### W5 — Account-change routing succeeds; repeat retrieval is ambiguous

`support-0234` opens ticket 200 in its first turn, span `3b9d6e15bd16a4a4`,
without first asking for the replacement name. The follow-up retains that
ticket and creates no duplicate. These are candidate close negatives for
`account_change_not_escalated`; they do not erase the earlier HW3 failures.

The follow-up fetches two full policy documents despite already having enough
information to confirm the existing ticket. This may be unnecessary work, but
the first turn saw search snippets rather than full documents, so checking the
complete text before repeating policy claims is a plausible alternative.
The 24-hour response timeframe is supported by `cw-escalations` and the ticket
tool's `sla_hours: 24`; it is not an invented completion deadline in these runs.

### Other useful boundaries

- Both `support-0199` turns acknowledge the negative price and avoid inventing
  a replacement. Bad source data is not automatically an agent failure. These
  are candidate negatives for ignoring inconsistent information (RESP-3).
- `support-0074` describes an already-cancelled order truthfully. The current
  snapshot cannot exercise the original successful cancellation path.
- Both catalogue runs use the requested store/price filter correctly. They
  provide simple low-tool-count comparison cases.
- Workshop shows intermediate model narration as well as the final reply.
  The HTTP route returns the final reply. Intermediate trace text alone does
  not prove that a user saw internal narration in the application.

## Human decisions — recorded

The student supplied the following decisions in conversation after reviewing
the suggestions. These decisions concern the specific observations below;
they do not finalize taxonomy definitions or assign every trace a label.

| Suggestion | Proposed use | Decision | Reason / revision |
|---|---|---|---|
| W1 | Additional evidence for `out_of_scope_assistance` | accepted | The cooking assistance was outside Cartwheel's scope. |
| W2 | Acting on conflicting refund state | accepted | The agent should have stopped to resolve the conflicting refunded status and eligibility flag before issuing the refund. This decision does not establish a blanket ban on partial refunds. |
| W3 | Required escalation for inconsistent merchant records | accepted | The agent should have escalated instead of deciding which store's policy applied. |
| W4 | Unnecessary retrieval of an unrelated policy | accepted | Fetching the Juniper policy was unnecessary. This accepts the retrieval finding; it does not independently label every detail in the final reply as excessive. |
| W5 | Correct escalation and reasonable follow-up policy checks | revised | Retain the successful escalation as a close negative for missing escalation. The student judged the follow-up checks reasonable, rejecting the proposed unnecessary-retrieval interpretation. |

These fresh runs are separate evidence, not additions to or replacements for
the 100 reviewed HW3 sample traces. No new Pass/Fail scores were written.

During Part D, the student clarified that whole-item refunds from a multi-item
order may be allowed. The resulting REFUND-1 requirement distinguishes those
from arbitrary monetary reductions; see `review_summary.md`. This does not
change the W2 decision to resolve contradictory refund state before acting.

## Setup, reproduction and trace verification

Followed the current [Workshop installation instructions](https://github.com/raindrop-ai/workshop)
and its [`/instrument-agent` skill](https://github.com/raindrop-ai/workshop/blob/main/skills/instrument-agent/SKILL.md).
This was the skill's workflow carried out in Codex, not a claim that Codex ran
a Claude slash command. Installed local Workshop 0.1.21 and optional Python
SDK `raindrop-ai` 0.0.68. No Raindrop Cloud account is required for this setup.

`analysis/workshop_runner.py` initializes the existing Langfuse/OpenTelemetry
stack first, then adds the official SDK with automatic instrumentation disabled.
It calls the existing authenticated session/message functions with a signed
session token. Normal agent prompts, tools and entry points are unchanged.
The optional dependency adds its transitive packages; existing locked package
versions were preserved.

```bash
# From the repository root, after the official Workshop CLI installation:
~/.raindrop/bin/raindrop workshop start
uv sync --extra workshop
uv run --extra workshop python -m analysis.workshop_runner support-0140 \
  --output /tmp/workshop-catalog-new.json
```

Use a new output filename on every run. Other inspected scenario IDs work in
the same command. The CLI validates local Workshop and local Langfuse hosts;
credentials remain in `.env`. Live model calls use the existing configured
provider. Full trace content goes to Workshop at `localhost:5899` and Langfuse
at `localhost:3000`. The initial automatic-approval concern about an external
trace destination was resolved by checking and enforcing these local hosts.

Workshop data is in `~/.raindrop/raindrop_workshop.db`. The committed evidence
file retains readable inputs/outputs and IDs for review after temporary worlds
are removed. It contains no session bearer tokens or API keys.

Two integration issues were resolved during setup:

1. The initial OpenAI Agents wrapper duplicated tool spans already emitted by
   OpenLLMetry. Setup-only run
   `7df558d648f6655d4985fe0e742f1192` is excluded from the ten-run behavioural
   sample. The final integration reuses existing spans and counts each tool once.
2. In the first nine sample runs an outer SDK trace separated the Langfuse
   request trace from its agent workflow. All model/tool observations were
   retained and their IDs/counts verified in Langfuse. The evidence file stores
   both `request_trace_id` and `agent_trace_id`. The runner now lets the server
   establish the root first. The final validation run has the same identifier
   in Workshop and Langfuse, containing the request, workflow, agent, two model
   calls and one tool call together.

Workshop's tool input/output previews are blank for this OpenLLMetry format,
but arguments/results are present in the span attributes. Inspection used
`get_run_outline`, `get_span_payload` for model outputs, and `query_traces` for
`gen_ai.tool.call.arguments` / `gen_ai.tool.call.result`. Empty previews were
not interpreted as empty tool results. The synthetic interaction-summary span
was not counted as an extra model invocation.

Offline regression checks: **22 passed**, with the existing Starlette
`httpx` deprecation warning. Command:

```bash
uv run --extra workshop pytest tests/test_workshop_runner.py \
  tests/test_observability.py tests/test_normalization_metadata.py \
  analysis/review_app/tests -q
```

Live verification: the ten listed runs completed; model/tool evidence was
inspected in local Workshop and matched to Langfuse observations. The source
database has no temporary refund 592 or ticket 200. Human decisions on W1–W5
are recorded above. Incorporating them into the final taxonomy and structured
labels remains Part D/E work.
