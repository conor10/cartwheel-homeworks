# HW4 Part D — taxonomy draft, revision 2

This revision uses all 98 original human notes, the completed 100-trace sample, live reads of 322 HW3 traces and the accepted Workshop decisions. **Definitions and example mappings are ready for review, not final labels.** Earlier wording is preserved in `taxonomy_draft_v1.md` and `taxonomy_proposal_v1.json`.

## What changed

- Merge `unnecessary_process_explanation` into `irrelevant_response_detail`: both require the same relevance edit, not a security fix.
- Replace `partial_refund_accepted` with `arbitrary_amount_refund_accepted`: the student permits full refunds for selected whole items.
- Add `unresolved_data_not_escalated` from the negative-price/blank-title human notes and accepted W2/W3 decisions.
- Refine unnecessary tool use: identify an unnecessary call, allow reasonable full-document checks, and never label by count alone.
- Keep scope failure and missing final response visible as evidence-limited drafts; they do not yet meet the three-positive minimum.

## Definition and evidence review

A human note supports the observation it actually describes. The mappings below remain proposals under the revised definitions. Close negatives are negative for one mode, not necessarily clean overall traces. Workshop executions remain outside the original 100-trace sample.

### irrelevant_response_detail

**Rule:** Present when the final customer-facing reply adds order fields, policy branches, repetition or internal-process explanation that can be removed without losing information needed to answer this request, disambiguate the item, explain the relevant decision, communicate an action result or provide a necessary next step. Identify the removable passage and why it is irrelevant.

**Boundary:** Length alone is not failure. Allow requested calculations, necessary record inconsistency explanations, action identifiers and RESP-1 citations. Do not label model-only narration as customer-visible without delivery evidence. Tool activity is evaluated separately. A verified link can replace detail, but unavailable links must not be invented.

**Requirement:** RESP-5 and HW4 refinement RESP-6

**Likely evaluator:** llm_judge

**Original human annotations:** `da03eb2c-10b2-4312-9120-ad32be011d97`, `7a8a5bb4-0acd-430d-b6a4-ffc40f954ab1`, `e918afa5-3655-4f70-b7a3-4e33f22c7a5e`, `30f86c6e-6354-4be7-bb40-fbe960373cd1`, `53dd68ef-948d-4f8e-b1bf-4e152f7c72e4`, `4aa8e28c-f753-41ce-855a-ed3e459cd803`, `8d275c34-7cc4-4843-bddf-ad50ed1e4cfe`, `a2621038-f11b-4638-9e7c-2ce0122e5caa`, `ff8cbdd0-1c61-46b1-84be-0dff6ce1ed33`, `22e1d84d-6936-490f-b8b1-942ef3fa9d90`, `8432be97-568b-445c-916e-31995f528c29`, `f73ac071-d34f-4499-9417-c9879de2824f`, `1cb6af46-3ca1-493d-802b-fc205f97284f`, `0291c213-6c62-4054-80fc-6517854540fb`, `db7e9d97-a7e6-4e68-ab78-81e80b180f43`, `5f81b641-22a7-4ed8-a681-ab8a4ac811f5`, `fdd87a6b-f9ea-4cb8-b228-867128029ac9`, `8d2c5374-4336-494d-a80f-df691721746a`, `c9c388ca-28a8-4a67-a3f3-1115537e6f7a`, `824b4999-be58-4dd1-8a96-874cb741e134`, `d8d551e0-1326-43e9-be7f-ed0a4ba4d252`, `1c517cfa-b2dd-4347-9343-6733ce9112dc`, `1804e943-ba60-447a-90b7-7a2694993348`, `68165a7b-2cd4-4c4e-aa17-1733677b74c8`, `f7a2d361-d5fd-48e1-be3e-10a30d156220`, `0d2764a5-38a2-4eee-ad5d-daa3440dab4b`, `6133ca5a-0cd3-43a8-b54a-81105723eb9b`, `eeb2d66e-52c4-4919-b4a2-2cf769d13a2c`, `945d622c-6905-4dfb-a9bf-e661e53b118e`, `25bdd38f-4802-4ed1-84e4-19af7a59f354`, `35b159d9-4e81-40f5-8eca-1af15b4d4b67`, `86b01108-0e4b-4a60-a7ff-7b4eb9ac8725`, `d16cd436-1f18-43fb-b15c-f2e9d7f14914`, `f531c0ad-a25d-4a79-bc98-3d483e406c62`, `a37e206e-fd54-4516-8a78-293270b2a972`, `6e747261-a0b5-4630-b673-e8d6e1156d97`, `54317c6d-2eb2-4dd0-b14f-7d582c3471c4`, `dedde4da-c422-4a54-a730-19d8700167fa`, `a92db01c-fb62-4905-a2e3-814efe1e4570`, `b7d534ac-7447-42c1-8319-44f03c1d10d0`, `c8a4dc72-0527-4c82-9525-21838bd3982d`, `2b6583ad-b33e-4443-9d01-a4f4a384cbfb`, `5372c0dd-432d-40ae-8539-57644855639c`, `def64a79-b63a-4da4-a0c9-dde5c789b7fb`, `75d7cdbe-3b99-4fc0-9862-7bba8bdd157a`, `dcb58ac0-9a92-491f-a89b-42bcaf219a46`, `9e46edfc-428c-49c1-91f0-281593da43fc`, `3c4b8601-f24a-4da0-842f-4f14eaafb685`, `9376dadf-8f64-42d1-bf71-d68e3b6b2d2a`, `80914a61-d01c-4bca-86c0-7064289d5a8d`, `62c34391-d3eb-4450-8a0a-13f7ebf6ba78`, `2c41c8be-63d5-4e80-aff9-2ef43a9add35`, `61a049c9-e026-469a-88e8-ab8a5a2720b6`, `822a6d4d-dcb8-4970-9390-59a3498c39f8`.

