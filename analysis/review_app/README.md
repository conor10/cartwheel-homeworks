# HW4 trace review

Run from the repository root:

```sh
uv run python -m analysis.review_app.server
```

Open **http://localhost:8022**. The application binds only to loopback. It uses
the existing `LANGFUSE_*` settings from `.env`; keys never enter the browser.
Use `--port` if this port is occupied. No additional dependencies are required.

## Review workflow

- **Review:** filter the queue by role, intent, scenario group or review status.
  Each queue item shows Unreviewed, Reviewed · failure (amber), or Reviewed ·
  no failure (green). The queue header counts reviewed traces in the current filter.
  The queue retains its scroll position across refreshes and navigation, scrolling
  just enough to keep the selected trace visible. The outline also follows the active span.
  The complete session appears in chronological order, but the outline and
  notes always identify the individual trace currently being reviewed.
  The active turn shows “Reviewing this trace” and an indicator beside the
  notes. Selecting a turn displays confirmation without completing its review.
- **Trace outline:** click a span to scroll to it. Previous/Next and **J/K**
  navigate spans when focus is outside a form control. The outline preserves
  parent/child indentation, follows scrolling, and marks notes and execution
  errors. Select a different turn to change the active trace. Collapse the
  queue or outline for more space.
- **Evidence:** select text within one evidence field, write an observation,
  and save. Notes retain the trace ID, observation ID, field, quote and offsets.
  Drafts stay in browser storage; saved notes are mirrored locally and sent to
  Langfuse. Draft evidence stays highlighted with a dashed underline, including
  after a reload; saved evidence uses a solid underline. Note revisions preserve
  previous wording.
  **Clear selected evidence** removes a draft highlight while retaining the
  note text. To remove a saved highlight, edit its note, clear the evidence,
  then save the revision; the note and its previous evidence remain in history.
- **Complete open coding:** explicitly record “No failure observed”, or select
  a saved note and mark it as the first failure. Merely opening a trace never
  marks it reviewed. Reopen a review if necessary.
  A completion panel confirms the outcome and its Langfuse sync status, with
  **Next unreviewed** beside it. Saving an outcome keeps you on the current trace.
- **Explore & sample:** choose the later product dimension before creating
  the initial 15 random + 15 cluster representative sample. Subsequent controls
  add 30 dimension traces, up to 25 manually selected depth-search traces, and
  the final 15 uniform traces after the first 85 have been reviewed and a
  taxonomy drafted. Each trace belongs to at most one batch. Seed 41 and
  selection reasons are retained in the manifest. These controls do not run
  automatically when the app starts.
  Once the initial sample exists, **Review initial 30 traces** opens its saved
  traces in a filtered queue. **Next unreviewed** stays within that batch;
  change the queue's review-status filter to see the wider collection.
  The dimension card likewise shows its saved batch and offers **Review
  dimension traces**, rather than attempting to create the batch again.
  Depth selections require a search purpose / selection reason. Validation and
  save confirmation appear beside the add button. Unfinished selections, search
  results and the reason stay in browser storage across navigation and reloads.
  **Review depth traces** opens the saved depth batch in its own filtered queue.
  **Edit depth selection** lists the saved depth traces and their selection
  reasons. Select unwanted entries (or select all and untick the ones to keep),
  record a correction reason, and remove them from the batch. This frees slots
  for replacements without deleting notes, reviews, labels or Langfuse scores.
  The manifest retains removed entries and the correction reason in `removals`;
  progress and sample fractions use only current batch membership.
- **Map/search:** load complete live observations on demand. Clustering reuses
  the supplied numeric trace-feature helpers; representatives are selected by
  distance from each cluster centroid. The plot shows tool calls against
  recorded messages with small deterministic jitter for overlapping points.
  Search uses the supplied bag-of-words cosine similarity, not an LLM.
- **Taxonomy:** write a definition, boundary, requirement source and likely
  evaluator; link supporting human notes. Definitions may be draft, final or
  retired. Revisions retain history and make labels for older versions stale.
  A rename can be represented by retiring the old mode and creating a new one.
- **Labeling:** assign present (Fail / 1) or absent (Pass / 0) for each reviewed
  sample trace and each final mode. Add evidence and optionally mark an absent
  case as a close negative. **Review by category** is the default: choose a
  category, filter pending judgments, read the evidence, select agreed rows and
  confirm them together. Select-all affects only visible resolved rows. Unknown
  values cannot be saved, and drafts survive filters/conversation navigation.
  **Review by trace** shows all modes together and allows edits to saved labels.
  Separate
  AI proposals prefill candidate values and evidence; unresolved choices remain
  blank. **Confirm judgments for this trace** atomically saves the whole set, and
  **Next trace needing judgments** advances without auto-confirming anything.
  Proposals never create scores. Confirmed labels retain their revision history.
