"""Offline safety and evidence tests for HW7 Part B."""
import copy
import random

import pytest

from analysis.helpers.normalization import normalize_trace
from analysis.run_judges import conversation_input
from monitoring import run
from monitoring.sample import select_traces


@pytest.fixture
def period_data():
    scenarios = [{"id": f"s-{i:02}", "followups": []} for i in range(50)]
    traces = [{
        "id": f"t-{i:02}", "timestamp": "2026-09-28T12:00:00Z",
        "metadata": {"attributes": {"cartwheel.scenario_id": s["id"], "cartwheel.session_id": f"session-{i}"}},
        "input": "What is the policy?", "output": "The response.",
        "observations": [{"id": f"g-{i}", "type": "GENERATION", "model": "test-model", "input": "SECRET SYSTEM", "output": "private narration"}],
        "scores": [{"value": 1, "comment": "human verdict"}],
    } for i, s in enumerate(scenarios)]
    return scenarios, traces


def test_sampling_uniform_overlap_and_empty():
    rows = [{"id": str(i)} for i in range(50)]
    original = copy.deepcopy(rows)
    plan = select_traces(rows, .2, {"all": lambda t: True, "also": lambda t: True})
    assert plan["random"] == random.Random(7).sample(rows, 10)
    assert len(plan["to_judge"]) == 50
    assert plan["to_judge"][:10] == plan["random"]
    assert rows == original
    assert select_traces([], .2, {}) == {"random": [], "risk_groups": {}, "to_judge": []}
    for rate in [0, -1, 1.1, float("nan")]:
        with pytest.raises(ValueError):
            select_traces(rows, rate, {})
    with pytest.raises(ValueError):
        select_traces([{}], .2, {})


def test_conversation_uses_exact_hw5_evidence_and_final_id(period_data):
    scenarios, traces = period_data
    first = traces[0]
    first["observations"].append({"id": "tool1", "type": "TOOL", "name": "get_policy", "startTime": first["timestamp"], "input": {"policy": "cw-returns"}, "output": "Retrieved evidence"})
    second = copy.deepcopy(first)
    second.update(id="t-final", timestamp="2026-09-28T12:01:00Z", input="And then?", output="Final response.", observations=[first["observations"][0]])
    scenarios[0]["followups"] = ["And then?"]
    traces.append(second)
    records = run.build_conversations(list(reversed(traces)), scenarios, "test-model")
    record = records[0]
    frozen = normalize_trace(conversation_input(second, {"session-0": [first, second]}))
    assert record["id"] == "t-final"
    assert record["text"] == frozen["text"]
    assert record["turn_count"] == 2
    assert record["tools"] == ["get_policy"]
    assert "Retrieved evidence" in record["text"]
    for excluded in ["SECRET SYSTEM", "private narration", "human verdict", "s-00", "session-0"]:
        assert excluded not in record["text"]
    assert records == run.build_conversations(traces, scenarios, "test-model")


@pytest.mark.parametrize("damage, message", [
    ("missing", "missing scenario"), ("model", "different generation model"),
    ("reply", "Missing final reply"), ("retry", "multiple sessions/retries"),
    ("duplicate", "duplicate trace"), ("turns", "expected 1 turns"),
])
def test_rejects_invalid_period_before_sampling(period_data, damage, message):
    scenarios, traces = period_data
    if damage == "missing": traces.pop()
    elif damage == "model": traces[0]["observations"][0]["model"] = "wrong"
    elif damage == "reply": traces[0]["output"] = None
    elif damage == "duplicate": traces.append(copy.deepcopy(traces[0]))
    else:
        extra = copy.deepcopy(traces[0]); extra["id"] = "extra"
        if damage == "retry": extra["metadata"]["attributes"]["cartwheel.session_id"] = "retry"
        traces.append(extra)
    with pytest.raises(ValueError, match=message):
        run.build_conversations(traces, scenarios, "test-model")