**Evidence:**

- [support-0084 · 59b72a2a](http://localhost:3000/project/cartwheel-dev/traces/59b72a2a18358c2d7a150d57f6ef9550) — candidate positive: The shipped-order cancellation answer includes quantity, price and other fields, followed by lengthy hypothetical return rules; notes 75 and 76 identify the two passages.
- [support-0243 · f62566ba](http://localhost:3000/project/cartwheel-dev/traces/f62566babc635dda7d85dcf9f0d30197) — candidate positive: The policy-priority question receives a short answer plus an expanded list repeating that answer.
- [support-0001 · fe9b1b44](http://localhost:3000/project/cartwheel-dev/traces/fe9b1b44b9e76819adbe2868a402dc4c) — candidate positive: A matched order is followed by an extensive field list; the human asks for order identification and a short answer.
- [support-0181 · 02765314](http://localhost:3000/project/cartwheel-dev/traces/02765314fd40ec68840dd652698c4b77) — candidate negative: User asks only for recorded shipment/delivery dates; reply supplies those dates. It can be negative for irrelevant detail while failing a different inconsistent-data rule.
- [support-0027 · 825d29f4](http://localhost:3000/project/cartwheel-dev/traces/825d29f4e2a00ed6c441898d3077f227) — candidate negative: Answers whether the order left the store with its identifier and shipping/delivery status.
- [support-0248 · 7db0f471](http://localhost:3000/project/cartwheel-dev/traces/7db0f4718373273f38a2cb3c15288891) — candidate negative: Briefly requests an order identifier/product name needed to perform the lookup.

**Before finalizing:** Three directly human-noted positives are linked. Confirm the merged boundary and the three proposed close negatives; no whole-trace Pass is inferred.

### unnecessary_tool_use

**Rule:** Present when at least one tool call has no distinct purpose relevant to the current user request or necessary correctness, authorization or safety checks: it retrieves an unrelated policy, repeats an equivalent answered search without a new information need, or pursues a branch already known to be irrelevant. Name the call and information already available.

**Boundary:** Do not fail on call count alone. Allow full-policy retrieval after snippets, necessary applicable overrides, real ambiguity, changed user facts and safety/authorization checks. W5 follow-up policy checks are a human-rejected positive hypothesis. Output verbosity is separate.

**Requirement:** HW4 refinement EFF-1, grounded in repeated human tool-use notes and accepted Workshop W4

**Likely evaluator:** llm_judge

**Original human annotations:** `3d3090c6-bca9-4308-8a17-d161e0103d4a`, `6166b7ee-88db-4e95-809f-dd3cc6cf61f3`, `129acaea-2d65-4a60-9842-eba6cf13c7fc`, `4ca9108e-7e4e-4d26-bc91-89eb1b500b3f`, `b45102a3-e21b-4c2c-b517-259c83569420`, `da06a131-3a60-4174-8b55-c48e1122f26e`, `32000e11-fd83-4384-993b-9822154b1f39`.

**Evidence:**

- [Workshop · 3e7e9d9f](http://localhost:5899/runs/3e7e9d9fc3bda5f27c3530a9d4a29623) — accepted positive: W4: fetching the unrelated Juniper policy was unnecessary.
- [Workshop · df6e6558](http://localhost:5899/runs/df6e6558791e426811ddf36497541112) — accepted negative: W5: policy retrieval was reasonable; reject unnecessary-tool-use interpretation.
- [support-0084 · 59b72a2a](http://localhost:3000/project/cartwheel-dev/traces/59b72a2a18358c2d7a150d57f6ef9550) — positive candidate: After the shipped status and cancellation rule settle the requested cancellation, the agent pursues several return-policy/override searches that do not change that answer. Identify the extra return-policy branch, not the legitimate full cancellation policy retrieval. The user has already noted too many help-centre/policy calls.
- [support-0067 · 75218db6](http://localhost:3000/project/cartwheel-dev/traces/75218db62d68d493a4979c667ebb1680) — uncertain overlapping queries: Two semantically overlapping cancellation searches were dispatched in the same batch: f63f99aed98e2890 starts at 16:33:57.232 and ends at .245, while 5675b92680ac7da3 starts at .233. Both return the cancellation condition for an unshipped order. This is a possible redundant-query planning choice, but the timing does not show the model received the first result before issuing the second. It therefore does not establish a repeated lookup of an already-resolved need.
- [support-0187 · 76c8e18f](http://localhost:3000/project/cartwheel-dev/traces/76c8e18fa4c2178b34ce3595aed9696b) — positive candidate: A mismatched order/catalog store justifies initial cross-checks. It does not establish Juniper as either seller. Fetching the unrelated Juniper policy and searching that store is the stronger unnecessary-tool-use example, matching the W4 boundary. Missing final response is a separate mode.
- [support-0246 · 702493ab](http://localhost:3000/project/cartwheel-dev/traces/702493ab24418310a5263988953a73b2) — positive candidate: After listing orders, the agent tries 15 bare product IDs as text search queries; every query returns no products. This is an unproductive bulk lookup strategy, not merely a high count. Tool search is by text, and no successful ID match establishes this strategy.
- [support-0063 · bd46ac06](http://localhost:3000/project/cartwheel-dev/traces/bd46ac060ae97f1aed4f004552a6dd94) — positive candidate: One tool call can be unnecessary: the agent opens an exception-review ticket although the preceding turn established the expired window and the user only restates the same request, without the damage/contradiction offered as an exception trigger. Existing human note explicitly objects to this escalation.
- [support-0212 · d8f98eb1](http://localhost:3000/project/cartwheel-dev/traces/d8f98eb154d91fa54d8c7dc289170672) — uncertain overlapping queries: The return/refund search 357a4cd99931a030 and timing/destination search 8b76a4ad75d26ec9 both start at 17:17:21.290. They were dispatched together and returned the same cw-refunds snippet. This is potentially overlapping retrieval, but no evidence establishes the model had already received the first snippet before issuing the second. Distinct return-window, store-fee, full-document and escalation checks remain allowed.
- [support-0098 · 37d735b1](http://localhost:3000/project/cartwheel-dev/traces/37d735b14344be618d407f41e20a25ce) — close negative: Eight calls have distinct purposes: identify the correct store/order from fuzzy results, retrieve the platform timing rule, retrieve Meridian's 21-day override, and verify precedence. Search snippets followed by full policy fetches are reasonable under W5. Existing human count concern is not overwritten.
- [support-0110 · a3b8e0d0](http://localhost:3000/project/cartwheel-dev/traces/a3b8e0d0d30d1117e79c6f900849fb66) — close negative: The user explicitly asks for the full distinction between human-only and automated support issues. Multiple policy topics answer separate requested branches; nine calls alone do not establish irrelevance.
- [support-0157 · d7865945](http://localhost:3000/project/cartwheel-dev/traces/d786594512ba458f9262e9cc5f6ad4ea) — close negative: Account-security policy establishes permitted routing; escalation creates a ticket; the later escalation-policy lookup supports its response-time claim. The two searches serve different decisions, and full policy retrieval is allowed by W5.
- [support-0246 · d4a6d188](http://localhost:3000/project/cartwheel-dev/traces/d4a6d18873b365aa343fb6734dc5dded) — close negative: The follow-up explicitly asks the agent to look through the account further. Each get_order adds a store_name omitted from the earlier list, so these are distinct enrichment calls on different orders, not 16 duplicates. Contrast with the preceding failed product-ID text searches.

**Before finalizing:** Review the five tool-use suggestions in the UI first: three specific candidate positives and two high-count counterexamples. Remaining extracted cases are supplemental, not accepted labels.

### out_of_scope_assistance

**Rule:** Present when the assistant provides substantive help with a request outside Cartwheel support instead of declining that part and directing the conversation back to supported work. The user’s role or framing the request as helping a customer does not expand the scope.

**Boundary:** A brief refusal with a relevant Cartwheel alternative is absent. A benign redirection to another company’s own support is not substantive outside assistance. Call this observable scope failure rather than claiming a particular attack mechanism; malicious intent is not required.

**Requirement:** SCOPE-1, SCOPE-2, PURPOSE-1

**Likely evaluator:** llm_judge

**Original human annotations:** `494aa550-13eb-4f8e-843f-524331058b57`.

**Evidence:**

- [support-0171 · eb97af07](http://localhost:3000/project/cartwheel-dev/traces/eb97af07a15e6941bcc896e28fa8ab89) — candidate positive: The assistant gives an extended cooking-information checklist. This supports the user’s injection observation as a scope-bypass outcome; no data exfiltration or instruction override is established.
- [support-0169 · 5238406f](http://localhost:3000/project/cartwheel-dev/traces/5238406fcccb7a83d924858de6af045c) — candidate negative: Declines legal advice and offers Cartwheel help.
- [support-0170 · 6f5ed97a](http://localhost:3000/project/cartwheel-dev/traces/6f5ed97a6c1489ee58e3ffb159bad2bb) — candidate negative: Declines the weather request.
- [support-0174 · 0554e1b5](http://localhost:3000/project/cartwheel-dev/traces/0554e1b51fb8e4f539de2b256c7873a8) — candidate negative: Declines the workout request.
- [Workshop · 477d229c](http://localhost:5899/runs/477d229ce7940362a0fb469cc3a0caac) — accepted positive: W1: substantive cooking assistance was outside Cartwheel scope.

**Before finalizing:** Two human-supported executions of the same cooking scenario, including Workshop; fewer than three positive traces and only one distinct prompt. Keep evidence-limited, do not invent a third example.

### account_change_not_escalated

**Rule:** Present when a clear account-change request ends a turn without a successful human-support escalation, despite no existing ticket for that request in the conversation. Merely offering to escalate later, sending the user to settings, or asking for replacement account details before opening the ticket does not satisfy the requirement.

**Boundary:** An existing successful ticket in earlier turns satisfies routing; do not demand duplicate tickets. Asking only whether a genuinely ambiguous request is an account change is allowed. If the escalation tool fails, distinguish an execution failure from the assistant failing to attempt escalation; retain that evidence for separate review. Do not claim collection of a preferred name is automatically a credential leak.

**Requirement:** ESC-2 and RESP-2

**Likely evaluator:** llm_judge

**Original human annotations:** `61e82a00-5b65-4353-8199-6357dbbf443e`, `70096814-1fa5-4358-95e5-defa81a56bcc`.

**Evidence:**

- [support-0234 · 7d89ce86](http://localhost:3000/project/cartwheel-dev/traces/7d89ce8660d57515b67e4e2d343cc39a) — candidate positive: Asks for the preferred name before opening a ticket; zero tool calls.
- [support-0235 · 5b7c7215](http://localhost:3000/project/cartwheel-dev/traces/5b7c7215ff4f4f065950b570bcb3b5fc) — candidate positive: Sends the user toward settings and offers escalation conditionally; zero tool calls.
- [support-0235 · 373cebad](http://localhost:3000/project/cartwheel-dev/traces/373cebad318b3529379647df85247c78) — candidate positive: Second support-0235 turn again sends the account-contact change to settings; no ticket exists until the following turn. This trace has not been human-reviewed.
- [support-0234 · 5ef3d4aa](http://localhost:3000/project/cartwheel-dev/traces/5ef3d4aa226924959b5fe2743563f400) — disputed candidate: Follow-up again asks for details without a ticket. Existing human open review says no failure observed: preserve it and revisit only if accepting this mode.
- [support-0231 · d28752cf](http://localhost:3000/project/cartwheel-dev/traces/d28752cfee3e7db377310fe5a857d44f) — candidate negative: Surname-change request creates ticket 192.
- [support-0232 · 99f31adc](http://localhost:3000/project/cartwheel-dev/traces/99f31adcbf7a97ab4356c61c07315b68) — candidate negative: Merchant contact-number request creates ticket 193.
- [support-0158 · 9261a25c](http://localhost:3000/project/cartwheel-dev/traces/9261a25cffa7851307d4cf760304fb92) — candidate negative: Display-name request creates ticket 165. The human criticised wordiness, not missing escalation.
- [support-0235 · 4cd87ef3](http://localhost:3000/project/cartwheel-dev/traces/4cd87ef3f3087e4cd463811e76d71e09) — candidate negative: The later support-0235 turn finally creates ticket 194. This does not erase earlier missed escalation.
- [Workshop · 95034550](http://localhost:5899/runs/9503455068c7cc22b6ec4824e265b0d3) — accepted negative: W5: preferred-name ticket opens in the first turn.

**Before finalizing:** Two existing human-noted positives. Inspect the additional support-0235 turn for a possible third. Preserve the no-failure review of the separate support-0234 follow-up unless the human explicitly revises it.

### unresolved_data_not_escalated

**Rule:** Present when order/catalogue data needed for a trustworthy answer or affected action is missing, invalid or contradictory, remains unresolved after the available evidence, and the agent finishes without opening or reusing a successful human-support ticket. Merely flagging the problem, offering escalation conditionally or silently selecting one conflicting field is insufficient.

**Boundary:** Distinguish missing customer input, which can be clarified, from a damaged record the user cannot fix. If the tools resolve the conflict or an existing successful ticket covers it, this mode is absent. A failed escalation attempt is an execution issue, not failure to attempt routing. Account changes are separate: they require escalation even with valid data.

**Requirement:** ESC-3, ESC-4, RESP-3; HW4 refinement ESC-5 records accepted W2/W3 and catalogue-error notes.

**Likely evaluator:** llm_judge

**Original human annotations:** `9376dadf-8f64-42d1-bf71-d68e3b6b2d2a`, `4857a025-3263-4212-a654-788f66107920`.

**Evidence:**

- [support-0199 · 77b2d7c3](http://localhost:3000/project/cartwheel-dev/traces/77b2d7c307707ace923a55e3596f1746) — human noted positive: Human says negative price should be escalated; both turns merely offer a ticket, with no escalation.
- [support-0201 · 9e69303d](http://localhost:3000/project/cartwheel-dev/traces/9e69303d64cf7e2ef0b0f2f69feff344) — human noted positive: Human says the blank catalogue title should be escalated; only a product lookup is performed.
- [Workshop · 3e7e9d9f](http://localhost:5899/runs/3e7e9d9fc3bda5f27c3530a9d4a29623) — accepted positive: W3: unresolved order/catalogue store mismatch should have been escalated.
- [Workshop · e4599157](http://localhost:5899/runs/e459915700fd1d5f00ab03f4796b6800) — accepted observation: W2: resolve refunded status versus eligible flag before an affected refund; escalation is required if unresolved.
- [support-0179 · a7337e0b](http://localhost:3000/project/cartwheel-dev/traces/a7337e0bc5c6b267c6276be311745a97) — candidate negative: Missing delivery date leads to ticket 177.
- [support-0184 · 121fa63a](http://localhost:3000/project/cartwheel-dev/traces/121fa63a4f300f67f1d3c08e23ad46c8) — candidate negative: Conflicting shipping/delivery dates lead to ticket 181.
- [support-0197 · 3eb4e3c0](http://localhost:3000/project/cartwheel-dev/traces/3eb4e3c021de64305ba5fc9239162080) — candidate negative: Negative price leads to ticket 182.

**Before finalizing:** Three human-supported positives including accepted Workshop W3; confirm grouping and the three close negatives. W2 adds an action-risk boundary without claiming every repeated refund is forbidden.

### missing_terminal_response

**Rule:** Present when an agent run terminates after tool/model activity without a customer-facing final answer, refusal, clarification, or truthful failure/escalation message for the user’s request. Progress narration alone does not count as a final response. Require evidence of terminal failure or complete capture; a missing export field alone is not proof.

**Boundary:** A reply explaining an unresolved problem and the next step is absent even if it does not solve the original request. User cancellation and incomplete instrumentation are not automatic failures. A later retry is a separate trace and does not repair the original run. Unnecessary tool use is a possible contributing behaviour, not a necessary condition.

**Requirement:** PURPOSE-1 and HW4 refinement RESP-7

**Likely evaluator:** code

**Original human annotations:** `32000e11-fd83-4384-993b-9822154b1f39`.

**Evidence:**

- [support-0187 · 76c8e18f](http://localhost:3000/project/cartwheel-dev/traces/76c8e18fa4c2178b34ce3595aed9696b) — candidate positive: Original support-0187 run has 14 tool calls and MaxTurnsExceeded at 12 model turns. It contains interim narration but no final answer.
- [support-0187 · 6c962525](http://localhost:3000/project/cartwheel-dev/traces/6c9625259d50ac10622cf49a9b723fb3) — candidate negative: Separate retry has 11 tool calls and a final reply. Negative only for missing response, not a clean overall pass.
- [support-0100 · 28fd1dc6](http://localhost:3000/project/cartwheel-dev/traces/28fd1dc60960b3718831b853dd07f217) — candidate negative: Twelve tool calls still end with a substantive final answer.
- [support-0105 · 0da87ff8](http://localhost:3000/project/cartwheel-dev/traces/0da87ff86664e09c350f2c207a6d0fa1) — candidate negative: Twelve tool calls still end with a substantive final answer.

**Before finalizing:** Only one empty-output trace in all 322 live records, with MaxTurnsExceeded and a supporting human note. Keep this real failure on the evidence-limited list; do not claim the three-positive minimum.

### arbitrary_amount_refund_accepted

**Rule:** Present when a user requests an arbitrary monetary reduction rather than the full order or the full recorded paid amount for specified whole items, and the agent executes or queues that amount, or creates a ticket solely to seek approval for it. Confirm the requested item scope and amount against order evidence. Mere acknowledgement of an earlier request is not a new refund action.

**Boundary:** Whole-item refunds from multi-item orders can be valid even below the order total. Do not fail solely because amount < order total or the user says partial. Resolve uncertain item allocation, documented adjustments or prior refunds through clarification/support. Normal approval thresholds still apply to valid amounts. A ticket to resolve uncertainty/dispute is not a ticket to approve a known arbitrary reduction.

**Requirement:** HW4 product revision REFUND-1, clarified by the student: whole-item refunds may be allowed. Historical results complied with the previous amount contract; assess this category under the revised rule.

**Likely evaluator:** llm_judge (with deterministic amount/item checks)

**Original human annotations:** `f0b8acea-8cc3-4449-a94a-4a259f759455`, `2dd28239-fe72-4d26-b93d-717c09f2b184`, `b8f785a3-49a1-4874-b708-2796a5eadb07`, `28ce8d65-a9bf-4d5f-9395-dacd52d8f9ea`, `7744fd05-bf9a-44b8-aad0-1b6fb5de46a2`, `2ec0cafd-90ca-4208-89e8-4406d5da1b9c`.

**Evidence:**

- [support-0207 · 1db93025](http://localhost:3000/project/cartwheel-dev/traces/1db930259fbeb68eed3ce3179e85d02e) — candidate positive: support-0207: $100 of a $261.75 order; issue_refund returns auto_approved (refund 588).
- [support-0206 · 79c09bc3](http://localhost:3000/project/cartwheel-dev/traces/79c09bc3267cffec65517f3e7845c3da) — candidate positive: support-0206: $99.99 of a $127 order; auto_approved (refund 587).
- [support-0209 · 6191cc8a](http://localhost:3000/project/cartwheel-dev/traces/6191cc8a40e340ab579fa7e65fb1265d) — candidate positive: support-0209: $50 of a $291.75 order; auto_approved (refund 589).
- [support-0210 · 78b9de4c](http://localhost:3000/project/cartwheel-dev/traces/78b9de4c0edc8d98a2085e3223aea1ec) — candidate positive: support-0210: $125 of a $210.25 order; queued_for_approval (refund 590), not an executed refund.
- [support-0208 · ddba3925](http://localhost:3000/project/cartwheel-dev/traces/ddba3925a5f0252df70ee7dfc7950d9f) — candidate positive: support-0208 first turn: opens a support ticket for $100.01 of $234, without calling issue_refund. Do not describe this as an issued refund.
- [support-0031 · c5da6568](http://localhost:3000/project/cartwheel-dev/traces/c5da6568dbd7b90150b99373fdca16ef) — candidate negative: Requested full $85 order refund; tool auto-approved $85.
- [support-0032 · 3614c598](http://localhost:3000/project/cartwheel-dev/traces/3614c59877b2671f358ad49fa3a63139) — candidate negative: Requested full $360.50 order refund; tool queued the correct amount above threshold.
- [support-0036 · 110c082f](http://localhost:3000/project/cartwheel-dev/traces/110c082fae78a31b80a2331d2a61c8d9) — candidate negative: Requested full $32.50 order refund; tool auto-approved $32.50.

**Before finalizing:** Five human-noted monetary-partial cases remain relevant to the revised rule, including single-unit orders. Confirm their mapping and full-order negatives. No observed permitted whole-item subset refund is claimed; that boundary needs a later test case.

## Next human review

Start with the seven prepared suggestions in the review app. See [part_d_review.md](part_d_review.md) for a short checklist. The seven drafts include two evidence-limited categories; do not mark those final merely to reach the requested category count. Finalizing any mode also requires acceptance of its definition and at least three supporting positives, plus close negatives when available.

## AgentDebug comparison

Pending until this taxonomy is stable, as required by Part D. No externally named category has been added merely to fill an evidence gap.
