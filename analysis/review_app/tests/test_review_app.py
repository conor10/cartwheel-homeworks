"""Offline regression checks. All writes use temporary state and a fake score API."""

import json
from types import SimpleNamespace

import pytest

from analysis.review_app.state import Conflict, Workspace
from analysis.review_app.traces import TraceStore, present


class Scores:
    def __init__(self):
        self.calls, self.records, self.fail = [], {}, False

    def create(self, request):
        self.calls.append(request)
        if self.fail:
            raise ConnectionError("Test failure")
        self.records[request.id] = request


@pytest.fixture
def setup(tmp_path):
    scenarios, traces = [], []
    for i in range(110):
        sid, tid = f"support-{i:04}", f"{i:032x}"
        scenarios.append({"id": sid, "tuple": {"intent": "order_status"}, "scenario_group": "coverage"})
        traces.append({"id": tid, "timestamp": f"2026-09-15T12:{i//60:02}:{i%60:02}Z",
            "metadata": {"attributes": {"cartwheel.scenario_id": sid, "cartwheel.session_id": f"session-{i}",
                                      "cartwheel.user_role": ["shopper", "merchant", "support"][i%3]}},
            "input": f"Question {i}", "output": "Recorded answer", "observations": [
                {"id": f"span-{i}", "type": "GENERATION", "name": "model", "startTime": "2026-09-15T12:00:01Z",
                 "output": [{"parts": [{"type": "text", "content": "Recorded answer"}]}]}]})
    scenarios_path = tmp_path / "scenarios.jsonl"
    scenarios_path.write_text("\n".join(json.dumps(s) for s in scenarios))
    export = tmp_path / "export.json"
    export.write_text(json.dumps({"traces": traces}))
    store = TraceStore(None, scenarios_path, "http://localhost:3000", export)
    scores = Scores()
    workspace = Workspace(tmp_path / "state", SimpleNamespace(api=SimpleNamespace(score=scores)))
    return store, workspace, scores


def change(workspace, store, action, **body):
    return workspace.mutate(action, {"revision": workspace.data["revision"], **body}, store)


def make_mode(store, workspace):
    tid = store.summaries()[0]["id"]
    change(workspace, store, "note", id="human-note", trace_id=tid, note="The reply claims completion before confirmation.")
    change(workspace, store, "review", trace_id=tid, status="first_failure", annotation_id="human-note")
    change(workspace, store, "mode", name="unconfirmed_write", definition="Claims success without confirmation",
           boundary="Not an accurate pending-status reply", requirement="RESP-2", evaluator_type="llm_judge",
           created_from=["human-note"], status="final")
    return tid


def test_sessions_keep_followups_together_and_retry_separate(setup):
    store, _, _ = setup
    rows = store.summaries()
    a, b, retry = [r["id"] for r in rows[:3]]
    store.index[b]["session_id"] = store.index[a]["session_id"]
    store.index[retry]["scenario_id"] = store.index[a]["scenario_id"]
    session = store.session(a)
    assert [t["id"] for t in session] == [a, b]
    assert [t["id"] for t in store.session(retry)] == [retry]
    assert session[0]["spans"][0]["id"] == "span-0"
    assert session[0]["extra_output"] == ""  # Final model text is shown once.


def test_missing_session_does_not_merge_unrelated_traces(setup):
    store, _, _ = setup
    record = store.raw(store.summaries()[0]["id"])
    from analysis.review_app.traces import describe
    del record["metadata"]["attributes"]["cartwheel.session_id"]
    assert describe(record, store.scenarios, store.host)["session_id"] == record["id"]
    assert describe(record, store.scenarios, store.host)["session_missing"]


def test_failed_execution_retains_error_and_no_fake_answer(setup):
    store, _, _ = setup
    row = store.summaries()[0]
    raw = {**store.raw(row["id"]), "output": None,
           "observations": [{"id": "failed", "type": "AGENT", "level": "ERROR", "statusMessage": "MaxTurnsExceeded"}]}
    result = present(raw, row)
    assert result["missing_output"] and not result["extra_output"]
    assert result["spans"][0]["error"] == "MaxTurnsExceeded"


