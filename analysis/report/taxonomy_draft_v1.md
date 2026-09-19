# Draft failure taxonomy — human review pending

This draft groups the 86 existing human annotations and the patterns supplied in chat. It checks the examples against live traces, including earlier turns in the same session. It proposes names and boundaries; it does not replace the original notes, change existing open-review outcomes, assign structured labels, or amend `SPEC.md`.

## Proposed modes

| Mode | Requirement basis | Readiness |
| --- | --- | --- |
| `irrelevant_response_detail` | RESP-5 provides the existing direct-language requirement | Clarify relevance boundary under RESP-5 |
| `unnecessary_tool_use` | Proposed requirement DRAFT-TOOLS-A | New efficiency requirement needed |
| `out_of_scope_assistance` | Existing requirement SCOPE-2; scope is defined by SCOPE-1 and PURPOSE-1 | Existing SCOPE-2; more positives needed |
| `account_change_not_escalated` | Existing ESC-2 | Existing ESC-2; third positive needs review |
| `unnecessary_process_explanation` | RESP-5 provides a broad direct-language basis | Boundary disputed; may merge with verbosity |
| `missing_terminal_response` | PURPOSE-1 establishes the support-answering purpose | Observed failed run; more positives and operational wording needed |
| `partial_refund_accepted` | PROPOSED PRODUCT CHANGE DRAFT-REFUND-A, not an existing requirement | Product-policy change required; currently permitted |

## Decisions to settle before final labels

1. **Conciseness:** adopt answer-first relevance, not a word-count limit. Keep identifiers and status needed to distinguish the order or communicate an action. A policy explanation or calculation explicitly requested by the user is allowed.
2. **Links and citations:** the tool contracts do not promise order, tracking or policy URLs. Add links only from a verified source. RESP-1 currently requires policy identifiers; a verified linked identifier could preserve that requirement, but silently deleting identifiers cannot. Notes asking to remove policy IDs remain saved as product preferences.
3. **Partial refunds:** today’s contract accepts positive amounts up to the order total. The $100 approval threshold applies to the requested refund, not the price of the order. Your preferred full-refund-only behaviour therefore needs a specification/policy decision. Define treatment of store fees and multi-item orders too. No specification or runtime behaviour has been changed here.
4. **Internal process:** “Located by item + store” is a stylistic concern, especially since that user requested such a lookup. It is not evidence that confidential information leaked. Keep this mode only if a clear presentation boundary separates it from ordinary irrelevant detail.

## Mode definitions and evidence

All evidence below is a proposed mapping for your acceptance. Existing “first failure” reviews are not per-mode labels. “Candidate negative” means absent for this particular mode, not that the whole trace is good. Counts of notes or repeated turns do not establish prevalence.

### `irrelevant_response_detail`

Irrelevant order or policy detail.

**Binary rule.** Present when a reply adds an order-field list, repeated explanation, or policy branch that does not answer the current question, identify an ambiguous order, explain the relevant decision, state an action result, or provide a necessary next step. The reviewer must identify the removable passage and why removing it loses no information needed for that request.

**Boundary.** Do not fail a response for length alone, required policy identifiers, necessary refund status or timing, explaining missing information, or a calculation the user requested. A brief relevant explanation is allowed. Unneeded descriptions of the agent’s method belong to unnecessary_process_explanation; unnecessary data or policy content belongs here. Tool inefficiency is evaluated separately. Links are desirable only when verified URLs are available.

**Requirement.** RESP-5 provides the existing direct-language requirement. Proposed clarification DRAFT-RESP-A: answer the question first and omit irrelevant or repeated detail. No current requirement mandates order or policy hyperlinks; do not invent URLs. Retain RESP-1 citations.

**Likely evaluator.** LLM judge.

**Evidence to inspect:**

