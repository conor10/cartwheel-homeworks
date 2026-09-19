# HW4 review summary — work in progress

## Sample and human review

Live collection: 322 HW3 traces in 251 sessions. Selected sample: 100 distinct traces,
all reviewed. Batches: 15 initial random, 15 cluster representatives, 30 distributed
across intent, 25 depth-search selections, and 15 final uniform selections.
Role composition: 73 shopper, 15 support, 12 merchant traces.
Open reviews: 50 first-failure and 50 no-failure-observed outcomes. These are open
coding outcomes, not per-mode labels or population prevalence estimates.
The state contains 98 original notes and six suggestion-linked notes (five accepted and one revised rejection), plus 102 reviewed traces in total; the two
additional reviewed traces do not increase the selected sample count.

## Taxonomy revision and requirement provenance

Revision 2 merges unnecessary process explanation into irrelevant response detail:
one customer-facing relevance rule addresses both. Original notes and version 1
proposals remain available. Separate account-change routing from unresolved-record
routing because one needs unconditional account-intent routing and the other needs
record-quality detection and resolution. Terminal execution failure remains distinct
from inefficient tool use because fixing one does not necessarily fix the other.

The student's whole-item clarification replaces the overly broad partial-refund
category with `arbitrary_amount_refund_accepted`. A monetary reduction is not the
same as refunding the full paid value of selected whole items.

SPEC.md additions record intended behaviour, not runtime changes:

| Requirement | Motivation |
|---|---|
| RESP-6, relevant concise replies | Human notes `dcb58ac0-9a92-491f-a89b-42bcaf219a46`, `9e46edfc-428c-49c1-91f0-281593da43fc` (support-0084), `b7d534ac-7447-42c1-8319-44f03c1d10d0` (support-0243), and internal-process notes retained in the merged mode. |
| EFF-1, purposeful tool calls | Human note `da06a131-3a60-4174-8b55-c48e1122f26e`, accepted Workshop W4, and W5's explicit reasonable-verification boundary. |
| ESC-5, unresolved record escalation | Human notes `9376dadf-8f64-42d1-bf71-d68e3b6b2d2a` and `4857a025-3263-4212-a654-788f66107920`; accepted Workshop W2/W3. |
| RESP-7, truthful terminal response | Human note `32000e11-fd83-4384-993b-9822154b1f39`, original support-0187 MaxTurnsExceeded with no final reply. |
| REFUND-1, full order or whole items | Human notes `f0b8acea-8cc3-4449-a94a-4a259f759455`, `b8f785a3-49a1-4874-b708-2796a5eadb07`, `28ce8d65-a9bf-4d5f-9395-dacd52d8f9ea`; student explicitly clarified “Whole-item refunds may also be allowed.” |

Retain required policy citations despite some notes preferring links: a verified
linked identifier can work, but deleting citations would contradict RESP-1. No
invented order or policy URLs are required. Historical monetary-partial results
must be identified as examples under the revised product rule, not falsely called
violations of the earlier specification.

## Search and required human decisions

A two-pass unnecessary-tool-use search screened all 322 live traces, including
reviewed and unreviewed records. The first pass retrieved 65 broad candidates.
The second pass rechecked purposes and session context under the refined rule;
full-document verification and genuine store-override checks can be legitimate.
The search record is `tool_use_search.json`, with precise span evidence and an
audit entry for every trace. It is retrieval evidence, never automatic labels.
All seven cards have human decisions retained with history in `part_d_decisions.json`.
The original support-0187 tool-use suggestion remains rejected: the reviewer
identified failed escalation of inconsistent merchant data as the underlying issue.
The reviewer clarified on 19 September that support-0098 has reasonable tool calls
and excessive response detail, while support-0246's second turn has unnecessary
tool calls. Those corrections are saved and synced; earlier decisions remain in
history. W5's reasonable verification remains a separate Workshop rejection.

## Final 15 and stability

All 15 final traces have human open reviews. The reviewer explicitly confirmed
**0 previously unseen consequential modes**: “No new modes in the final 15.”
The stability assessment is complete; no additional batch is indicated by it.
The blank-title escalation observation in support-0201 strengthens the already
noted unresolved-record theme from support-0199. Other notes repeat response-detail
and tool-use concerns. The confirmation and supporting notes are recorded in
`part_e_results.json`. This confirms taxonomy stability, not individual binary labels.

All seven definitions are final, including `out_of_scope_assistance` and
`missing_terminal_response`. The reviewer explicitly requested their inclusion
and does not want a further search for examples. Scope failure has two observed
executions of one prompt; missing terminal response has one. Both therefore
remain below the handout's three-confirmed-positive requirement. This is an
explicit evidence limitation, not grounds for excluding the findings. The
AgentDebug comparison is in `agentdebug_comparison.md`.

## Part E counts and remaining judgments

All 700 selected trace/mode pairs have evidence-backed proposals. 61 map specific
human notes or explicit clarifications and are saved as accepted binary judgments:
44 response-detail positives; four tool-use positives and one negative; two
account-escalation positives; three data-escalation positives; and five arbitrary
refund positives; one out-of-scope assistance positive; and one missing terminal
response positive. These counts overlap by trace and are not sample fractions.

The other 639 pairs remain proposed rather than saved binary labels, including 15
unresolved boundary cases. Their finalization is separate from the now-completed
stability check; the handout does not prescribe 639 additional manual reviews. Proposed negatives were inspected independently; open-review
absence was not expanded into seven automatic Pass labels. `part_e_review.md`
explains the Labeling workflow and lists the unresolved cases. `part_e_results.json`
records the exact snapshot. Live Progress counts update as judgments are confirmed.
Final sample fractions are withheld until every pair for that mode is judged.

## Verification and pending submission work

This work inspected existing live Langfuse traces; it made no fresh agent/model
calls. Original notes, review history and sample membership are preserved.
All 61 mapped human judgments synced successfully and were individually read back
from Langfuse; trace, mode, value, version and evidence matched. Zero writes were
pending at revision 264. Twenty offline review-app tests passed; an isolated browser fixture
verified missing decisions block submission and all modes save together.

Part E remains incomplete until the remaining binary judgments are accepted or
corrected. Then refresh the report's counts/fractions from the final labels.
The student reports that the video is recorded. Its contents were not independently
verified. The binary-label completion status above remains unchanged.