def test_pending_save_survives_restart_and_sync_is_idempotent(setup):
    store, workspace, scores = setup
    tid = store.summaries()[0]["id"]
    scores.fail = True
    change(workspace, store, "note", id="note-one", trace_id=tid, note="Original observation", observation_id="span-0")
    assert workspace.data["outbox"]["note:note-one"]["status"] == "pending"
    reloaded = Workspace(workspace.directory, workspace.client)
    assert reloaded.data["annotations"][0]["note"] == "Original observation"
    scores.fail = False
    change(reloaded, store, "sync")
    change(reloaded, store, "sync")
    change(reloaded, store, "note", id="note-one", trace_id=tid, note="Refined observation", observation_id="span-0")
    assert len(scores.records) == 1
    assert len(scores.calls) == 3  # failed, retried, revised; no resend of synced state
    assert reloaded.data["annotations"][0]["history"][0]["note"] == "Original observation"
    assert next(iter(scores.records.values())).trace_id == tid


def test_stale_browser_cannot_overwrite_new_notes(setup):
    store, workspace, _ = setup
    tid = store.summaries()[0]["id"]
    change(workspace, store, "note", trace_id=tid, note="Keep this")
    with pytest.raises(Conflict):
        workspace.mutate("note", {"revision": 0, "trace_id": tid, "note": "Stale"}, store)
    assert len(workspace.data["annotations"]) == 1


def test_unknown_observation_and_unreviewed_labels_are_rejected(setup):
    store, workspace, _ = setup
    tid = store.summaries()[0]["id"]
    with pytest.raises(ValueError, match="Observation"):
        change(workspace, store, "note", trace_id=tid, note="Wrong span", observation_id="span-1")
    make_mode(store, workspace)
    with pytest.raises(ValueError, match="open coding"):
        change(workspace, store, "label", trace_id=store.summaries()[1]["id"], mode="unconfirmed_write", label=1, note="Premature")


def test_labels_update_same_score_and_preserve_other_label_records(setup):
    store, workspace, scores = setup
    tid = make_mode(store, workspace)
    path = workspace.directory / "labels/unconfirmed_write.jsonl"
    path.parent.mkdir()
    path.write_text(json.dumps({"trace_id": "starter-example", "label": 0}) + "\n")
    change(workspace, store, "label", trace_id=tid, mode="unconfirmed_write", label=1, note="Evidence A")
    score = workspace.data["labels"][tid + ":unconfirmed_write"]["score_id"]
    change(workspace, store, "label", trace_id=tid, mode="unconfirmed_write", label=0, note="Revised after checking the previous turn", close_negative=True)
    labels = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(labels) == 2 and labels[0]["trace_id"] == "starter-example"
    assert labels[1]["score_id"] == score and labels[1]["label"] == 0
    assert labels[1]["history"][0]["label"] == 1
    assert scores.records[score].value == 0


def test_definition_revision_keeps_labels_but_marks_version_stale(setup):
    store, workspace, _ = setup
    tid = make_mode(store, workspace)
    change(workspace, store, "label", trace_id=tid, mode="unconfirmed_write", label=1, note="Evidence")
    mode = workspace.data["modes"][0]
    change(workspace, store, "mode", **{**mode, "definition": "A refined binary rule", "revision_reason": "Clarify the boundary"})
    assert workspace.data["modes"][0]["version"] == 2
    assert workspace.data["labels"][tid + ":unconfirmed_write"]["mode_version"] == 1
    assert workspace.data["modes"][0]["history"][0]["definition"] == "Claims success without confirmation"