def test_union_judged_once_with_separate_memberships(monkeypatch):
    calls = []
    def judge(judge_id, rows):
        calls.append(rows)
        assert judge_id == "frozen"
        assert rows == [{"id": "a", "text": "evidence a"}, {"id": "b", "text": "evidence b"}]
        return {"a": 1, "b": 0}
    monkeypatch.setattr(run, "judge_sample", judge)
    result = run.evaluate_plan({"judge_id": "frozen", "random": ["a"], "risk_groups": {"policy": ["a", "b"], "other": ["a"]}, "to_judge": [{"id": "a", "text": "evidence a", "scenario_id": "excluded"}, {"id": "b", "text": "evidence b"}]})
    assert len(calls) == 1
    assert result["random_verdicts"] == {"a": 1}
    assert result["risk_verdicts"] == {"a": 1, "b": 0}
    assert result["risk_group_verdicts"]["other"] == {"a": 1}


def test_approved_missing_reply_stays_in_sample_without_verdict(period_data, monkeypatch):
    scenarios, traces = period_data
    selected_index = random.Random(7).sample(range(50), 10)[0]
    target = traces[selected_index]
    target["output"] = None
    target["observations"].append({"id": "lookup", "type": "TOOL", "name": "get_policy"})
    exception = {"trace_id": target["id"], "scenario_id": scenarios[selected_index]["id"], "reason": "Approved missing reply exception"}
    records = run.build_conversations(traces, scenarios, "test-model", [exception])
    assert len(records) == 50
    config = {"risk_groups": ["policy_lookup"], "random_rate": .2, "judge_id": "frozen", "judge_mode": "detail", "model": "test-model"}
    plan = run.prepare_plan(config, {"label": "before"}, records, {"model": "judge", "prompt_text": "frozen"})
    assert len(plan["random"]) == 10
    assert plan["random"] == [r["id"] for r in random.Random(7).sample(records, 10)]
    assert target["id"] in plan["random"]
    assert target["id"] in plan["risk_groups"]["policy_lookup"]
    assert target["id"] not in {r["id"] for r in plan["to_judge"]}
    assert plan["not_judgeable"][0]["in_random"] is True
    assert plan["not_judgeable"][0]["risk_groups"] == ["policy_lookup"]
    monkeypatch.setattr(run, "judge_sample", lambda _, rows: {r["id"]: 0 for r in rows})
    result = run.evaluate_plan(plan)
    assert result["random_selected_count"] == 10
    assert result["random_judged_count"] == 9
    assert target["id"] not in result["random_verdicts"]
    assert result["risk_selected_count"] == 1
    assert result["risk_judged_count"] == 0
    assert result["not_judgeable"] == plan["not_judgeable"]


@pytest.mark.parametrize("damage", ["stale", "wrong_scenario", "wrong_trace", "missing_user"])
def test_exception_does_not_bypass_other_evidence_errors(period_data, damage):
    scenarios, traces = period_data
    exception = {"trace_id": traces[0]["id"], "scenario_id": scenarios[0]["id"], "reason": "Approved"}
    if damage != "stale":
        traces[0]["output"] = None
    if damage == "wrong_scenario": exception["scenario_id"] = "another"
    if damage == "wrong_trace": exception["trace_id"] = "another"
    if damage == "missing_user": traces[0]["input"] = None
    with pytest.raises(ValueError):
        run.build_conversations(traces, scenarios, "test-model", [exception])


@pytest.mark.parametrize("sample,labels,preds", [
    ([], [0, 1], [0, 1]), ([2], [0, 1], [0, 1]),
    ([0], [0], [0]), ([0], [0, 1], [0]),
    ([0], [0, 1], [1, 1]),
])
def test_correction_rejects_unusable_inputs(sample, labels, preds):
    from monitoring.correct import corrected_mode_prevalence
    with pytest.raises(ValueError):
        corrected_mode_prevalence(sample, labels, preds, bootstrap_iterations=10)


