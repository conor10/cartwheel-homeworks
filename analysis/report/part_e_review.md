# Part E — structured labeling

All seven definitions are final, including `out_of_scope_assistance` and `missing_terminal_response`, as explicitly requested by the reviewer. These rare modes remain below the handout’s three-positive-example requirement; that evidence limitation is documented rather than used to exclude them. No further example search is planned.

All 100 selected traces have proposals for all seven modes. 61 judgments map specific existing human notes or the reviewer’s explicit 19 September corrections; these are saved as binary labels and synced to Langfuse. The other 639 pairs require acceptance or correction. An open-code “no failure observed” is not silently expanded into seven negative labels, and an initial first-failure note does not establish absence of later failures.

## Completing the judgments

Reload http://localhost:8022/ once to load the updated interface, then select **Labeling**. The default **Review by category** view lets you choose a failure category and filter its remaining proposals to **Needs your decision**, **Proposed present**, or **Proposed absent**.

Read the evidence reasons together and use **Read conversation** when needed. Adjust **Your judgment** and **Edit evidence / reason** for corrections. Tick the rows you agree with, or use **Select all shown with a decision** after checking that group, then **Confirm selected judgments**. Only visible selected rows are saved; hidden rows and other categories are untouched. Unresolved choices cannot be selected until you supply a binary decision and a reason. Draft choices survive filtering and opening conversations.

Use **Review by trace** to review all seven modes together or edit a previously confirmed judgment. Both views save to the same Langfuse scores and local label files. **Progress** shows the live outstanding count and sample fractions. This written report is a snapshot and must be refreshed with the final counts after labeling.

Before recording, finish binary judgments, ensure **No pending saves**, and check the summary's final-15 assessment and documented evidence limitations. The initial 100 reviews and all suggestion decisions are already complete. The video is a single continuous recording of at most five minutes; see the handout's Video section for the required talking points.

## Accepted counts — incomplete sample fractions

These counts describe accepted labels, not all proposed labels. A sample fraction is intentionally withheld until that mode has judgments for all 100 traces. The live Progress page updates as you confirm; this report is a revision-264 snapshot.

| Mode | Accepted present | Accepted absent | Pending | Sample fraction |
|---|---:|---:|---:|---|
| `irrelevant_response_detail` | 44 | 0 | 56 | Pending full labeling |
| `unnecessary_tool_use` | 4 | 1 | 95 | Pending full labeling |
| `out_of_scope_assistance` | 1 | 0 | 99 | Pending full labeling |
| `account_change_not_escalated` | 2 | 0 | 98 | Pending full labeling |
| `missing_terminal_response` | 1 | 0 | 99 | Pending full labeling |
| `unresolved_data_not_escalated` | 3 | 0 | 97 | Pending full labeling |
| `arbitrary_amount_refund_accepted` | 5 | 0 | 95 | Pending full labeling |

## Final 15 and stability

The reviewer confirmed: **“No new modes in the final 15.”** The stability assessment is complete: **0 previously unseen consequential modes**. The blank-product-title observation in support-0201 is another instance of the unresolved-data escalation problem already observed in support-0199. Other observations fit the response-detail and tool-use categories. Boundary disagreements remain below; they do not currently suggest a new mode. Exact trace IDs and original notes are in `part_e_results.json`. This aggregate assessment is human-confirmed; it does not create individual binary labels.

## Rare findings retained

- `out_of_scope_assistance`: original support-0171 cooking response plus the accepted Workshop replay. Two executions of one prompt; insufficient for three confirmed positive traces.
- `missing_terminal_response`: original support-0187 MaxTurnsExceeded execution. The completed retry is a separate trace and does not repair the failure. One confirmed positive trace.

Both remain important findings. Both are included in the final seven categories and the structured labeling pass. Their inclusion does not imply that the handout’s three-positive-example minimum has been met. No unsupported examples or negative labels were manufactured.

## Decisions that need a boundary judgment

These 15 pairs are deliberately unanswered rather than defaulted to Pass. The remaining pending pairs have a concrete proposed value.

### support-0008 · af49984d · irrelevant_response_detail

Human asks for delivery date plus courier link, but the customer explicitly asks for recorded delivery details, which the four-field reply supplies. No verified courier link is present. Clarify the removable passage rather than invent a link.

Trace: `af49984dc91e47db608d63faa92ded92`.

### support-0107 · 03eea94e · irrelevant_response_detail

Reply directly answers payment destination and arrival time. Human criticism targets replacing cw-refunds citation with a link; RESP-1 requires a policy ID and this mode permits citations. No irrelevant factual passage clearly identified.

Trace: `03eea94e339079ee9def08a11381d891`.

### support-0120 · 5b837ec6 · irrelevant_response_detail

Human note asks to link rather than quote policy IDs. Required case list is relevant; clarify whether the extra 24-hour SLA is the intended failure, because citations alone are explicitly allowed.

Trace: `5b837ec63fe035d8f5a30e747439cd78`.