def test_suggestion_decision_is_preserved_and_does_not_assign_a_label(setup):
    store, workspace, _ = setup
    tid = store.summaries()[0]["id"]
    change(workspace, store, "suggestions", items=[{"id": "suggestion-1", "trace_id": tid, "text": "A hypothesis", "source": "Workshop"}])
    change(workspace, store, "suggestion", id="suggestion-1", decision="accepted", reason="My revised observation")
    assert workspace.data["annotations"][0]["source"] == "accepted_suggestion"
    assert not workspace.data["labels"] and not workspace.data["reviews"]
    with pytest.raises(ValueError, match="already decided"):
        change(workspace, store, "suggestion", id="suggestion-1", decision="rejected", reason="Overwrite")


def test_suggestion_revisions_update_one_note_and_keep_decision_history(setup):
    store, workspace, scores = setup
    tid = store.summaries()[0]["id"]
    change(workspace, store, "suggestions", items=[{
        "id": "s1", "trace_id": tid, "text": "Candidate", "source": "Search"}])
    change(workspace, store, "suggestion", id="s1", decision="accepted", reason="Original")
    aid = workspace.data["suggestions"][0]["annotation_id"]
    score_id = workspace.data["outbox"]["note:" + aid]["id"]
    for decision, reason in [("accepted", "More precise"), ("rejected", "Calls were justified"),
                             ("rejected", "Clarified rejection"), ("accepted", "One call was redundant")]:
        change(workspace, store, "suggestion", id="s1", decision=decision, reason=reason, revise=True)
        note = workspace.data["annotations"][0]
        assert len(workspace.data["annotations"]) == len(scores.records) == 1
        assert note["id"] == aid
        assert note["source"] == decision + "_suggestion"
        assert note["note"] == (reason if decision == "accepted" else "Suggestion rejected: " + reason)
        assert json.loads(scores.records[score_id].comment)["note"] == note["note"]
    reloaded = Workspace(workspace.directory, workspace.client)
    suggestion = reloaded.data["suggestions"][0]
    assert [h["decision_reason"] for h in suggestion["history"]] == [
        "Original", "More precise", "Calls were justified", "Clarified rejection"]
    assert len(reloaded.data["annotations"][0]["history"]) == 4
    assert not reloaded.data["labels"] and not reloaded.data["reviews"]


def test_rejected_suggestion_can_be_edited_without_creating_a_note(setup):
    store, workspace, _ = setup
    tid = store.summaries()[0]["id"]
    change(workspace, store, "suggestions", items=[{
        "id": "s1", "trace_id": tid, "text": "Candidate", "source": "Search"}])
    change(workspace, store, "suggestion", id="s1", decision="rejected", reason="No failure")
    before = workspace.snapshot()
    with pytest.raises(ValueError, match="reason"):
        change(workspace, store, "suggestion", id="s1", decision="accepted", reason=" ", revise=True)
    assert workspace.snapshot() == before
    with pytest.raises(Conflict):
        workspace.mutate("suggestion", {"revision": 0, "id": "s1", "decision": "accepted",
                                       "reason": "Stale edit", "revise": True}, store)
    change(workspace, store, "suggestion", id="s1", decision="rejected", reason="Needed for verification", revise=True)
    assert not workspace.data["annotations"] and not workspace.data["outbox"]
    change(workspace, store, "suggestion", id="s1", decision="accepted", reason="Found the redundant call", revise=True)
    assert len(workspace.data["annotations"]) == 1
    assert workspace.data["suggestions"][0]["history"][0]["decision_reason"] == "No failure"