def test_perfect_judge_correction_and_clipping():
    from monitoring.correct import corrected_mode_prevalence
    estimate = corrected_mode_prevalence([1, 0, 0, 0], [0, 1]*10, [0, 1]*10, bootstrap_iterations=500)
    assert estimate["raw"] == estimate["corrected"] == .25
    assert estimate["failure_sensitivity"] == estimate["pass_specificity"] == 1
    assert estimate["ci_low"] <= .25 <= estimate["ci_high"]
    estimate = corrected_mode_prevalence([0]*10, [0]*10+[1]*10, [0]*8+[1]*2+[1]*8+[0]*2, bootstrap_iterations=100)
    assert estimate["corrected"] == 0


def test_summary_uses_random_only_and_history_is_repeatable(tmp_path, monkeypatch):
    monkeypatch.setattr(run, "judge_test_data", lambda _: ([0, 1]*10, [0, 1]*10))
    plan = {"period": {"label": "before"}, "judge_id": "frozen", "judge_model": "judge", "model": "agent", "mode": "detail", "trace_count": 74, "conversation_count": 50,
            "random": ["a", "b", "missing"], "risk_groups": {"policy": ["a", "c", "missing"]},
            "not_judgeable": [{"id": "missing", "reason": "No final reply"}]}
    result = {"plan_sha256": "hash", "random_verdicts": {"a": 0, "b": 0}, "risk_verdicts": {"a": 0, "c": 1}}
    summary = run.summarize_period(plan, result, "hash")
    assert summary["raw"] == 0
    assert summary["n_sample"] == 2
    assert summary["random_sample_count"] == 3
    assert summary["random_judged_count"] == 2
    assert summary["risk_sample_count"] == 3
    assert summary["risk_judged_count"] == 2
    assert summary["limitations"]
    config = {"periods": [{"label": "before"}], "threshold": .15}
    run.save_history(summary, config, tmp_path)
    original = (tmp_path / "history.jsonl").read_text()
    run.save_history(summary, config, tmp_path)
    assert (tmp_path / "history.jsonl").read_text() == original
    assert len(original.splitlines()) == 1
    assert "Missingness bias" in (tmp_path / "prevalence.svg").read_text()
    result["random_verdicts"]["missing"] = 0
    with pytest.raises(ValueError):
        run.summarize_period(plan, result, "hash")


def test_score_publisher_targets_batch_and_propagates_errors(monkeypatch):
    from types import SimpleNamespace
    import langfuse
    from analysis.helpers import langfuse_io
    from monitoring.write_scores import post_scores
    requests = []
    client = SimpleNamespace(api=SimpleNamespace(score=SimpleNamespace(create=lambda *, request: requests.append(request))))
    monkeypatch.setattr(langfuse, "get_client", lambda: client)
    monkeypatch.setattr(langfuse_io, "is_configured", lambda: True)
    records = [{"score_id": "stable", "name": "mode_prevalence", "value": .2, "data_type": "NUMERIC", "trace_id": None, "comment": "limitations"}]
    assert post_scores(records) == 1
    assert requests[0].id == "stable"
    assert requests[0].session_id == "monitoring-stable"
    assert requests[0].trace_id is None
    def reject(**kwargs):
        raise RuntimeError("rejected")
    client.api.score.create = reject
    with pytest.raises(RuntimeError, match="rejected"):
        post_scores(records)


def test_daily_groups_by_session_not_scenario(period_data):
    _, traces = period_data
    first, second = copy.deepcopy(traces[:2])
    second['metadata'] = copy.deepcopy(first['metadata'])
    second['timestamp'] = '2026-09-28T12:01:00Z'
    first['metadata']['attributes'].pop('cartwheel.scenario_id')
    second['metadata']['attributes'].pop('cartwheel.scenario_id')
    records = run.build_session_conversations([second, first], 'test-model')
    assert len(records) == 1
    assert records[0]['id'] == second['id']
    assert records[0]['turn_count'] == 2
    assert run.build_session_conversations([first], 'different-model') == []
    assert run.build_session_conversations([], 'test-model') == []


