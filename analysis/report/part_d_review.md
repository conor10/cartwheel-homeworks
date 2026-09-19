> **19 September update:** All seven suggestion decisions are now saved. This checklist is retained as the original review instructions. See `part_d_decisions.json` and `review_summary.md` for current status.

# Part D — your next review

Open http://localhost:8022 and choose **Suggestions**. There are seven new cards. Open the complete conversation from each card before deciding.

- **Accept as a note** when the proposed failure is present; briefly explain why.
- **Reject suggestion** when the proposed failure is absent; briefly explain the boundary.
- Cards 4 and 5 are deliberately disputed high-count hits. I currently recommend rejecting those failure hypotheses because the calls supply relevant missing information. That recommendation is not a saved human decision.

| Card | Scenario | What to check |
|---|---|---|
| 1 | support-0084 · `59b72a2a` | Extra return-policy branch after the shipped cancellation is already decided. |
| 2 | support-0187 · `76c8e18f` | Unrelated Juniper policy in the original failed run. |
| 3 | support-0246 · `702493ab` | Fifteen product-ID text searches that return no products. |
| 4 | support-0098 · `37d735b1` | Whether the eight calls each establish needed order/policy facts. |
| 5 | support-0246 · `d4a6d188` | Whether the follow-up order lookups add missing store names requested by the user. |
| 6 | support-0235 · `373cebad` | Account-change follow-up ends without the required ticket. |
| 7 | support-0187 · `6c962525` | Completed retry chooses a policy despite inconsistent merchant records. |

Then review the seven definitions in **Taxonomy** or [taxonomy_draft.md](taxonomy_draft.md). The original notes are linked, and each definition has candidate positives and close negatives. You can give definition changes here in chat.

Two shortages are explicit: cooking scope failure has two observed positive executions of one prompt (HW3 + Workshop), and missing final response has one. Neither satisfies three confirmed positives yet. No extra runs were generated to manufacture evidence.

Part D still needs your decisions on these suggestions and example mappings, then the AgentDebug comparison once the taxonomy is stable. The saved search currently contains **no human-rejected search suggestion**; W5 rejected a Workshop hypothesis, which is different. Please reject only where the evidence warrants it.

The review app will preserve any rejection and its reason. It will not assign all Part E binary labels when you accept a suggestion.