### support-0096 · 9b1992c6 · irrelevant_response_detail

User explicitly asks how last return day is calculated; human calls day-by-day arithmetic verbose. Definition permits requested calculations. Clarify whether to remove intermediate day counts while retaining calculation.

Trace: `9b1992c61269c5847959a4b8f0f0cf91`.

### support-0113 · 21a4cd26 · irrelevant_response_detail

Human note concerns policy linking; store conditions/windows/fees are directly requested. Clarify a removable passage under RESP-6 without dropping RESP-1 citations.

Trace: `21a4cd2657d5a85f73e45d541ef74a1a`.

### support-0173 · 089507b6 · irrelevant_response_detail

Human says perhaps unnecessary, but user explicitly requests where to look or whom to contact for external purchase. Redirect to receipt and platform support appears responsive; human confirmation needed.

Trace: `089507b64071be7c8c4a5106d91ba528`.

### support-0007 · c81c0040 · irrelevant_response_detail

Human says older-order mention perhaps unnecessary; two exact orders exist and latest was chosen. Clarify whether older order disambiguation is useful or irrelevant before definitive label.

Trace: `c81c00408d16cc3c4fa83ed70eb5692d`.

### support-0160 · 73f0b843 · irrelevant_response_detail

Human asks to hide cw-escalations reference, but RESP-1 and current boundary require/allow policy IDs. Clarify whether repetitive surrounding explanation, rather than citation, is intended.

Trace: `73f0b843314c4c9e25c1af321734589e`.

### support-0108 · 387254f5 · irrelevant_response_detail

Final-15 human says perhaps unnecessary about three stage examples. User explicitly asks whether preparation or shipment is cutoff; examples may resolve that confusion. Clarify repetition boundary.

Trace: `387254f5a3a7ef46bc17203b3000d828`.

### support-0241 · 15722bec · irrelevant_response_detail

Final-15 note says opened-item fee should be first, but this selected turn asks unopened returns; later companion turn corrects to opened. Do not retroactively treat future correction as original request. Clarify whether critique belongs to later turn or opening priority.

Trace: `15722bec05498dbe2f89313b8fa0cfc7`.

### support-0187 · 76c8e18f · unnecessary_tool_use

Preserve the latest rejected suggestion: the reviewer says the store mismatch should have been escalated at the start. The trace does contain the unrelated Juniper lookup and original tool-count note, but the user has rejected this tool-use interpretation. Leave this mode unresolved rather than overriding that decision; unresolved-data escalation is separately supported.

Trace: `76c8e18fa4c2178b34ce3595aed9696b`.

### support-0214 · 52f2fc00 · unnecessary_tool_use

The human note says too many tool calls. The two Golden Hour Coffee override queries overlap in the same batch and seek nearly equivalent information, but they are not retries after receiving the first result. The other calls establish two candidate orders, policy, queued refund and escalation. Specific duplication remains a proposal requiring human boundary confirmation rather than a count-only positive.

Trace: `52f2fc0018f1dc217e65e663ac43075f`.

### support-0234 · 5ef3d4aa · account_change_not_escalated

The human review records no_failure_observed. Under the current mode definition, this repeat explicit account-name request still has no ticket: the assistant asks for the preferred name before opening one. Preserve the human judgment and request clarification instead of silently replacing it with failure.

Trace: `5ef3d4aa226924959b5fe2743563f400`.

### support-0198 · 24236f8d · unresolved_data_not_escalated

Definition suggests positive: Rustic Pitcher price -$5 is flagged as invalid, but no ticket is opened. However, the existing human review is no_failure_observed. Preserve it and ask the human to reconcile this trace against the later negative-price escalation boundary; do not silently convert it to a failure.

Trace: `24236f8dba7acf1357062f9c642ee2d2`.

### support-0208 · 99638720 · arbitrary_amount_refund_accepted

Needs your decision: the saved note treats this acknowledgement as accepting a partial refund. However, this turn only repeats that ticket 183 already requests $100.01 of a $234.00 one-item order; it neither creates a ticket nor executes/queues a new refund. The current mode explicitly excludes mere acknowledgement of an earlier request, which would make this turn absent. The original ticket-creation turn is separately proposed present. Do you want this turn absent under the current boundary, or to revise the definition to include reaffirming an earlier invalid request?

Trace: `99638720ac41b466629adc9e9e59c7c9`.

## Verification

- Read all 322 live Langfuse traces and their 251 sessions; no fresh agent/model runs.
- Validated all 700 pairs against selected trace IDs, saved annotation IDs, and actual span IDs in the same conversation.
- 61 mapped human judgments synced and individually read back from Langfuse; trace, mode, value, version and evidence note matched. Zero pending writes at revision 264.
- 20 offline review-app regression tests passed. Isolated browser check verified unresolved choices prevent submission and multi-mode confirmation saves without touching real reviews.

Part E is not yet complete: 639 binary decisions still need acceptance/correction. Final sample fractions and the submission-ready report depend on these judgments.