def test_empty_daily_window_exits_without_judge(tmp_path, monkeypatch):
    import json
    import sys
    import langfuse
    config = {'judge_id': 'frozen', 'model': 'test-model', 'judge_mode': 'detail', 'risk_groups': ['policy_lookup'], 'random_rate': .2}
    path = tmp_path / 'config.json'
    path.write_text(json.dumps(config))
    monkeypatch.setattr(sys, 'argv', ['monitor', '--last-hours', '24', '--config', str(path), '--output-dir', str(tmp_path / 'out'), '--approve-paid-run', '--publish'])
    monkeypatch.setattr(langfuse, 'Langfuse', lambda: object())
    monkeypatch.setattr(run, 'fetch_traces', lambda *args: [])
    monkeypatch.setattr(run, 'load_monitoring_judge', lambda _: {'model': 'test-judge', 'prompt_text': 'fixed'})
    def no_calls(*args, **kwargs):
        pytest.fail('No-data windows must not call models or publish scores')
    monkeypatch.setattr(run, 'judge_sample', no_calls)
    monkeypatch.setattr(run, 'post_scores', no_calls)
    run.main()
    summaries = list((tmp_path / 'out').glob('*/summary.json'))
    assert len(summaries) == 1
    summary = json.loads(summaries[0].read_text())
    assert summary['status'] == 'no_data'
    assert summary['conversation_count'] == summary['judge_calls'] == 0


def test_exact_evidence_cache_avoids_new_judging(tmp_path, monkeypatch):
    import hashlib
    import json
    plan = {'judge_id': 'frozen', 'judge_model': 'judge', 'prompt_sha256': 'p', 'to_judge': [{'id': 'a', 'text': 'exact evidence'}], 'random': ['a'], 'risk_groups': {}}
    folder = tmp_path / 'prior'; folder.mkdir()
    (folder / 'plan.json').write_text(json.dumps(plan))
    digest = hashlib.sha256(json.dumps(plan, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    (folder / 'verdicts.json').write_text(json.dumps({'plan_sha256': digest, 'random_verdicts': {'a': 1}, 'risk_verdicts': {}}))
    cached = run.reusable_verdicts(plan, tmp_path)
    assert cached == {'a': 1}
    monkeypatch.setattr(run, 'judge_sample', lambda *args: pytest.fail('cached evidence must not be judged again'))
    assert run.evaluate_plan(plan, cached)['random_verdicts'] == {'a': 1}
    changed = copy.deepcopy(plan); changed['to_judge'][0]['text'] = 'changed'
    assert run.reusable_verdicts(changed, tmp_path) == {}


def test_daily_call_cap_blocks_before_spending(tmp_path, monkeypatch, period_data):
    import json
    import sys
    import langfuse
    _, traces = period_data
    config = {'judge_id': 'frozen', 'model': 'test-model', 'judge_mode': 'detail', 'risk_groups': ['policy_lookup'], 'random_rate': .2}
    path = tmp_path / 'config.json'; path.write_text(json.dumps(config))
    monkeypatch.setattr(sys, 'argv', ['monitor', '--last-hours', '24', '--config', str(path), '--output-dir', str(tmp_path / 'out'), '--approve-paid-run', '--max-judge-calls', '0'])
    monkeypatch.setattr(langfuse, 'Langfuse', lambda: object())
    monkeypatch.setattr(run, 'fetch_traces', lambda *args: traces)
    monkeypatch.setattr(run, 'load_monitoring_judge', lambda _: {'model': 'test-judge', 'prompt_text': 'fixed'})
    monkeypatch.setattr(run, 'judge_sample', lambda *args: pytest.fail('Must stop before a paid call'))
    with pytest.raises(SystemExit) as error:
        run.main()
    assert error.value.code == 1
    summary = json.loads(next((tmp_path / 'out').glob('*/summary.json')).read_text())
    assert summary['status'] == 'call_cap_exceeded'
    assert summary['judge_calls'] == 0