- **Suggestions:** proposals remain separate until explicitly accepted or
  rejected. Acceptance saves the reviewer's own wording as a note. It does not
  complete a review or assign a binary label. Rejections remain inspectable.
- **Progress:** counts distinct sampled traces, incomplete/stale decisions,
  batch coverage, composition and sample fractions. It does not certify the
  later Workshop analysis, taxonomy stability assessment or video.

Use **Specification** to consult `SPEC.md`. Scenario expected outcomes are not
included in the review payload. Recorded text is shown faithfully, including
Markdown source; complete model inputs and result JSON are expandable.

## Data and persistence

The default collection is live Langfuse traces whose scenario IDs occur in
`scenarios/support_scenarios.jsonl`. This excludes pilot and demonstration
records. Use `--scenarios PATH` to explicitly select a different collection.
The supplied scenario file adds only intent and group metadata; its expected
outcomes do not become labels. The source trace IDs remain unchanged.

Session grouping uses `cartwheel.session_id`, including nested OpenTelemetry
attributes. Missing session IDs fall back to one trace per group, never one
shared unknown session. A retry with a different session ID remains separate,
with a link to the other attempt. Full traces are cached in memory during the
server session; restart the server to fetch newly arriving traces.

Langfuse stores saved notes and review outcomes as TEXT scores, with complete
structured evidence in the score comment. Accepted binary judgments are
NUMERIC scores named for the mode: **1 means failure present**. A deterministic
score ID identifies each note, review status, or trace/mode pair. Synchronous
API writes update the same score on edits and retries. Unrelated scores are
untouched.

`analysis/state/review_workspace.json` stores the local workflow snapshot,
revision history and pending write queue. It is written atomically before
network calls. The app also maintains the homework mirrors:

- `annotations.json`, `patterns.json`, `suggestions.json`
- `sample_manifest.json`
- `label_proposals.json` (unconfirmed evidence and proposed values, separate from labels)
- `labels/<mode>.jsonl`

Existing unrelated per-mode label records are preserved. Starter demo labels
are not imported into this review workspace. A missing file gets an empty
default; malformed human state causes an error rather than being overwritten.
These files are created only when a reviewer saves something. Commit the
workspace snapshot alongside the required mirrors to retain recovery history.

The status bar distinguishes pending writes from confirmed Langfuse writes.
**Retry sync** resumes pending writes. A network failure never silently switches
the trace source. Stale browser revisions are rejected; refresh state before
resubmitting the retained draft. This is a single-reviewer application: edit
judgments through it, rather than concurrently editing scores in Langfuse or
the mirror files. Direct external score changes are not automatically merged.

## Agent suggestions API

Read `GET /api/state` for the current revision, then send JSON to
`POST /api/suggestions`:

```json
{
  "revision": 0,
  "items": [{
    "id": "unique-proposal-id",
    "trace_id": "an-existing-trace-id",
    "source": "Workshop run identifier or documented search method",
    "text": "A hypothesis for the human to inspect",
    "quote": "Optional recorded evidence"
  }]
}
```

Use the actual revision and trace IDs. This example is not a saved suggestion.
Use **Refresh state** in the browser to see additions. Do not overwrite local
mirror files while the server is running. Every POST checks the revision;
HTTP 409 means the caller must reload state before trying again.

Reviewed suggestions have an **Edit decision** form for changing the response
or switching between accepted and rejected. **Save changes** retains the prior
decision under **Previous decisions**. The API uses `POST /api/suggestion` with
`revise: true` for this explicit revision, plus the current workspace revision.
If acceptance created a note, edits update that same note and Langfuse score;
reversing acceptance records an explicit rejection note and keeps its history.
Trace review outcomes and binary labels are not automatically changed.

## Offline and tests

Normal homework review uses live Langfuse. An explicit offline demonstration
requires both a source and a recorded reason:

```sh
uv run python -m analysis.review_app.server \
  --offline-export traces/support_traces.json \
  --offline-reason 'Langfuse temporarily unavailable; explain the incident here'
```

Record an actual outage reason in `analysis/report/interface_comparison.md`.
Offline saves stay pending. Restart against live Langfuse with the same state
directory and use **Retry sync** when service returns.

For isolated UI verification, supply `--state-dir /tmp/hw4-review-test` and a
different port along with an offline fixture. Those annotations are test data,
not homework review decisions, and must not be synchronized or committed.

```sh
uv run pytest analysis/review_app/tests -q
uv run pytest tests/test_normalization_metadata.py tests/test_langfuse_export.py \
  tests/test_hw_holes.py -k 'm2 or normalization or langfuse' -q
```

The tests use temporary files and a fake score API. They cover session/retry
separation, missing outputs, pending-write recovery, stable score IDs, stale
browser revisions, evidence ownership, definition history, suggestion
decisions and the four disjoint sampling batches. They make no model calls.