def test_label_proposals_remain_separate_until_explicit_confirmation(setup):
    store, workspace, scores = setup
    tid = make_mode(store, workspace)
    workspace.data["manifest"]["picks"] = [{"trace_id": tid, "batch": "depth"}]
    before_scores = len(scores.records)
    proposal = {"trace_id": tid, "mode": "unconfirmed_write", "mode_version": 1,
                "label": None, "note": "Needs human resolution", "source": "human"}
    change(workspace, store, "label_proposals", items=[proposal])
    assert not workspace.data["labels"] and len(scores.records) == before_scores
    p = workspace.data["label_proposals"][tid + ":unconfirmed_write"]
    assert p["source"] == "agent_proposal" and p["label"] is None
    assert not (workspace.directory / "labels").exists()
    confirmed = {**proposal, "label": 1, "note": "I checked the pending result against the success claim"}
    change(workspace, store, "label_batch", items=[confirmed])
    assert workspace.data["labels"][tid + ":unconfirmed_write"]["source"] == "human"
    assert len(scores.records) == before_scores + 1
    assert p["label"] is None  # Original proposal is retained separately.


def test_label_batch_is_atomic_and_rejects_unknown_or_stale_judgments(setup):
    store, workspace, scores = setup
    tid = make_mode(store, workspace)
    item = {"trace_id": tid, "mode": "unconfirmed_write", "mode_version": 1,
            "label": 1, "note": "Confirmed evidence"}
    before, score_count = workspace.snapshot(), len(scores.calls)
    for items in ([item, {**item, "trace_id": "missing"}],
                  [{**item, "mode_version": 0}], [item, item], [{**item, "label": None}]):
        with pytest.raises(ValueError):
            change(workspace, store, "label_batch", items=items)
        assert workspace.snapshot() == before
        assert len(scores.calls) == score_count


def test_all_four_sampling_batches_are_disjoint_and_reproducible(setup, tmp_path):
    store, workspace, _ = setup
    change(workspace, store, "sample", stage="initial", dimension="role")
    again = Workspace(tmp_path / "repeat")
    change(again, store, "sample", stage="initial", dimension="role")
    assert workspace.data["manifest"]["picks"] == again.data["manifest"]["picks"]
    picks = workspace.data["manifest"]["picks"]
    assert sum(p["batch"] == "initial_random" for p in picks) == 15
    assert sum(p["batch"] == "initial_cluster" for p in picks) == 15
    change(workspace, store, "sample", stage="dimension")
    picked = {p["trace_id"] for p in workspace.data["manifest"]["picks"]}
    depth = [r["id"] for r in store.summaries() if r["id"] not in picked][:25]
    change(workspace, store, "sample", stage="depth", trace_ids=depth, reason="Human-selected candidates and close negatives")
    with pytest.raises(ValueError, match="draft"):
        change(workspace, store, "sample", stage="final")
    change(workspace, store, "mode", name="draft_mode", definition="Candidate binary rule")
    for pick in workspace.data["manifest"]["picks"]:
        workspace.data["reviews"][pick["trace_id"]] = {"status": "no_failure_observed"}
    change(workspace, store, "sample", stage="final")
    picks = workspace.data["manifest"]["picks"]
    assert len(picks) == len({p["trace_id"] for p in picks}) == 100
    assert workspace.data["manifest"]["dimension"] == "role"


def test_depth_removal_preserves_work_and_allows_replacements(setup):
    store, workspace, _ = setup
    change(workspace, store, "sample", stage="initial", dimension="role")
    initial = workspace.snapshot()["manifest"]["picks"]
    selected = {p["trace_id"] for p in initial}
    depth = [r["id"] for r in store.summaries() if r["id"] not in selected][:25]
    change(workspace, store, "sample", stage="depth", trace_ids=depth, reason="Search candidates")
    change(workspace, store, "note", trace_id=depth[0], note="Keep my observation")
    change(workspace, store, "review", trace_id=depth[0], status="no_failure_observed")
    before = workspace.snapshot()
    change(workspace, store, "sample", stage="depth_remove", trace_ids=depth[:20], reason="Accidental selection")
    saved = Workspace(workspace.directory).snapshot()
    assert saved["manifest"]["picks"][:30] == initial
    assert [p["trace_id"] for p in saved["manifest"]["picks"] if p["batch"] == "depth"] == depth[20:]
    for key in ("annotations", "reviews", "labels", "outbox"):
        assert saved[key] == before[key]
    removal = saved["manifest"]["removals"][0]
    assert removal["reason"] == "Accidental selection"
    assert [p["trace_id"] for p in removal["picks"]] == depth[:20]
    assert all(p["reason"] == "Search candidates" for p in removal["picks"])
    change(workspace, store, "sample", stage="depth", trace_ids=depth[:20], reason="Rechecked selection")
    assert len(workspace.data["manifest"]["picks"]) == 55


