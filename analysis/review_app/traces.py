"""Live trace loading; display sessions without merging their trace identities."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import RLock
from typing import Any

from analysis.helpers.normalization import _metadata, _text, normalize_trace
from scenarios.export_langfuse import _jsonable


def describe(raw: dict, scenarios: dict, host: str) -> dict:
    meta = _metadata(raw)
    sid = meta.get("cartwheel.scenario_id") or raw.get("cartwheel_scenario_id")
    scenario = scenarios.get(sid, {})
    dimensions = scenario.get("tuple", {})
    tid = raw["id"]
    return {
        "id": tid, "scenario_id": sid,
        "session_id": meta.get("cartwheel.session_id") or raw.get("sessionId") or tid,
        "session_missing": not (meta.get("cartwheel.session_id") or raw.get("sessionId")),
        "timestamp": raw.get("timestamp", ""),
        "role": meta.get("cartwheel.user_role", "unknown"),
        "user_id": meta.get("cartwheel.user_id"),
        "prompt_version": meta.get("cartwheel.prompt_version"),
        "intent": dimensions.get("intent", "unknown"),
        "group": scenario.get("scenario_group", "unknown"),
        "preview": _text(raw.get("input")),
        "url": host.rstrip("/") + str(raw.get("htmlPath") or
            f"/project/{raw.get('projectId', '')}/traces/{tid}"),
    }


def present(raw: dict, summary: dict) -> dict:
    """Expose observed content once, retaining hierarchy, IDs and raw evidence."""
    spans = sorted(raw.get("observations") or [], key=lambda o: (o.get("startTime") or "", o["id"]))
    known = {s["id"]: s for s in spans}
    result = []
    assistant_text = set()
    for span in spans:
        parent = span.get("parentObservationId")
        depth, seen = 0, {span["id"]}
        while parent in known and parent not in seen:
            seen.add(parent)
            depth += 1
            parent = known[parent].get("parentObservationId")
        messages, calls = [], []
        if span.get("type") == "GENERATION" and isinstance(span.get("output"), list):
            for message in span["output"]:
                for part in message.get("parts", []):
                    if part.get("type") == "text" and part.get("content"):
                        messages.append(part["content"])
                        assistant_text.add(part["content"])
                    elif part.get("type") == "tool_call":
                        calls.append(part)
        result.append({
            "id": span["id"], "parent_id": span.get("parentObservationId"), "depth": depth,
            "name": span.get("name"), "type": span.get("type"),
            "start": span.get("startTime"), "end": span.get("endTime"),
            "level": span.get("level"), "error": span.get("statusMessage"),
            "input": span.get("input"), "output": span.get("output"),
            "messages": messages, "calls": calls, "model": span.get("model"),
            "usage": span.get("usageDetails") or span.get("usage"),
            "cost": span.get("calculatedTotalCost"),
        })
    output = _text(raw.get("output"))
    return {**summary, "input": _text(raw.get("input")), "output": output,
            "extra_output": output if output not in assistant_text else "",
            "spans": result, "scores": raw.get("scores", []),
            "metadata": raw.get("metadata"), "latency": raw.get("latency"),
            "cost": raw.get("totalCost"), "models": sorted({s["model"] for s in result if s["model"]}),
            "missing_output": raw.get("output") is None}


class TraceStore:
    def __init__(self, client: Any, scenarios: Path, host: str, offline: Path | None = None):
        self.client, self.host, self.offline = client, host, offline
        self.scenarios = {s["id"]: s for s in
                          (json.loads(line) for line in scenarios.read_text().splitlines() if line.strip())}
        self.index: dict[str, dict] | None = None
        self.cache: dict[str, dict] = {}
        self.lock = RLock()

    def summaries(self) -> list[dict]:
        with self.lock:
            if self.index is None:
                records = []
                if self.offline:
                    data = json.loads(self.offline.read_text())
                    records = data.get("traces", []) if isinstance(data, dict) else data
                else:
                    page = 1
                    while True:
                        batch = self.client.api.trace.list(page=page, limit=100).data or []
                        records.extend(_jsonable(t) for t in batch)
                        if len(batch) < 100:
                            break
                        page += 1
                index = {}
                for raw in records:
                    row = describe(raw, self.scenarios, self.host)
                    if row["scenario_id"] not in self.scenarios:
                        continue
                    index[row["id"]] = row
                    if self.offline:
                        self.cache[row["id"]] = raw
                if not index:
                    raise ValueError("No traces match the selected scenario file. No demo data was substituted.")
                self.index = index
            return sorted(self.index.values(), key=lambda t: (t["timestamp"], t["id"]))

    def raw(self, tid: str) -> dict:
        self.summaries()
        if tid not in self.index:
            raise ValueError("Trace is outside this review collection")
        with self.lock:
            cached = self.cache.get(tid)
        if cached is not None:
            return cached
        raw = _jsonable(self.client.api.trace.get(tid))
        with self.lock:
            self.cache[tid] = raw
        return raw

    def session(self, tid: str) -> list[dict]:
        rows = self.summaries()
        if tid not in self.index:
            raise ValueError("Unknown trace")
        session = self.index[tid]["session_id"]
        members = [s for s in rows if s["session_id"] == session]
        return [present(self.raw(s["id"]), s) for s in members]

    def normalized(self) -> list[dict]:
        rows = self.summaries()
        def normalize(row):
            raw = self.raw(row["id"])
            result = normalize_trace(raw)
            tokens = sum(o.get("totalTokens") or 0 for o in raw.get("observations", []) if o.get("type") == "GENERATION")
            if tokens:
                result["features"]["tokens"] = tokens
            return result
        with ThreadPoolExecutor(max_workers=4) as pool:
            return list(pool.map(normalize, rows))
