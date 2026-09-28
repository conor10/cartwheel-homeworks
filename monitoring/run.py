"""HW7 period sampling. Default: preview only; --approve-paid-run calls the judge.

Run from the repository root. Local plans and verdicts default to ignored
.harbor/hw7/monitoring; they include conversation evidence and are not exports
for committing. --publish writes scores, history and the Part C chart.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from analysis.helpers.normalization import _metadata, normalize_trace
from analysis.run_judges import conversation_input
from monitoring.run_judges import judge_sample, judge_test_data, load_monitoring_judge
from monitoring.correct import corrected_mode_prevalence
from monitoring.write_scores import build_score_records, post_scores
from monitoring.chart import prevalence_chart
from monitoring.sample import DEFAULT_RISK_GROUPS, select_traces
from observability.instrument import load_env
from scenarios.export_langfuse import _attribute_scenario_id, _jsonable
from scenarios.validate import load_jsonl, validate_scenarios

ROOT = Path(__file__).resolve().parents[1]


def timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("period and trace timestamps must include a timezone")
    return parsed


def fetch_traces(client: Any, period: dict, scenario_ids: set[str] | None) -> list[dict]:
    """Read only this time window; hydrate matching trace summaries."""
    start, end = timestamp(period["from"]), timestamp(period["to"])
    if start >= end:
        raise ValueError("period start must precede its end")
    traces = []
    page = 1
    while True:
        batch = client.api.trace.list(
            page=page, limit=100, from_timestamp=start, to_timestamp=end
        ).data
        for summary in batch:
            if scenario_ids is not None and _attribute_scenario_id(summary.metadata) not in scenario_ids:
                continue
            if scenario_ids is None and not _metadata(_jsonable(summary)).get("cartwheel.session_id"):
                continue
            trace = _jsonable(client.api.trace.get(summary.id))
            if start <= timestamp(trace["timestamp"]) < end:
                traces.append(trace)
        if len(batch) < 100:
            return traces
        page += 1


def build_conversations(
    traces: list[dict], scenarios: list[dict], model: str,
    not_judgeable: list[dict] | None = None,
) -> list[dict]:
    """Validate the full period before sampling; reuse the frozen HW5 formatter.

    A missing response is an invalid input for this particular frozen judge.
    Do not synthesize a response, remove the scenario, or merge a later retry.
    Explicitly approved trace/scenario exceptions stay in the population with
    no judge text. All other evidence errors still reject the period.
    """
    expected = {row["id"]: row for row in scenarios}
    if len(scenarios) != 50 or len(expected) != 50:
        raise ValueError("comparison requires exactly 50 unique scenario IDs")
    groups = defaultdict(list)
    seen = set()
    session_scenarios = {}
    for trace in traces:
        scenario = _attribute_scenario_id(trace.get("metadata"))
        if scenario not in expected:
            continue
        if trace["id"] in seen:
            raise ValueError(f"duplicate trace: {trace['id']}")
        seen.add(trace["id"])
        generations = [o for o in trace.get("observations", []) if o.get("type") == "GENERATION"]
        if not generations or any(o.get("model") != model for o in generations):
            raise ValueError(f"{scenario}: missing or different generation model")
        session = _metadata(trace).get("cartwheel.session_id") or trace.get("sessionId")
        if not session:
            raise ValueError(f"{scenario}: missing session ID")
        if session in session_scenarios and session_scenarios[session] != scenario:
            raise ValueError("a session contains multiple scenarios")
        session_scenarios[session] = scenario
        groups[scenario].append(trace)
    missing = expected.keys() - groups.keys()
    if missing:
        raise ValueError(f"period is missing scenario IDs: {', '.join(sorted(missing))}")

    exceptions = {item["trace_id"]: item for item in (not_judgeable or [])}
    if len(exceptions) != len(not_judgeable or []):
        raise ValueError("duplicate not-judgeable exception")
    used_exceptions = set()
    records = []
    errors = []
    # Canonical order makes sampling independent of API pagination order.
    for scenario in sorted(expected):
        turns = sorted(groups[scenario], key=lambda t: (timestamp(t["timestamp"]), t["id"]))
        sessions = defaultdict(list)
        for turn in turns:
            sid = _metadata(turn).get("cartwheel.session_id") or turn.get("sessionId")
            sessions[sid].append(turn)
        if len(sessions) != 1:
            raise ValueError(f"{scenario}: multiple sessions/retries in this period")
        required_turns = 1 + len(expected[scenario].get("followups") or [])
        if len(turns) != required_turns:
            raise ValueError(f"{scenario}: expected {required_turns} turns, found {len(turns)}")
        exception = exceptions.get(turns[-1]["id"])
        reason = None
        text = None
        try:
            normalized = normalize_trace(conversation_input(turns[-1], sessions))
            text = normalized["text"]
        except ValueError as exc:
            if (str(exc) == "Missing final reply" and exception
                    and exception.get("scenario_id") == scenario
                    and exception.get("reason", "").strip()):
                reason = exception["reason"]
                used_exceptions.add(turns[-1]["id"])
            else:
                errors.append(f"{scenario} ({turns[-1]['id']}): {exc}")
                continue
        records.append({
            "id": turns[-1]["id"],
            "scenario_id": scenario,
            "session_id": next(iter(sessions)),
            "trace_ids": [turn["id"] for turn in turns],
            "text": text,
            "judgeable": reason is None,
            "not_judgeable_reason": reason,
            "tools": sorted({o["name"] for t in turns for o in t.get("observations", []) if o.get("type") == "TOOL"}),
            "turn_count": len(turns),
        })
    if errors:
        raise ValueError("Frozen HW5 input validation failed; no scenarios were dropped:\n" + "\n".join(errors))
    if used_exceptions != exceptions.keys():
        raise ValueError("unused or stale not-judgeable exception; review the evidence")
    return records


def build_session_conversations(traces: list[dict], model: str) -> list[dict]:
    """Daily windows group observed turns by session, not scenario/fixture IDs."""
    sessions = defaultdict(list)
    for trace in traces:
        sid = _metadata(trace).get("cartwheel.session_id") or trace.get("sessionId")
        if sid:
            sessions[sid].append(trace)
    records = []
    for sid in sorted(sessions):
        turns = sorted(sessions[sid], key=lambda t: (timestamp(t["timestamp"]), t["id"]))
        if len({t["id"] for t in turns}) != len(turns):
            raise ValueError("duplicate trace in daily window")
        models = {o.get("model") for t in turns for o in t.get("observations", []) if o.get("type") == "GENERATION"}
        if models != {model}:
            continue
        normalized = normalize_trace(conversation_input(turns[-1], {sid: turns}))
        records.append({"id": turns[-1]["id"], "scenario_id": None, "session_id": sid,
                        "trace_ids": [t["id"] for t in turns], "text": normalized["text"],
                        "judgeable": True, "not_judgeable_reason": None,
                        "tools": sorted({o["name"] for t in turns for o in t.get("observations", []) if o.get("type") == "TOOL"}),
                        "turn_count": len(turns)})
    return records


def reusable_verdicts(plan: dict, directory: Path) -> dict[str, int]:
    """Reuse only exact evidence and judge identity; never mix changed inputs."""
    wanted = {r["id"]: r["text"] for r in plan["to_judge"]}
    found = {}
    for path in sorted(directory.glob("*/verdicts.json")):
        prior_plan = json.loads((path.parent / "plan.json").read_text())
        if any(prior_plan[k] != plan[k] for k in ("judge_id", "judge_model", "prompt_sha256")):
            continue
        prior = json.loads(path.read_text())
        digest = hashlib.sha256(json.dumps(prior_plan, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        if prior.get("plan_sha256") != digest:
            raise ValueError("cached verdict provenance mismatch")
        verdicts = {**prior["random_verdicts"], **prior["risk_verdicts"]}
        for record in prior_plan["to_judge"]:
            tid = record["id"]
            if tid in wanted and record["text"] == wanted[tid] and tid in verdicts:
                value = verdicts[tid]
                if type(value) is not int or value not in (0, 1):
                    raise ValueError("cached verdict is not binary")
                if tid in found and found[tid] != value:
                    raise ValueError("conflicting cached verdicts for identical evidence")
                found[tid] = value
    return found


def prepare_plan(config: dict, period: dict, records: list[dict], judge: dict) -> dict:
    names = config["risk_groups"]
    if not names or len(set(names)) != len(names) or any(n not in DEFAULT_RISK_GROUPS for n in names):
        raise ValueError("configure at least one distinct DEFAULT_RISK_GROUPS entry")
    # Sample the complete population first. Never replace an unjudgeable draw.
    selection = select_traces(records, config["random_rate"], {n: DEFAULT_RISK_GROUPS[n] for n in names})
    return {
        "period": period,
        "judge_id": config["judge_id"],
        "judge_model": judge["model"],
        "prompt_sha256": hashlib.sha256(judge["prompt_text"].encode()).hexdigest(),
        "model": config["model"],
        "mode": config["judge_mode"],
        "seed": 7,
        "trace_count": sum(len(r["trace_ids"]) for r in records),
        "conversation_count": len(records),
        "random": [r["id"] for r in selection["random"]],
        "risk_groups": {n: [r["id"] for r in rows] for n, rows in selection["risk_groups"].items()},
        "not_judgeable": [
            {"id": r["id"], "scenario_id": r["scenario_id"],
             "reason": r["not_judgeable_reason"],
             "in_random": r in selection["random"],
             "risk_groups": [n for n, rows in selection["risk_groups"].items() if r in rows]}
            for r in records if not r["judgeable"]
        ],
        "to_judge": [r for r in selection["to_judge"] if r["judgeable"]],
    }


def evaluate_plan(plan: dict, cached: dict | None = None) -> dict:
    # Only allowlisted evidence reaches the supplied frozen wrapper.
    verdicts = dict(cached or {})
    pending = [r for r in plan["to_judge"] if r["id"] not in verdicts]
    if pending:
        verdicts.update(judge_sample(plan["judge_id"], [{"id": r["id"], "text": r["text"]} for r in pending]))
    if set(verdicts) != {r["id"] for r in plan["to_judge"]} or any(type(v) is not int or v not in (0, 1) for v in verdicts.values()):
        raise ValueError("judge did not return one binary verdict per selected conversation")
    risk_ids = dict.fromkeys(tid for ids in plan["risk_groups"].values() for tid in ids)
    return {
        "label_convention": "1 = failure present; 0 = failure absent",
        "not_judgeable": plan.get("not_judgeable", []),
        "random_selected_count": len(plan["random"]),
        "random_judged_count": sum(tid in verdicts for tid in plan["random"]),
        "risk_selected_count": len(risk_ids),
        "risk_judged_count": sum(tid in verdicts for tid in risk_ids),
        "random_verdicts": {tid: verdicts[tid] for tid in plan["random"] if tid in verdicts},
        "risk_verdicts": {tid: verdicts[tid] for tid in risk_ids if tid in verdicts},
        "risk_group_verdicts": {name: {tid: verdicts[tid] for tid in ids if tid in verdicts} for name, ids in plan["risk_groups"].items()},
    }


def summarize_period(plan: dict, result: dict, fingerprint: str) -> dict:
    """Estimate only from observed random verdicts, disclosing missing outcomes."""
    excluded = {r["id"] for r in plan["not_judgeable"]}
    expected_random = set(plan["random"]) - excluded
    expected_risk = {tid for ids in plan["risk_groups"].values() for tid in ids} - excluded
    if (result.get("plan_sha256") != fingerprint
            or set(result["random_verdicts"]) != expected_random
            or set(result["risk_verdicts"]) != expected_risk):
        raise ValueError("saved verdicts do not match this plan")
    for values in (result["random_verdicts"], result["risk_verdicts"]):
        if any(type(v) is not int or v not in (0, 1) for v in values.values()):
            raise ValueError("saved verdicts must be binary")
    if any(result["random_verdicts"][tid] != result["risk_verdicts"][tid]
           for tid in expected_random & expected_risk):
        raise ValueError("overlapping verdicts disagree")
    labels, predictions = judge_test_data(plan["judge_id"])
    estimate = corrected_mode_prevalence(list(result["random_verdicts"].values()), labels, predictions)
    limitations = []
    if plan["not_judgeable"]:
        limitations.append("Missing response excluded without replacement or imputation. Estimate uses observed random outcomes; missingness may bias the comparison and is not covered by the bootstrap interval.")
    denominator = estimate["failure_sensitivity"] + estimate["pass_specificity"] - 1
    if abs(denominator) < .1:
        limitations.append("Frozen judge correction denominator is near zero; corrected estimates are highly unstable.")
    return {"label": plan["period"]["label"], "period": plan["period"],
            "judge_id": plan["judge_id"], "judge_model": plan["judge_model"],
            "model": plan["model"], "mode": plan["mode"], "plan_sha256": fingerprint,
            "trace_count": plan["trace_count"], "conversation_count": plan["conversation_count"],
            "random_sample_count": len(plan["random"]), "random_judged_count": len(expected_random),
            "risk_sample_count": len(expected_risk | (excluded & {tid for ids in plan["risk_groups"].values() for tid in ids})),
            "risk_judged_count": len(expected_risk),
            "risk_group_counts": {n: len(ids) for n, ids in plan["risk_groups"].items()},
            "not_judgeable": plan["not_judgeable"], "limitations": limitations,
            "random_verdicts": result["random_verdicts"], "risk_verdicts": result["risk_verdicts"],
            **estimate}


def save_history(summary: dict, config: dict, directory: Path) -> None:
    """Replace this period in history; a repeat never appends a duplicate."""
    from html import escape
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "history.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []
    rows = [r for r in rows if r["label"] != summary["label"]] + [summary]
    if any(r["judge_id"] != summary["judge_id"] or r["model"] != summary["model"] for r in rows):
        raise ValueError("cannot combine different judges or Cartwheel models in history")
    order = {p["label"]: i for i, p in enumerate(config["periods"])}
    rows.sort(key=lambda r: order[r["label"]])
    temporary = path.with_suffix(".tmp")
    temporary.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    temporary.replace(path)
    points = [dict(r, label=f"{r['label']} (n={r['n_sample']})") for r in rows]
    svg = prevalence_chart(points, config["threshold"], summary["mode"])
    # Keep the supplied chart, adding room for its threshold label and caveats.
    svg = svg.replace('width="720" height="360"', 'width="850" height="420"').replace('viewBox="0 0 720 360"', 'viewBox="0 0 850 420"')
    notes = []
    if any(r["not_judgeable"] for r in rows):
        notes.append("Before: 1 missing response; no replacement. Missingness bias is not in the interval.")
    if any(any("near zero" in text for text in r["limitations"]) for r in rows):
        notes.append("Near-zero judge correction denominator: estimates are highly unstable.")
    svg = svg.replace("</svg>", "\n".join(f'<text x="56" y="{375 + 18*i}" font-size="12">{escape(note)}</text>' for i, note in enumerate(notes)) + "\n</svg>")
    (directory / "prevalence.svg").write_text(svg)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    window = parser.add_mutually_exclusive_group(required=True)
    window.add_argument("--period")
    window.add_argument("--last-hours", type=int)
    parser.add_argument("--max-judge-calls", type=int, default=0,
                        help="Daily paid-call cap; zero means cached results only")
    parser.add_argument("--config", type=Path, default=ROOT / "monitoring/config.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / ".harbor/hw7/monitoring")
    parser.add_argument("--approve-paid-run", action="store_true")
    parser.add_argument("--publish", action="store_true", help="write Langfuse scores and Part C history/chart")
    args = parser.parse_args()
    load_env()
    config = json.loads(args.config.read_text())
    if args.last_hours is not None:
        if args.last_hours <= 0 or args.max_judge_calls < 0:
            parser.error("hours must be positive and call cap nonnegative")
        end = datetime.now(timezone.utc)
        period = {"label": "daily-" + end.strftime("%Y%m%dT%H%M%S"),
                  "from": (end - timedelta(hours=args.last_hours)).isoformat(), "to": end.isoformat()}
    else:
        matches = [p for p in config["periods"] if p["label"] == args.period]
        if len(matches) != 1:
            parser.error("select one unique configured period")
        period = matches[0]
    judge = load_monitoring_judge(config["judge_id"])
    scenarios = load_jsonl(ROOT / "scenarios/monitoring_scenarios.jsonl")
    validate_scenarios(scenarios)
    from langfuse import Langfuse
    client = Langfuse()
    # The SDK shares resources with post_scores/get_client. Keep them alive
    # until publishing completes; Langfuse's atexit handler closes them.
    traces = fetch_traces(client, period, None if args.last_hours else {s["id"] for s in scenarios})
    try:
        records = (build_session_conversations(traces, config["model"]) if args.last_hours else
                   build_conversations(traces, scenarios, config["model"], period.get("not_judgeable")))
        plan = prepare_plan(config, period, records, judge)
    except ValueError as exc:
        parser.exit(1, f"Period rejected before judging: {exc}\n")
    encoded = json.dumps(plan, sort_keys=True, ensure_ascii=False)
    fingerprint = hashlib.sha256(encoded.encode()).hexdigest()
    destination = args.output_dir / fingerprint
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n")
    cached = reusable_verdicts(plan, args.output_dir)
    new_calls = len(plan["to_judge"]) - len(cached)
    print(json.dumps({"period": period["label"], "agent_runs": 0, "judge_model": judge["model"],
        "conversations": len(records), "random_count": len(plan["random"]),
        "risk_counts": {n: len(ids) for n, ids in plan["risk_groups"].items()},
        "random_judgeable_count": len(plan["random"]) - sum(r["in_random"] for r in plan["not_judgeable"]),
        "not_judgeable": plan["not_judgeable"],
        "unique_judge_calls": len(plan["to_judge"]), "cached_verdicts": len(cached), "new_judge_calls": new_calls, "output": str(destination)}, indent=2), flush=True)
    if not records:
        (destination / "summary.json").write_text(json.dumps({"period": period, "status": "no_data", "trace_count": len(traces), "conversation_count": 0, "judge_calls": 0}, indent=2) + "\n")
        print("No eligible conversations; zero judge calls.")
        return
    result_path = destination / "verdicts.json"
    if result_path.exists():
        print("Saved verdicts already exist for this exact plan; no judge calls made.")
    elif new_calls and (not args.approve_paid_run or (args.last_hours and new_calls > args.max_judge_calls)):
        status = "call_cap_exceeded" if args.approve_paid_run else "preview"
        (destination / "summary.json").write_text(json.dumps({"period": period, "status": status, "conversation_count": len(records), "new_judge_calls": new_calls, "judge_calls": 0}, indent=2) + "\n")
        if args.approve_paid_run:
            parser.exit(1, f"Need {new_calls} new judge calls; exceeds the approved daily cap of {args.max_judge_calls}. No calls made.\n")
        print("Preview only. Review the call count before using --approve-paid-run.")
        return
    else:
        result = evaluate_plan(plan, cached)
        result["plan_sha256"] = fingerprint
        temporary = destination / "verdicts.tmp"
        temporary.write_text(json.dumps(result, indent=2) + "\n")
        temporary.replace(result_path)
        print(f"Separate random and risk verdicts saved: {result_path}")
    result = json.loads(result_path.read_text())
    summary = summarize_period(plan, result, fingerprint)
    summary["threshold"] = config["threshold"]
    scores = build_score_records(plan["mode"], result["random_verdicts"], result["risk_verdicts"], summary, period["label"])
    if summary["limitations"]:
        scores[-1]["comment"] += "; " + " ".join(summary["limitations"])
    (destination / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (destination / "scores.json").write_text(json.dumps(scores, indent=2) + "\n")
    if args.publish:
        count = post_scores(scores)
        if args.last_hours:
            save_history(summary, {**config, "periods": [period]}, destination)
        else:
            save_history(summary, config, args.config.parent)
        print(f"Posted {count} scores using stable IDs; updated history and chart.")
    print(json.dumps({k: summary[k] for k in ("label", "raw", "corrected", "ci_low", "ci_high", "n_sample", "limitations")}, indent=2))


if __name__ == "__main__":
    main()
