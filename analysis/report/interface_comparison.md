# HW4 interface comparison

## Evidence inspected

The proposal used ten complete live Langfuse traces from six HW3 scenarios:
both turns of `support-0001`, both turns of `support-0031`, `support-0140`,
the failed attempt and retry of `support-0187`, both turns of `support-0189`,
and `support-0190`. They cover shopper, merchant and support roles. Standard
Langfuse trace and annotation controls were also inspected. These technical
checks do not substitute for the student's own trace review or failure labels.

## Retained design

The reference UI's evidence selection and adjacent tool arguments/results are
retained. Selecting a passage opens a freeform note beside the conversation.
Notes retain exact evidence coordinates and earlier versions. Long model
requests and raw JSON can be expanded when needed.

## Changed design, based on the traces

The main workspace groups traces by `cartwheel.session_id` and displays all
turns chronologically. Each turn retains its own trace ID and review status.
For example, the second turn of `support-0031` confirms a refund without a new
tool call; the supporting result is in the first turn. Reading the second
trace alone obscures that evidence.

The reference offline normalizer groups by scenario ID, which would combine
the failed attempt and retry of `support-0187`. The new adapter preserves their
separate sessions. Langfuse's native session field was empty in all ten
inspected traces; the Cartwheel metadata supplies the grouping key instead.

The added trace outline follows the current position and supports jumping
among nested spans, Previous/Next controls, keyboard navigation, annotation
markers, error markers and conversation-turn selection. The review queue and
outline can collapse to make more room for evidence. This responds directly
to the student's requested navigation improvement.

Open coding, taxonomy editing and structured labeling have separate views.
Pending suggestions are visually distinct and require a human decision.
Progress counts selected trace IDs, not sessions or casually viewed context.
Definition changes make existing labels stale rather than silently treating
old judgments as decisions under the new definition.

## Remaining limitation

This is a local, single-reviewer interface. It rejects stale browser saves but
does not merge concurrent editing or import later edits made directly to
Langfuse scores. Make review edits through the interface, retain the local
workspace snapshot, and resolve pending sync operations before submission.
Trace caching is per server session; restart to see newly arriving runs.

## Verification and pending homework work

- The live interface loaded 322 HW3 traces into 251 sessions. The live feature
  map loaded all 322 records. This did not execute new agent/model runs.
- Browser checks exercised span jumps, turn selection, and the visible layout.
- An isolated UI instance using temporary state verified quote selection,
  persistent highlighting after reload, explicit review status, initial
  sampling, taxonomy editing, labels and stale judgments after a revision.
  Its synthetic notes and labels were not written to the real homework state
  or Langfuse. This was test-fixture use, not an offline homework review.
- Score writes, edits, retries and failure recovery were checked against a fake
  API. No synthetic test score was added to live traces. Part E subsequently
  wrote 59 judgments grounded in human reviews and read each back through the
  Langfuse v2 API, matching trace, mode, value, version and evidence note.
- Offline regression checks: 37 passed, 3 skipped (optional submission
  checks), 19 deselected. JavaScript syntax validation also passed.
- The student's standard-Langfuse friction notes and human assessments remain
  theirs to provide. Part C's ten fresh runs and candidate findings are recorded
  in [workshop_notes.md](workshop_notes.md), together with the student's decisions:
  W1–W4 accepted; W5 revised to retain correct escalation and treat the follow-up
  checks as reasonable.

## Workshop comparison after Part C

Workshop's run outline and MCP queries made it straightforward to compare actual
model/tool activity and isolate a refund on conflicting order state. Its
conversation view exposes intermediate model narration as well as the final
reply; that distinction matters because the application returns the final reply.
The custom review interface remains the place for the sampled HW3 conversations,
evidence notes, taxonomy decisions and structured labels.

Initially Workshop's tool previews were empty although span attributes retained
the arguments/results. On 19 September the runner's compatibility mapping was
fixed and 24 recorded tool spans were backfilled from their existing attributes.
Tool payload verification is recorded in `workshop_payload_verification.json`.
The custom interface also places these details beside the conversation. Workshop
also grouped request and workflow spans that appeared under separate Langfuse
trace IDs during initial setup; the final runner preserves one trace for both.
These are instrumentation/display limitations, not agent failure labels.

No live-store outage required an offline review fallback.
