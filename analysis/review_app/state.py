"""Durable human decisions and retryable, idempotent Langfuse writes."""

from __future__ import annotations

import copy
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from uuid import NAMESPACE_URL, uuid4, uuid5

from analysis.server import _write_json


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read(path: Path, default):
    # Never silently replace corrupt human work with an empty document.
    return json.loads(path.read_text()) if path.exists() else copy.deepcopy(default)


def rows(value, key):
    return value.get(key, []) if isinstance(value, dict) else value


def required(data, key):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key.replace('_', ' ')} is required")
    return value.strip()


class Conflict(ValueError):
    pass


class Workspace:
    def __init__(self, directory: Path, client=None):
        self.directory, self.client = directory, client
        self.lock = RLock()
        self.path = directory / "review_workspace.json"
        self.data = read(self.path, {
            "revision": 0, "annotations": rows(read(directory / "annotations.json", []), "annotations"),
            "modes": rows(read(directory / "patterns.json", {"modes": []}), "modes"),
            "suggestions": rows(read(directory / "suggestions.json", []), "suggestions"),
            "manifest": read(directory / "sample_manifest.json", {"picks": [], "batches": []}),
            "reviews": {}, "labels": {}, "outbox": {}, "history": [],
        })
        if not all(isinstance(self.data[k], list) for k in ("annotations", "modes", "suggestions")):
            raise ValueError("Existing review state has an unsupported format; it has not been modified.")
        self.data.setdefault("label_proposals", {})

    def snapshot(self):
        with self.lock:
            return copy.deepcopy(self.data)

    def persist(self):
        _write_json(self.path, self.data)
        _write_json(self.directory / "annotations.json", {"annotations": self.data["annotations"]})
        _write_json(self.directory / "patterns.json", {"modes": self.data["modes"]})
        _write_json(self.directory / "suggestions.json", self.data["suggestions"])
        _write_json(self.directory / "sample_manifest.json", self.data["manifest"])
        _write_json(self.directory / "label_proposals.json", self.data["label_proposals"])
        # Preserve starter/other records; only replace the exact trace/mode pairs we own.
        for mode in {v["mode"] for v in self.data["labels"].values()}:
            path = self.directory / "labels" / f"{mode}.jsonl"
            old = [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []
            labels = {v["trace_id"]: v for v in self.data["labels"].values() if v["mode"] == mode}
            retained = [v for v in old if v.get("trace_id") not in labels]
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".jsonl.tmp")
            tmp.write_text("".join(json.dumps(v, ensure_ascii=False) + "\n" for v in retained + list(labels.values())))
            tmp.replace(path)

    def queue(self, key, tid, name, value, kind, record):
        score_id = str(uuid5(NAMESPACE_URL, "cartwheel-hw4:" + key))
        self.data["outbox"][key] = {
            "id": score_id, "trace_id": tid, "name": name, "value": value,
            "data_type": kind, "comment": json.dumps(record, ensure_ascii=False),
            "metadata": {"source": "hw4_review_app", "record_key": key},
            "status": "pending", "updated_at": now(),
        }
        return score_id

    def sync(self):
        """Synchronous API acknowledgement, not a fire-and-forget SDK flush."""
        if self.client is None:
            return
        from langfuse.api.resources.score.types.create_score_request import CreateScoreRequest
        for item in self.data["outbox"].values():
            if item["status"] == "synced":
                continue
            try:
                self.client.api.score.create(request=CreateScoreRequest(**{
                    key: item[key] for key in ("id", "trace_id", "name", "value", "data_type", "comment", "metadata")
                }))
                item.update(status="synced", synced_at=now())
                item.pop("error", None)
            except Exception as exc:
                # SDK exceptions can include request details: never send them to the UI.
                item.update(status="pending", error=f"Langfuse write failed ({type(exc).__name__}). Retry sync.")
        for label in self.data["labels"].values():
            label["sync_status"] = self.data["outbox"]["label:" + label["trace_id"] + ":" + label["mode"]]["status"]

    def mutate(self, action: str, body: dict, traces):
        with self.lock:
            if body.get("revision") != self.data["revision"]:
                raise Conflict("The workspace changed. Reload the latest state before saving your draft.")
            before = copy.deepcopy(self.data)
            try:
                self._apply(action, body, traces)
            except Exception:
                self.data = before
                raise
            self.data["revision"] += 1
            self.data["history"].append({"action": action, "at": now(), "revision": self.data["revision"]})
            self.persist()  # Persist pending intent before contacting the canonical store.
            self.sync()
            self.persist()
            return self.snapshot()

    def _trace(self, body, traces):
        tid = required(body, "trace_id")
        if tid not in {t["id"] for t in traces.summaries()}:
            raise ValueError("Unknown trace")
        return tid

    def _note(self, body, traces):
        tid = self._trace(body, traces)
        oid = body.get("observation_id") or None
        if oid and oid not in {s["id"] for s in traces.raw(tid).get("observations", [])}:
            raise ValueError("Observation does not belong to this trace")
        aid = body.get("id") or str(uuid4())
        previous = next((a for a in self.data["annotations"] if a["id"] == aid), None)
        if previous and previous["trace_id"] != tid:
            raise ValueError("An annotation cannot move between traces")
        note = {"id": aid, "trace_id": tid, "observation_id": oid,
                "field": body.get("field", "trace"), "quote": body.get("quote", ""),
                "start": body.get("start"), "end": body.get("end"),
                "note": required(body, "note"), "requirement": body.get("requirement", ""),
                "source": body.get("source", "human"), "updated_at": now(),
                "history": (previous.get("history", []) + [{k: v for k, v in previous.items() if k != "history"}]) if previous else []}
        if previous:
            self.data["annotations"][self.data["annotations"].index(previous)] = note
        else:
            self.data["annotations"].append(note)
        self.queue("note:" + aid, tid, "hw4_open_code", "Human note", "TEXT", note)
        return note

    def _apply(self, action, body, traces):
        if action == "sync":
            return
        if action == "note":
            self._note(body, traces)
        elif action == "review":
            tid = self._trace(body, traces)
            status = body.get("status")
            if status not in ("first_failure", "no_failure_observed", "unreviewed"):
                raise ValueError("Choose a review outcome")
            aid = body.get("annotation_id")
            if status == "first_failure" and not any(a["id"] == aid and a["trace_id"] == tid for a in self.data["annotations"]):
                raise ValueError("Choose a saved note describing the first failure")
            old = self.data["reviews"].get(tid)
            review = {"status": status, "annotation_id": aid if status == "first_failure" else None,
                      "updated_at": now(), "history": (old.get("history", []) + [{k: v for k, v in old.items() if k != "history"}]) if old else []}
            self.data["reviews"][tid] = review
            self.queue("review:" + tid, tid, "hw4_review_status", status, "TEXT", review)
        elif action == "mode":
            name = required(body, "name")
            if not re.fullmatch(r"[a-z][a-z0-9_]{0,79}", name):
                raise ValueError("Use a snake_case mode name")
            old = next((m for m in self.data["modes"] if m["name"] == name), None)
            mode = {k: body.get(k, "") for k in ("name", "definition", "boundary", "requirement", "evaluator_type")}
            mode["definition"] = required(body, "definition")
            mode["status"] = body.get("status", "draft")
            if mode["status"] not in ("draft", "final", "retired"):
                raise ValueError("Invalid mode status")
            mode["created_from"] = body.get("created_from", [])
            valid_notes = {a["id"] for a in self.data["annotations"]}
            if not isinstance(mode["created_from"], list) or not set(mode["created_from"]) <= valid_notes:
                raise ValueError("Supporting annotation IDs must identify existing human notes")
            if mode["status"] == "final":
                for key in ("boundary", "requirement", "evaluator_type"):
                    required(mode, key)
                if not mode["created_from"]:
                    raise ValueError("A final mode must link to supporting human annotations")
            mode.update(version=old.get("version", 0) + 1 if old else 1, updated_at=now(),
                        revision_reason=required(body, "revision_reason") if old else "Initial definition",
                        history=(old.get("history", []) + [{k: v for k, v in old.items() if k != "history"}]) if old else [])
            if old:
                self.data["modes"][self.data["modes"].index(old)] = mode
            else:
                self.data["modes"].append(mode)
        elif action == "label_proposals":
            selected = {p["trace_id"] for p in self.data["manifest"]["picks"]}
            seen = set()
            for item in body.get("items", []):
                tid = self._trace(item, traces)
                mode = next((m for m in self.data["modes"] if m["name"] == item.get("mode")), None)
                if tid not in selected or not mode or mode["status"] == "retired":
                    raise ValueError("Proposals require a selected trace and an active mode")
                if item.get("mode_version") != mode["version"]:
                    raise ValueError("Proposal definition version is stale")
                value = item.get("label")
                if value is not None and (type(value) is not int or value not in (0, 1)):
                    raise ValueError("Proposed label must be 0, 1 or null for unresolved")
                key = tid + ":" + mode["name"]
                if key in seen:
                    raise ValueError("Duplicate proposal")
                seen.add(key)
                old = self.data["label_proposals"].get(key)
                self.data["label_proposals"][key] = {
                    **item, "note": required(item, "note"), "source": "agent_proposal",
                    "updated_at": now(),
                    "history": (old.get("history", []) + [{k: v for k, v in old.items() if k != "history"}]) if old else [],
                }
            # Proposed labels never enter the score outbox or canonical label files.
        elif action == "label_batch":
            items = body.get("items")
            if not isinstance(items, list) or not items or len(items) > 800:
                raise ValueError("Choose 1 to 800 judgments to confirm")
            pairs = [(i.get("trace_id"), i.get("mode")) for i in items]
            if len(pairs) != len(set(pairs)):
                raise ValueError("Duplicate judgment in confirmation")
            for item in items:
                mode = next((m for m in self.data["modes"] if m["name"] == item.get("mode")), None)
                if not mode or item.get("mode_version") != mode["version"]:
                    raise ValueError("Definition changed; reload before confirming judgments")
                self._apply("label", item, traces)
        elif action == "label":
            tid = self._trace(body, traces)
            mode = next((m for m in self.data["modes"] if m["name"] == body.get("mode") and m["status"] == "final"), None)
            if not mode:
                raise ValueError("Choose a final mode first")
            if self.data["reviews"].get(tid, {}).get("status", "unreviewed") == "unreviewed":
                raise ValueError("Complete open coding for this trace before structured labeling")
            value = body.get("label")
            if type(value) is not int or value not in (0, 1):
                raise ValueError("Label must be 1 (present) or 0 (absent)")
            key = tid + ":" + mode["name"]
            old = self.data["labels"].get(key)
            record = {"trace_id": tid, "mode": mode["name"], "mode_version": mode["version"],
                      "label": value, "note": required(body, "note"), "source": "human",
                      "close_negative": bool(body.get("close_negative")) and value == 0,
                      "updated_at": now(), "sync_status": "pending",
                      "history": (old.get("history", []) + [{k: v for k, v in old.items() if k != "history"}]) if old else []}
            record["score_id"] = self.queue("label:" + key, tid, mode["name"], value, "NUMERIC", record)
            self.data["labels"][key] = record
        elif action == "suggestions":
            existing = {s["id"] for s in self.data["suggestions"]}
            for suggestion in body.get("items", []):
                self._trace(suggestion, traces)
                sid = required(suggestion, "id")
                if sid in existing:
                    raise ValueError("Suggestion IDs must be unique; existing decisions are preserved")
                existing.add(sid)
                self.data["suggestions"].append({**suggestion, "text": required(suggestion, "text"),
                    "source": required(suggestion, "source"), "status": "pending", "created_at": now()})
        elif action == "suggestion":
            suggestion = next((s for s in self.data["suggestions"] if s["id"] == body.get("id")), None)
            if not suggestion:
                raise ValueError("Suggestion is missing")
            if suggestion["status"] != "pending" and body.get("revise") is not True:
                raise ValueError("Suggestion is missing or already decided")
            decision = body.get("decision")
            if decision not in ("accepted", "rejected"):
                raise ValueError("Accept or reject the suggestion")
            reason = required(body, "reason")
            if suggestion["status"] != "pending":
                suggestion.setdefault("history", []).append({
                    key: suggestion.get(key) for key in
                    ("status", "decision_reason", "decided_at", "annotation_id")
                })
            suggestion.update(status=decision, decision_reason=reason, decided_at=now())
            previous = next((a for a in self.data["annotations"]
                             if a["id"] == suggestion.get("annotation_id")), None)
            if decision == "accepted" or previous:
                # Revise the same annotation/remote score rather than leaving a
                # stale accepted note or creating duplicates. A reversed decision
                # remains an explicit rejection note, with the acceptance in history.
                note = self._note({**(previous or {}), "trace_id": suggestion["trace_id"],
                    "note": reason if decision == "accepted" else "Suggestion rejected: " + reason,
                    "quote": suggestion.get("quote", ""),
                    "source": "accepted_suggestion" if decision == "accepted" else "rejected_suggestion"}, traces)
                suggestion["annotation_id"] = note["id"]
            # Acceptance records a human note, never an implicit binary label.
        elif action == "sample":
            from .sampling import add_batch
            add_batch(self.data, body, traces)
        else:
            raise ValueError("Unknown action")