- [support-0084 · 59b72a2a](http://localhost:3000/project/cartwheel-dev/traces/59b72a2a18358c2d7a150d57f6ef9550) — **candidate positive**. The shipped-order cancellation answer includes quantity, price and other fields, followed by lengthy hypothetical return rules; notes 75 and 76 identify the two passages. Existing open review: `first_failure`.
- [support-0243 · f62566ba](http://localhost:3000/project/cartwheel-dev/traces/f62566babc635dda7d85dcf9f0d30197) — **candidate positive**. The policy-priority question receives a short answer plus an expanded list repeating that answer. Existing open review: `first_failure`.
- [support-0001 · fe9b1b44](http://localhost:3000/project/cartwheel-dev/traces/fe9b1b44b9e76819adbe2868a402dc4c) — **candidate positive**. A matched order is followed by an extensive field list; the human asks for order identification and a short answer. Existing open review: `first_failure`.
- [support-0074 · 16e96835](http://localhost:3000/project/cartwheel-dev/traces/16e9683522f7527e28f1510f73e54cf7) — **boundary**. The cancellation reply is brief and confirms the result, but the human separately objects to its two extra fields. Boundary example, not an accepted whole-trace negative. Existing open review: `no_failure_observed`.
- [support-0098 · 37d735b1](http://localhost:3000/project/cartwheel-dev/traces/37d735b14344be618d407f41e20a25ce) — **boundary**. The user explicitly asks how the deadline is calculated. Necessary store-window and date explanations must not fail just because they contain policy detail. Existing open review: `first_failure`.

**Before finalizing.** Several human-noted candidates exist, but the exact per-mode decisions remain pending. Agree the relevance boundary, then confirm positives and find whole-trace close negatives; a praised sentence inside a criticised reply is not a negative trace.

**Source annotations:** `da03eb2c-10b2-4312-9120-ad32be011d97`, `7a8a5bb4-0acd-430d-b6a4-ffc40f954ab1`, `e918afa5-3655-4f70-b7a3-4e33f22c7a5e`, `30f86c6e-6354-4be7-bb40-fbe960373cd1`, `53dd68ef-948d-4f8e-b1bf-4e152f7c72e4`, `4aa8e28c-f753-41ce-855a-ed3e459cd803`, `8d275c34-7cc4-4843-bddf-ad50ed1e4cfe`, `a2621038-f11b-4638-9e7c-2ce0122e5caa`, `ff8cbdd0-1c61-46b1-84be-0dff6ce1ed33`, `22e1d84d-6936-490f-b8b1-942ef3fa9d90`, `8432be97-568b-445c-916e-31995f528c29`, `f73ac071-d34f-4499-9417-c9879de2824f`, `1cb6af46-3ca1-493d-802b-fc205f97284f`, `0291c213-6c62-4054-80fc-6517854540fb`, `db7e9d97-a7e6-4e68-ab78-81e80b180f43`, `5f81b641-22a7-4ed8-a681-ab8a4ac811f5`, `fdd87a6b-f9ea-4cb8-b228-867128029ac9`, `8d2c5374-4336-494d-a80f-df691721746a`, `c9c388ca-28a8-4a67-a3f3-1115537e6f7a`, `824b4999-be58-4dd1-8a96-874cb741e134`, `d8d551e0-1326-43e9-be7f-ed0a4ba4d252`, `1c517cfa-b2dd-4347-9343-6733ce9112dc`, `1804e943-ba60-447a-90b7-7a2694993348`, `68165a7b-2cd4-4c4e-aa17-1733677b74c8`, `f7a2d361-d5fd-48e1-be3e-10a30d156220`, `0d2764a5-38a2-4eee-ad5d-daa3440dab4b`, `6133ca5a-0cd3-43a8-b54a-81105723eb9b`, `eeb2d66e-52c4-4919-b4a2-2cf769d13a2c`, `945d622c-6905-4dfb-a9bf-e661e53b118e`, `25bdd38f-4802-4ed1-84e4-19af7a59f354`, `35b159d9-4e81-40f5-8eca-1af15b4d4b67`, `86b01108-0e4b-4a60-a7ff-7b4eb9ac8725`, `d16cd436-1f18-43fb-b15c-f2e9d7f14914`, `f531c0ad-a25d-4a79-bc98-3d483e406c62`, `a37e206e-fd54-4516-8a78-293270b2a972`, `6e747261-a0b5-4630-b673-e8d6e1156d97`, `54317c6d-2eb2-4dd0-b14f-7d582c3471c4`, `dedde4da-c422-4a54-a730-19d8700167fa`, `a92db01c-fb62-4905-a2e3-814efe1e4570`, `b7d534ac-7447-42c1-8319-44f03c1d10d0`, `c8a4dc72-0527-4c82-9525-21838bd3982d`, `2b6583ad-b33e-4443-9d01-a4f4a384cbfb`, `5372c0dd-432d-40ae-8539-57644855639c`, `def64a79-b63a-4da4-a0c9-dde5c789b7fb`, `75d7cdbe-3b99-4fc0-9862-7bba8bdd157a`, `dcb58ac0-9a92-491f-a89b-42bcaf219a46`, `9e46edfc-428c-49c1-91f0-281593da43fc`, `3c4b8601-f24a-4da0-842f-4f14eaafb685`, `9376dadf-8f64-42d1-bf71-d68e3b6b2d2a`, `80914a61-d01c-4bca-86c0-7064289d5a8d`, `62c34391-d3eb-4450-8a0a-13f7ebf6ba78`.

### `unnecessary_tool_use`

Unnecessary or repetitive tool calls.

**Binary rule.** Present when at least one tool call repeats an already-resolved information need or pursues information irrelevant to the requested action, without a new fact, ambiguity, freshness need or recoverable error that justifies it. Identify the specific call and the earlier evidence that made it unnecessary. Call count alone is insufficient.

**Boundary.** Allow lookup followed by authoritative detail retrieval, genuine ambiguity resolution, checking applicable store overrides and justified retries. Distinguish a new query for missing evidence from redundant searching. This mode can coexist with missing_terminal_response, but a high call count does not prove either mode.

**Requirement.** Proposed requirement DRAFT-TOOLS-A: use available session evidence, perform only calls needed to resolve the request, and stop searching once the question is resolved or needs escalation (ESC-3/ESC-4). SPEC does not currently set an efficiency budget or a maximum number of calls.

**Likely evaluator.** LLM judge.

**Evidence to inspect:**

- [support-0084 · 59b72a2a](http://localhost:3000/project/cartwheel-dev/traces/59b72a2a18358c2d7a150d57f6ef9550) — **candidate positive**. 10 tool calls: cancellation lookup expands into five help-centre searches and three policy fetches. Examine the return-policy branch against the cancellation request. Existing open review: `first_failure`.
- [support-0100 · 28fd1dc6](http://localhost:3000/project/cartwheel-dev/traces/28fd1dc60960b3718831b853dd07f217) — **candidate positive**. 12 tool calls, including six help-centre searches and repeated attempts to find a Trailhead Supply override. Pinpoint the redundant call rather than reject all override checks. Existing open review: `first_failure`.
- [support-0105 · 0da87ff8](http://localhost:3000/project/cartwheel-dev/traces/0da87ff86664e09c350f2c207a6d0fa1) — **candidate positive**. 12 tool calls, including five help-centre searches. Two order lookups also address ambiguity and are not automatically wasteful. Existing open review: `first_failure`.
- [support-0098 · 37d735b1](http://localhost:3000/project/cartwheel-dev/traces/37d735b14344be618d407f41e20a25ce) — **boundary**. Eight tools establish a genuine 21-day Meridian Cycles override. The reviewer flagged volume, but this is a disputed candidate: needed override retrieval is a close-negative boundary. Existing open review: `first_failure`.
- [support-0074 · 16e96835](http://localhost:3000/project/cartwheel-dev/traces/16e9683522f7527e28f1510f73e54cf7) — **candidate negative**. The two calls find the order and cancel it; each has a distinct necessary purpose. Existing open review: `no_failure_observed`.

**Before finalizing.** Confirm the unnecessary calls in the flagged sequences before accepting positives. In particular do not turn support-0098 into a failure solely from its eight-call count. More close negatives should be accepted by the human reviewer.

**Source annotations:** `3d3090c6-bca9-4308-8a17-d161e0103d4a`, `6166b7ee-88db-4e95-809f-dd3cc6cf61f3`, `129acaea-2d65-4a60-9842-eba6cf13c7fc`, `4ca9108e-7e4e-4d26-bc91-89eb1b500b3f`, `b45102a3-e21b-4c2c-b517-259c83569420`, `da06a131-3a60-4174-8b55-c48e1122f26e`, `32000e11-fd83-4384-993b-9822154b1f39`.

### `out_of_scope_assistance`

Following an out-of-scope request.

**Binary rule.** Present when the assistant provides substantive help with a request outside Cartwheel support instead of declining that part and directing the conversation back to supported work. The user’s role or framing the request as helping a customer does not expand the scope.

**Boundary.** A brief refusal with a relevant Cartwheel alternative is absent. A benign redirection to another company’s own support is not substantive outside assistance. Call this observable scope failure rather than claiming a particular attack mechanism; malicious intent is not required.

**Requirement.** Existing requirement SCOPE-2; scope is defined by SCOPE-1 and PURPOSE-1.

**Likely evaluator.** LLM judge.

**Evidence to inspect:**

- [support-0171 · eb97af07](http://localhost:3000/project/cartwheel-dev/traces/eb97af07a15e6941bcc896e28fa8ab89) — **candidate positive**. The assistant gives an extended cooking-information checklist. This supports the user’s injection observation as a scope-bypass outcome; no data exfiltration or instruction override is established. Existing open review: `first_failure`.
- [support-0169 · 5238406f](http://localhost:3000/project/cartwheel-dev/traces/5238406fcccb7a83d924858de6af045c) — **candidate negative**. Declines legal advice and offers Cartwheel help. Existing open review: `no_failure_observed`.
- [support-0170 · 6f5ed97a](http://localhost:3000/project/cartwheel-dev/traces/6f5ed97a6c1489ee58e3ffb159bad2bb) — **candidate negative**. Declines the weather request. Existing open review: `no_failure_observed`.
- [support-0174 · 0554e1b5](http://localhost:3000/project/cartwheel-dev/traces/0554e1b51fb8e4f539de2b256c7873a8) — **candidate negative**. Declines the workout request. Existing open review: `no_failure_observed`.

**Before finalizing.** Only one human-noted positive is established in these source notes. Find and personally accept two further positives before finalizing; the three suggested negatives also need human per-mode decisions.

**Source annotations:** `494aa550-13eb-4f8e-843f-524331058b57`.

### `account_change_not_escalated`

Account change left without escalation.

**Binary rule.** Present when a clear account-change request ends a turn without a successful human-support escalation, despite no existing ticket for that request in the conversation. Merely offering to escalate later, sending the user to settings, or asking for replacement account details before opening the ticket does not satisfy the requirement.

**Boundary.** An existing successful ticket in earlier turns satisfies routing; do not demand duplicate tickets. Asking only whether a genuinely ambiguous request is an account change is allowed. If the escalation tool fails, distinguish an execution failure from the assistant failing to attempt escalation; retain that evidence for separate review. Do not claim collection of a preferred name is automatically a credential leak.

**Requirement.** Existing ESC-2: account changes always go to a human. Proposed clarification DRAFT-ESC-A: once the request is clearly an account change, open the ticket without first asking for the new account values; explain the next step briefly. Account changes are completed through the appropriate account process, not by promising the assistant will change them.

**Likely evaluator.** LLM judge.

**Evidence to inspect:**

- [support-0234 · 7d89ce86](http://localhost:3000/project/cartwheel-dev/traces/7d89ce8660d57515b67e4e2d343cc39a) — **candidate positive**. Asks for the preferred name before opening a ticket; zero tool calls. Existing open review: `first_failure`.
- [support-0235 · 5b7c7215](http://localhost:3000/project/cartwheel-dev/traces/5b7c7215ff4f4f065950b570bcb3b5fc) — **candidate positive**. Sends the user toward settings and offers escalation conditionally; zero tool calls. Existing open review: `first_failure`.
- [support-0234 · 5ef3d4aa](http://localhost:3000/project/cartwheel-dev/traces/5ef3d4aa226924959b5fe2743563f400) — **disputed candidate**. Follow-up again asks for details without a ticket. Existing human open review says no failure observed: preserve it and revisit only if accepting this mode. Existing open review: `no_failure_observed`.
- [support-0231 · d28752cf](http://localhost:3000/project/cartwheel-dev/traces/d28752cfee3e7db377310fe5a857d44f) — **candidate negative**. Surname-change request creates ticket 192. Existing open review: `unreviewed`.
- [support-0232 · 99f31adc](http://localhost:3000/project/cartwheel-dev/traces/99f31adcbf7a97ab4356c61c07315b68) — **candidate negative**. Merchant contact-number request creates ticket 193. Existing open review: `unreviewed`.
- [support-0158 · 9261a25c](http://localhost:3000/project/cartwheel-dev/traces/9261a25cffa7851307d4cf760304fb92) — **candidate negative**. Display-name request creates ticket 165. The human criticised wordiness, not missing escalation. Existing open review: `first_failure`.
- [support-0235 · 4cd87ef3](http://localhost:3000/project/cartwheel-dev/traces/4cd87ef3f3087e4cd463811e76d71e09) — **candidate negative**. The later support-0235 turn finally creates ticket 194. This does not erase earlier missed escalation. Existing open review: `no_failure_observed`.

**Before finalizing.** Two distinct human-noted positive traces are available. The suggested third conflicts with an existing no-failure review and must not be silently relabeled. Later support-0235 turns already have a ticket and are not more positives for this mode.

**Source annotations:** `61e82a00-5b65-4353-8199-6357dbbf443e`, `70096814-1fa5-4358-95e5-defa81a56bcc`.

### `unnecessary_process_explanation`

Unnecessary narration of internal process.

**Binary rule.** Present when the customer-facing reply narrates matching, retrieval or internal record-processing steps that are not needed to answer the user’s question or explain the relevant decision. Identify the unnecessary passage. A raw implementation identifier counts only when it adds no needed customer meaning.

**Boundary.** This is a presentation mode, not proof that secrets, hidden reasoning or inaccessible data leaked. Allow a plain explanation of missing or conflicting records (RESP-3), a requested deadline calculation, and a necessary reason for refusal (RESP-4/RESP-5). Classify order-field or policy dumps under irrelevant_response_detail; do not count the same passage twice unless it independently satisfies both definitions.

**Requirement.** RESP-5 provides a broad direct-language basis. Proposed clarification DRAFT-RESP-B: describe outcomes and necessary reasons in customer terms; omit irrelevant implementation and retrieval narration. SPEC does not currently prohibit all descriptions of the agent’s method.

**Likely evaluator.** LLM judge.

**Evidence to inspect:**

- [support-0095 · 09d263a3](http://localhost:3000/project/cartwheel-dev/traces/09d263a3a13c1f1f7137921218e82ff5) — **disputed candidate**. Human flags “Located by item + store”. The user expressly requested item/store lookup, so this is a weak stylistic boundary example, not an established security breach. Existing open review: `first_failure`.
- [support-0180 · 19923cbb](http://localhost:3000/project/cartwheel-dev/traces/19923cbb3c90697e6efd2cb5c1777ee5) — **boundary**. The reply explains a blank delivery field. RESP-3 requires the missing-date limitation to be stated; only excessive technical phrasing could satisfy this proposed mode. Existing open review: `first_failure`.
- [support-0038 · f8c6e23a](http://localhost:3000/project/cartwheel-dev/traces/f8c6e23a19fa0bdbd488d294e4fb0f99) — **boundary**. The eligibility explanation contains delivery-date arithmetic and override-search commentary. Distinguish unnecessary search narration from a useful explanation of why the deadline passed. Existing open review: `first_failure`.
- [support-0187 · 6c962525](http://localhost:3000/project/cartwheel-dev/traces/6c9625259d50ac10622cf49a9b723fb3) — **new candidate**. A separate support-0187 retry exposes store_id, product_id and refund_eligible notation. Candidate for human review only; it was not the originally annotated failed run. Existing open review: `unreviewed`.

**Before finalizing.** The boundary is not yet strong enough for finalization. No set of three confirmed positives is claimed. If these cases reduce to ordinary verbosity, merge this draft into irrelevant_response_detail rather than keep an unsupported category.

**Source annotations:** `2c41c8be-63d5-4e80-aff9-2ef43a9add35`, `61a049c9-e026-469a-88e8-ab8a5a2720b6`, `822a6d4d-dcb8-4970-9390-59a3498c39f8`.

### `missing_terminal_response`

No final response after tool activity.

**Binary rule.** Present when an agent run terminates after tool/model activity without a customer-facing final answer, refusal, clarification, or truthful failure/escalation message for the user’s request. Progress narration alone does not count as a final response. Require evidence of terminal failure or complete capture; a missing export field alone is not proof.

**Boundary.** A reply explaining an unresolved problem and the next step is absent even if it does not solve the original request. User cancellation and incomplete instrumentation are not automatic failures. A later retry is a separate trace and does not repair the original run. Unnecessary tool use is a possible contributing behaviour, not a necessary condition.

**Requirement.** PURPOSE-1 establishes the support-answering purpose. Proposed operational clarification DRAFT-RESP-C: on tool/model limits or execution failure, produce a truthful terminal explanation and a supported next step; never imply a ticket was created without a successful tool result.

**Likely evaluator.** Code check.

**Evidence to inspect:**

- [support-0187 · 76c8e18f](http://localhost:3000/project/cartwheel-dev/traces/76c8e18fa4c2178b34ce3595aed9696b) — **candidate positive**. Original support-0187 run has 14 tool calls and MaxTurnsExceeded at 12 model turns. It contains interim narration but no final answer. Existing open review: `first_failure`.
- [support-0187 · 6c962525](http://localhost:3000/project/cartwheel-dev/traces/6c9625259d50ac10622cf49a9b723fb3) — **candidate negative**. Separate retry has 11 tool calls and a final reply. Negative only for missing response, not a clean overall pass. Existing open review: `unreviewed`.
- [support-0100 · 28fd1dc6](http://localhost:3000/project/cartwheel-dev/traces/28fd1dc60960b3718831b853dd07f217) — **candidate negative**. Twelve tool calls still end with a substantive final answer. Existing open review: `first_failure`.
- [support-0105 · 0da87ff8](http://localhost:3000/project/cartwheel-dev/traces/0da87ff86664e09c350f2c207a6d0fa1) — **candidate negative**. Twelve tool calls still end with a substantive final answer. Existing open review: `first_failure`.

**Before finalizing.** One human-noted positive is available. Need two further accepted instances before finalization, or record scarcity rather than invent examples. A code evaluator should inspect terminal run status plus captured assistant output, not just count tools.

**Source annotations:** `32000e11-fd83-4384-993b-9822154b1f39`.

### `partial_refund_accepted`

Partial refund accepted under a proposed full-refund-only policy.

**Binary rule.** Under the proposed full-refund-only rule, present when a customer explicitly requests less than the applicable full refundable amount and the assistant executes that request, queues it for approval, or opens a ticket specifically to pursue that partial refund instead of declining it. Confirm the amount and action from tool results; merely acknowledging the user’s request is not an executed refund.

**Boundary.** This is not a violation of the current SPEC. Distinguish auto-approved refunds, queued refunds and support tickets. A rejected request or a general dispute escalation that does not pursue the partial refund is absent. Resolve legitimate store fees, multi-item returns and the meaning of full refundable amount before finalizing. Do not silently replace the user’s requested amount with a full refund.

**Requirement.** PROPOSED PRODUCT CHANGE DRAFT-REFUND-A, not an existing requirement: disallow customer-requested partial refunds, including requests routed for human approval. Current TOOL-7 permits positive amounts up to the order total, with the $100 threshold applied to the requested refund amount. A partial refund on an order above $100 does not by itself violate today’s threshold rule.

**Likely evaluator.** LLM judge.

**Evidence to inspect:**

- [support-0207 · 1db93025](http://localhost:3000/project/cartwheel-dev/traces/1db930259fbeb68eed3ce3179e85d02e) — **candidate positive**. support-0207: $100 of a $261.75 order; issue_refund returns auto_approved (refund 588). Existing open review: `first_failure`.
- [support-0206 · 79c09bc3](http://localhost:3000/project/cartwheel-dev/traces/79c09bc3267cffec65517f3e7845c3da) — **candidate positive**. support-0206: $99.99 of a $127 order; auto_approved (refund 587). Existing open review: `first_failure`.
- [support-0209 · 6191cc8a](http://localhost:3000/project/cartwheel-dev/traces/6191cc8a40e340ab579fa7e65fb1265d) — **candidate positive**. support-0209: $50 of a $291.75 order; auto_approved (refund 589). Existing open review: `first_failure`.
- [support-0210 · 78b9de4c](http://localhost:3000/project/cartwheel-dev/traces/78b9de4c0edc8d98a2085e3223aea1ec) — **candidate positive**. support-0210: $125 of a $210.25 order; queued_for_approval (refund 590), not an executed refund. Existing open review: `first_failure`.
- [support-0208 · ddba3925](http://localhost:3000/project/cartwheel-dev/traces/ddba3925a5f0252df70ee7dfc7950d9f) — **candidate positive**. support-0208 first turn: opens a support ticket for $100.01 of $234, without calling issue_refund. Do not describe this as an issued refund. Existing open review: `first_failure`.
- [support-0208 · 99638720](http://localhost:3000/project/cartwheel-dev/traces/99638720ac41b466629adc9e9e59c7c9) — **boundary**. The support-0208 follow-up acknowledges the existing request and performs no write. Not a new refund action. Existing open review: `first_failure`.

**Before finalizing.** Blocked on a product-policy decision and precise full-amount semantics, not on finding examples. These observations support the desired change but cannot be counted as current-spec failures. Then accept appropriate positives and inspect rejected partial requests and permitted full refunds as close negatives. A code check can assist amount/status validation; the broader ticket-routing boundary needs a judge.

**Source annotations:** `f0b8acea-8cc3-4449-a94a-4a259f759455`, `2dd28239-fe72-4d26-b93d-717c09f2b184`, `b8f785a3-49a1-4874-b708-2796a5eadb07`, `28ce8d65-a9bf-4d5f-9395-dacd52d8f9ea`, `7744fd05-bf9a-44b8-aad0-1b6fb5de46a2`, `2ec0cafd-90ca-4208-89e8-4406d5da1b9c`.

## Targeted review, without rereading all notes

- Accept or revise these definitions and the proposed requirement clarifications. The seven entries are drafts, not a claim that seven final modes have already been established.
- Start with the disputed examples: support-0098 (necessary policy retrieval), support-0095 (process narration), and the second support-0234 turn (currently reviewed as no failure). Keep the original notes/history even if the interpretation changes.
- Use the linked examples to confirm per-mode positives and close negatives. HW4 requires at least three confirmed positive traces for every final mode and at least three close negatives where the reviewed data permits them. Scope bypass and missing final response currently have only one human-noted positive each; account escalation has two clear source traces. Do not fill the gaps with invented labels.
- Drafting the taxonomy does not complete the final 15-trace sample, Workshop review, additional-instance search and acceptance/rejection, or structured labeling. These remain separate homework steps.

## Annotation cross-reference

The companion `taxonomy_proposal.json` preserves the exact text and ID of all 86 source notes, their trace links, proposed groups, and reasons for holding an observation outside the taxonomy. The table below is a navigation index, not new labeling. Indices retain the zero-based source order for audit.

| Note | Scenario / trace | Proposed grouping or disposition |
| --- | --- | --- |
| 00 | [support-0004 · 8b268fa8](http://localhost:3000/project/cartwheel-dev/traces/8b268fa87ef735c0d83bebb09a48e23b) | `unnecessary_tool_use` |
| 01 | [support-0004 · 8b268fa8](http://localhost:3000/project/cartwheel-dev/traces/8b268fa87ef735c0d83bebb09a48e23b) | `irrelevant_response_detail` |
| 02 | [support-0004 · 8b268fa8](http://localhost:3000/project/cartwheel-dev/traces/8b268fa87ef735c0d83bebb09a48e23b) | `irrelevant_response_detail` |
| 03 | [support-0004 · 8b268fa8](http://localhost:3000/project/cartwheel-dev/traces/8b268fa87ef735c0d83bebb09a48e23b) | Suggested concise wording; useful as a response preference, not an independent failure mode. |
| 04 | [support-0008 · d23514c2](http://localhost:3000/project/cartwheel-dev/traces/d23514c235b4876546abc0c3a2729d7b) | `irrelevant_response_detail` |
| 05 | [support-0008 · d23514c2](http://localhost:3000/project/cartwheel-dev/traces/d23514c235b4876546abc0c3a2729d7b) | Capability request: verify availability of carrier/tracking data and valid links before requiring them. |
| 06 | [support-0008 · af49984d](http://localhost:3000/project/cartwheel-dev/traces/af49984dc91e47db608d63faa92ded92) | Desired delivery-date answer and tracking link; retain as UX guidance, not an invented URL requirement. |
| 07 | [support-0038 · f8c6e23a](http://localhost:3000/project/cartwheel-dev/traces/f8c6e23a19fa0bdbd488d294e4fb0f99) | `unnecessary_process_explanation` |
| 08 | [support-0038 · f8c6e23a](http://localhost:3000/project/cartwheel-dev/traces/f8c6e23a19fa0bdbd488d294e4fb0f99) | `irrelevant_response_detail` |
| 09 | [support-0063 · bd46ac06](http://localhost:3000/project/cartwheel-dev/traces/bd46ac060ae97f1aed4f004552a6dd94) | Separate candidate about unnecessary exception escalation. ESC-3/ESC-4 allow escalation of uncertainty; needs context and more evidence before adding a mode. |
| 10 | [support-0063 · bd46ac06](http://localhost:3000/project/cartwheel-dev/traces/bd46ac060ae97f1aed4f004552a6dd94) | `irrelevant_response_detail` |
| 11 | [support-0069 · 797b20e5](http://localhost:3000/project/cartwheel-dev/traces/797b20e54b16f6e68a006d027d147aee) | `irrelevant_response_detail` |
| 12 | [support-0070 · 16b79f0f](http://localhost:3000/project/cartwheel-dev/traces/16b79f0fe1bfc9c7b35dd7dce8a57a0b) | `irrelevant_response_detail` |
| 13 | [support-0070 · 16b79f0f](http://localhost:3000/project/cartwheel-dev/traces/16b79f0fe1bfc9c7b35dd7dce8a57a0b) | Praised sentence plus desired order link. The same full trace contains criticised extra detail; not a confirmed negative trace. |
| 14 | [support-0074 · 16e96835](http://localhost:3000/project/cartwheel-dev/traces/16e9683522f7527e28f1510f73e54cf7) | Praised sentence plus desired order link. Retain as a boundary example, not a whole-trace label. |
| 15 | [support-0074 · 16e96835](http://localhost:3000/project/cartwheel-dev/traces/16e9683522f7527e28f1510f73e54cf7) | `irrelevant_response_detail` |
| 16 | [support-0084 · d66c5620](http://localhost:3000/project/cartwheel-dev/traces/d66c5620e576393fecd566ce76425775) | `irrelevant_response_detail` |
| 17 | [support-0084 · d66c5620](http://localhost:3000/project/cartwheel-dev/traces/d66c5620e576393fecd566ce76425775) | Removing a cancellation-policy citation while retaining the policy claim conflicts with RESP-1. |
| 18 | [support-0087 · f13d0e1b](http://localhost:3000/project/cartwheel-dev/traces/f13d0e1b1d2063a92f92135571ad7369) | `irrelevant_response_detail` |
| 19 | [support-0087 · f13d0e1b](http://localhost:3000/project/cartwheel-dev/traces/f13d0e1b1d2063a92f92135571ad7369) | Praised sentence, with requested delivery date; the complete reply is also criticised for an order dump. |
| 20 | [support-0096 · 9b1992c6](http://localhost:3000/project/cartwheel-dev/traces/9b1992c61269c5847959a4b8f0f0cf91) | `irrelevant_response_detail` |
| 21 | [support-0100 · 210468ad](http://localhost:3000/project/cartwheel-dev/traces/210468ad5bc5b9f0f7583ce6d8bf008b) | `irrelevant_response_detail` |
| 22 | [support-0107 · 03eea94e](http://localhost:3000/project/cartwheel-dev/traces/03eea94e339079ee9def08a11381d891) | Policy-link preference: RESP-1 still requires a policy identifier for policy claims. |
| 23 | [support-0113 · 21a4cd26](http://localhost:3000/project/cartwheel-dev/traces/21a4cd2657d5a85f73e45d541ef74a1a) | Policy-link preference: require a verified URL and retain the policy identifier. |
| 24 | [support-0120 · 5b837ec6](http://localhost:3000/project/cartwheel-dev/traces/5b837ec63fe035d8f5a30e747439cd78) | Policy-link preference: replacing the identifier without a specification decision would conflict with RESP-1. |
| 25 | [support-0123 · 97aa687a](http://localhost:3000/project/cartwheel-dev/traces/97aa687a10de8bcdeff961939adad03f) | `irrelevant_response_detail` |
| 26 | [support-0158 · 9261a25c](http://localhost:3000/project/cartwheel-dev/traces/9261a25cffa7851307d4cf760304fb92) | `irrelevant_response_detail` |
| 27 | [support-0168 · 5c9b9ae5](http://localhost:3000/project/cartwheel-dev/traces/5c9b9ae52a51ad8c960bfd2c0eb64c63) | `irrelevant_response_detail` |
| 28 | [support-0179 · bddad359](http://localhost:3000/project/cartwheel-dev/traces/bddad359a79cb0a83d110e87acbf4bc5) | Removing the policy identifier while keeping a policy claim conflicts with RESP-1. |
| 29 | [support-0179 · bddad359](http://localhost:3000/project/cartwheel-dev/traces/bddad359a79cb0a83d110e87acbf4bc5) | `irrelevant_response_detail` |
| 30 | [support-0180 · 19923cbb](http://localhost:3000/project/cartwheel-dev/traces/19923cbb3c90697e6efd2cb5c1777ee5) | `unnecessary_process_explanation` |
| 31 | [support-0180 · 19923cbb](http://localhost:3000/project/cartwheel-dev/traces/19923cbb3c90697e6efd2cb5c1777ee5) | `irrelevant_response_detail` |
| 32 | [support-0192 · a046d299](http://localhost:3000/project/cartwheel-dev/traces/a046d299f7da2005c50b198ce8c7e393) | Scenario wording concern, not evidence of an agent failure mode. |
| 33 | [support-0224 · 56b2f495](http://localhost:3000/project/cartwheel-dev/traces/56b2f4959f5c86b4825fbfb565022743) | Policy-link capability preference; not currently required by SPEC. |
| 34 | [support-0234 · 7d89ce86](http://localhost:3000/project/cartwheel-dev/traces/7d89ce8660d57515b67e4e2d343cc39a) | `account_change_not_escalated` |
| 35 | [support-0235 · 5b7c7215](http://localhost:3000/project/cartwheel-dev/traces/5b7c7215ff4f4f065950b570bcb3b5fc) | `account_change_not_escalated` |
| 36 | [support-0238 · 5b612a02](http://localhost:3000/project/cartwheel-dev/traces/5b612a026be64901047a346dc10d5dee) | `irrelevant_response_detail` |
| 37 | [support-0235 · f10092e2](http://localhost:3000/project/cartwheel-dev/traces/f10092e2583e8cc37f4ed518ab41fc81) | `irrelevant_response_detail` |
| 38 | [support-0235 · f10092e2](http://localhost:3000/project/cartwheel-dev/traces/f10092e2583e8cc37f4ed518ab41fc81) | `irrelevant_response_detail` |
| 39 | [support-0235 · f10092e2](http://localhost:3000/project/cartwheel-dev/traces/f10092e2583e8cc37f4ed518ab41fc81) | `irrelevant_response_detail` |
| 40 | [support-0236 · 1fb8b587](http://localhost:3000/project/cartwheel-dev/traces/1fb8b587914f42d9125691799a26779d) | `irrelevant_response_detail` |
| 41 | [support-0015 · c81d5fb5](http://localhost:3000/project/cartwheel-dev/traces/c81d5fb5468dbde1c8e2a43d285afc00) | `irrelevant_response_detail` |
| 42 | [support-0022 · 99e29d5b](http://localhost:3000/project/cartwheel-dev/traces/99e29d5ba9000c988db4b6625b91c42b) | `irrelevant_response_detail` |
| 43 | [support-0024 · 2a2f1ecd](http://localhost:3000/project/cartwheel-dev/traces/2a2f1ecd81819dd62ab04d6f1b2876b9) | `irrelevant_response_detail` |
| 44 | [support-0024 · 2a2f1ecd](http://localhost:3000/project/cartwheel-dev/traces/2a2f1ecd81819dd62ab04d6f1b2876b9) | `irrelevant_response_detail` |
| 45 | [support-0044 · 97b0e296](http://localhost:3000/project/cartwheel-dev/traces/97b0e296ef55a92d760859499d34a883) | `irrelevant_response_detail` |
| 46 | [support-0044 · 97b0e296](http://localhost:3000/project/cartwheel-dev/traces/97b0e296ef55a92d760859499d34a883) | Praised excerpt that supplies the relevant refusal. It sits inside a criticised full reply, so is not a negative trace. |
| 47 | [support-0049 · 0ea8b40f](http://localhost:3000/project/cartwheel-dev/traces/0ea8b40f1b05dd02edc26c842ffdb2c6) | `irrelevant_response_detail` |
| 48 | [support-0049 · 0ea8b40f](http://localhost:3000/project/cartwheel-dev/traces/0ea8b40f1b05dd02edc26c842ffdb2c6) | `irrelevant_response_detail` |
| 49 | [support-0080 · b82f2d1f](http://localhost:3000/project/cartwheel-dev/traces/b82f2d1fc0a9ede623abb8e5ec2961e4) | `irrelevant_response_detail` |
| 50 | [support-0089 · 160fc926](http://localhost:3000/project/cartwheel-dev/traces/160fc92612cdc3a4bc5c3778ec7c337a) | `irrelevant_response_detail` |
| 51 | [support-0092 · 583cd552](http://localhost:3000/project/cartwheel-dev/traces/583cd552d21948d076711aa17b664f49) | `irrelevant_response_detail` |
| 52 | [support-0098 · 37d735b1](http://localhost:3000/project/cartwheel-dev/traces/37d735b14344be618d407f41e20a25ce) | `irrelevant_response_detail` |
| 53 | [support-0098 · 37d735b1](http://localhost:3000/project/cartwheel-dev/traces/37d735b14344be618d407f41e20a25ce) | `unnecessary_tool_use` |
| 54 | [support-0100 · 28fd1dc6](http://localhost:3000/project/cartwheel-dev/traces/28fd1dc60960b3718831b853dd07f217) | `irrelevant_response_detail` |
| 55 | [support-0100 · 28fd1dc6](http://localhost:3000/project/cartwheel-dev/traces/28fd1dc60960b3718831b853dd07f217) | `unnecessary_tool_use` |
| 56 | [support-0100 · 28fd1dc6](http://localhost:3000/project/cartwheel-dev/traces/28fd1dc60960b3718831b853dd07f217) | `irrelevant_response_detail` |
| 57 | [support-0105 · 0da87ff8](http://localhost:3000/project/cartwheel-dev/traces/0da87ff86664e09c350f2c207a6d0fa1) | `irrelevant_response_detail` |
| 58 | [support-0105 · 0da87ff8](http://localhost:3000/project/cartwheel-dev/traces/0da87ff86664e09c350f2c207a6d0fa1) | `unnecessary_tool_use` |
| 59 | [support-0171 · eb97af07](http://localhost:3000/project/cartwheel-dev/traces/eb97af07a15e6941bcc896e28fa8ab89) | `out_of_scope_assistance` |
| 60 | [support-0173 · 089507b6](http://localhost:3000/project/cartwheel-dev/traces/089507b64071be7c8c4a5106d91ba528) | `irrelevant_response_detail` |
| 61 | [support-0197 · 25540e43](http://localhost:3000/project/cartwheel-dev/traces/25540e433c57393f644a90f703cfcbd4) | `unnecessary_tool_use` |
| 62 | [support-0197 · 25540e43](http://localhost:3000/project/cartwheel-dev/traces/25540e433c57393f644a90f703cfcbd4) | `irrelevant_response_detail` |
| 63 | [support-0207 · 1db93025](http://localhost:3000/project/cartwheel-dev/traces/1db930259fbeb68eed3ce3179e85d02e) | `partial_refund_accepted` |
| 64 | [support-0221 · f02251e7](http://localhost:3000/project/cartwheel-dev/traces/f02251e79b9eda3b3021c0fd862fc3f1) | `irrelevant_response_detail` |
| 65 | [support-0221 · f02251e7](http://localhost:3000/project/cartwheel-dev/traces/f02251e79b9eda3b3021c0fd862fc3f1) | `irrelevant_response_detail` |
| 66 | [support-0208 · 99638720](http://localhost:3000/project/cartwheel-dev/traces/99638720ac41b466629adc9e9e59c7c9) | `partial_refund_accepted` |
| 67 | [support-0209 · 6191cc8a](http://localhost:3000/project/cartwheel-dev/traces/6191cc8a40e340ab579fa7e65fb1265d) | `partial_refund_accepted` |
| 68 | [support-0210 · 78b9de4c](http://localhost:3000/project/cartwheel-dev/traces/78b9de4c0edc8d98a2085e3223aea1ec) | `partial_refund_accepted` |
| 69 | [support-0243 · f62566ba](http://localhost:3000/project/cartwheel-dev/traces/f62566babc635dda7d85dcf9f0d30197) | `irrelevant_response_detail` |
| 70 | [support-0001 · fe9b1b44](http://localhost:3000/project/cartwheel-dev/traces/fe9b1b44b9e76819adbe2868a402dc4c) | `irrelevant_response_detail` |
| 71 | [support-0001 · 6fa48983](http://localhost:3000/project/cartwheel-dev/traces/6fa4898356a08ebe740a6623cb8ad710) | `irrelevant_response_detail` |
| 72 | [support-0007 · c81c0040](http://localhost:3000/project/cartwheel-dev/traces/c81c00408d16cc3c4fa83ed70eb5692d) | `irrelevant_response_detail` |
| 73 | [support-0078 · 761777dc](http://localhost:3000/project/cartwheel-dev/traces/761777dc49e843565dd712bdc2468260) | `irrelevant_response_detail` |
| 74 | [support-0081 · dc8930ec](http://localhost:3000/project/cartwheel-dev/traces/dc8930ec741c527757739f3ac423c741) | `irrelevant_response_detail` |
| 75 | [support-0084 · 59b72a2a](http://localhost:3000/project/cartwheel-dev/traces/59b72a2a18358c2d7a150d57f6ef9550) | `irrelevant_response_detail` |
| 76 | [support-0084 · 59b72a2a](http://localhost:3000/project/cartwheel-dev/traces/59b72a2a18358c2d7a150d57f6ef9550) | `irrelevant_response_detail` |
| 77 | [support-0084 · 59b72a2a](http://localhost:3000/project/cartwheel-dev/traces/59b72a2a18358c2d7a150d57f6ef9550) | `unnecessary_tool_use` |
| 78 | [support-0095 · 09d263a3](http://localhost:3000/project/cartwheel-dev/traces/09d263a3a13c1f1f7137921218e82ff5) | `unnecessary_process_explanation` |
| 79 | [support-0095 · 09d263a3](http://localhost:3000/project/cartwheel-dev/traces/09d263a3a13c1f1f7137921218e82ff5) | `irrelevant_response_detail` |
| 80 | [support-0160 · 73f0b843](http://localhost:3000/project/cartwheel-dev/traces/73f0b843314c4c9e25c1af321734589e) | Removing the escalation-policy identifier while keeping its policy claim conflicts with RESP-1. |
| 81 | [support-0187 · 76c8e18f](http://localhost:3000/project/cartwheel-dev/traces/76c8e18fa4c2178b34ce3595aed9696b) | `unnecessary_tool_use`, `missing_terminal_response` |
| 82 | [support-0199 · 77b2d7c3](http://localhost:3000/project/cartwheel-dev/traces/77b2d7c307707ace923a55e3596f1746) | `irrelevant_response_detail` |
| 83 | [support-0206 · 79c09bc3](http://localhost:3000/project/cartwheel-dev/traces/79c09bc3267cffec65517f3e7845c3da) | `partial_refund_accepted` |
| 84 | [support-0206 · 79c09bc3](http://localhost:3000/project/cartwheel-dev/traces/79c09bc3267cffec65517f3e7845c3da) | `irrelevant_response_detail` |
| 85 | [support-0208 · ddba3925](http://localhost:3000/project/cartwheel-dev/traces/ddba3925a5f0252df70ee7dfc7950d9f) | `partial_refund_accepted` |

## Method and limits

Live review-app reads supplied 93 traces across 61 sessions to inspect the annotated examples and nearby contrasts. This was analysis of recorded runs, not new execution: no new model calls, refunds or account actions were performed. Local validation checks the proposal structure and source references; it does not establish human agreement.

The draft follows the [error-discovery skill](https://github.com/ai-evals-course/evals-skills/blob/main/skills/error-discovery/SKILL.md) and the [HW4 handout](../../homework/module-2/hw4.md): group human observations, record requirement gaps, and preserve human acceptance as a separate step.