def test_depth_removal_rejects_other_batches_and_invalid_requests(setup):
    store, workspace, _ = setup
    change(workspace, store, "sample", stage="initial", dimension="role")
    initial = workspace.data["manifest"]["picks"][0]["trace_id"]
    selected = {p["trace_id"] for p in workspace.data["manifest"]["picks"]}
    tid = next(r["id"] for r in store.summaries() if r["id"] not in selected)
    change(workspace, store, "sample", stage="depth", trace_ids=[tid], reason="Search candidate")
    before = workspace.snapshot()
    for ids, reason in [([initial], "Mistake"), ([tid, initial], "Mistake"),
                        ([tid, tid], "Mistake"), (["unknown"], "Mistake"),
                        ([], "Mistake"), ([tid], "")]:
        with pytest.raises(ValueError):
            change(workspace, store, "sample", stage="depth_remove", trace_ids=ids, reason=reason)
        assert workspace.snapshot() == before


def test_bad_request_rolls_back_every_in_memory_change(setup):
    store, workspace, _ = setup
    tid = store.summaries()[0]["id"]
    with pytest.raises(ValueError):
        change(workspace, store, "suggestions", items=[
            {"id": "valid", "trace_id": tid, "text": "Keep out until whole request succeeds", "source": "search"},
            {"id": "invalid", "trace_id": "unknown", "text": "Invalid", "source": "search"}])
    assert not workspace.data["suggestions"] and workspace.data["revision"] == 0


def test_corrupt_human_state_is_not_silently_replaced(tmp_path):
    (tmp_path / "annotations.json").write_text("{broken")
    with pytest.raises(json.JSONDecodeError):
        Workspace(tmp_path)
    assert (tmp_path / "annotations.json").read_text() == "{broken"


def test_http_rejects_cross_origin_and_nonlocal_hosts_before_saving(setup):
    from email.message import Message
    from io import BytesIO
    from analysis.review_app.server import make_handler

    store, workspace, _ = setup
    handler_class = make_handler(store, workspace)
    for host, origin in [("localhost:8022", "https://unrelated.example"), ("unrelated.example:8022", None)]:
        handler = object.__new__(handler_class)
        handler.headers = Message()
        handler.headers["Host"] = host
        if origin:
            handler.headers["Origin"] = origin
        handler.path = "/api/note"
        handler.rfile = BytesIO(b'{}')
        response = []
        handler.send = lambda body, status=200: response.append((body, status))
        handler.do_POST()
        assert response[0][1] == 403
    assert workspace.data["revision"] == 0


def test_http_returns_conflict_and_json_save_response(setup):
    from email.message import Message
    from io import BytesIO
    from analysis.review_app.server import make_handler

    store, workspace, _ = setup
    handler_class = make_handler(store, workspace)
    for expected in (200, 409):
        handler = object.__new__(handler_class)
        body = json.dumps({"revision": 0, "trace_id": store.summaries()[0]["id"], "note": "Transport test"}).encode()
        handler.headers = Message()
        handler.headers["Host"] = "localhost:8022"
        handler.headers["Origin"] = "http://localhost:8022"
        handler.headers["Content-Type"] = "application/json"
        handler.headers["Content-Length"] = str(len(body))
        handler.path, handler.rfile = "/api/note", BytesIO(body)
        response = []
        handler.send = lambda body, status=200: response.append((body, status))
        handler.do_POST()
        assert response[0][1] == expected
    assert len(workspace.data["annotations"]) == 1
