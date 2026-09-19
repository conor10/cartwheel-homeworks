"""Reproducible HW4 batches, without outcome-based automatic selection."""

import random
from collections import defaultdict

from analysis.helpers import selection
from .state import now


def clusters(traces):
    vectors = selection._standardize([selection._feature_vector(t) for t in traces])
    assignments = selection._kmeans(vectors, min(15, len(traces)), seed=41)
    groups = defaultdict(list)
    for i, cluster in enumerate(assignments):
        groups[cluster].append(i)
    ordered = {}
    for cluster, indices in groups.items():
        centre = [sum(vectors[i][d] for i in indices) / len(indices) for d in range(5)]
        ordered[cluster] = sorted(indices, key=lambda i: sum((a-b)**2 for a, b in zip(vectors[i], centre)))
    return assignments, ordered


def graph(store):
    traces = store.normalized()
    assignments, _ = clusters(traces)
    return [{"id": t["id"], "cluster": c,
             "x": t["features"]["tool_call_count"],
             "y": t["features"]["turn_count"],
             "tokens": t["features"]["tokens"]} for t, c in zip(traces, assignments)]


def add_batch(state, body, store):
    manifest = state["manifest"]
    picks = manifest.setdefault("picks", [])
    existing = {p["trace_id"] for p in picks}
    stage = body.get("stage")
    rows = store.summaries()
    pool = [t for t in rows if t["id"] not in existing]
    rng = random.Random(41)
    new = []
    if stage == "initial":
        if picks:
            raise ValueError("The initial sample already exists")
        dimension = body.get("dimension", "role")
        if dimension not in ("role", "intent", "group"):
            raise ValueError("Choose role, intent or group")
        if len(pool) < 30:
            raise ValueError("The initial batch requires at least 30 distinct traces")
        manifest.update(dimension=dimension, dimension_chosen_at=now(), seed=41,
                        source="offline" if store.offline else "langfuse")
        random_ids = {r["id"] for r in rng.sample(pool, 15)}
        new = [{"trace_id": r["id"], "batch": "initial_random", "reason": "Uniform random sample; seed 41"}
               for r in pool if r["id"] in random_ids]
        remaining = [t for t in store.normalized() if t["id"] not in random_ids]
        _, grouped = clusters(remaining)
        selected = []
        while len(selected) < 15:
            for cluster, indices in sorted(grouped.items()):
                if indices and len(selected) < 15:
                    selected.append((indices.pop(0), cluster))
        new += [{"trace_id": remaining[i]["id"], "batch": "initial_cluster",
                 "reason": f"Cluster {c} representative nearest centroid; seed 41"} for i, c in selected]
    elif stage == "dimension":
        if not manifest.get("dimension") or any(p["batch"] == "dimension" for p in picks):
            raise ValueError("Create the initial sample first; dimension sampling can run once")
        groups = defaultdict(list)
        for row in pool:
            groups[row[manifest["dimension"]]].append(row)
        for group in groups.values():
            rng.shuffle(group)
        while len(new) < 30 and any(groups.values()):
            for value, group in sorted(groups.items()):
                if group and len(new) < 30:
                    row = group.pop()
                    new.append({"trace_id": row["id"], "batch": "dimension",
                                "reason": f"Balanced {manifest['dimension']} sample: {value}; seed 41"})
        if len(new) != 30:
            raise ValueError("Not enough remaining traces for the dimension batch")
    elif stage == "depth_remove":
        ids = body.get("trace_ids", [])
        depth_ids = {p["trace_id"] for p in picks if p["batch"] == "depth"}
        if not ids or len(ids) != len(set(ids)) or not set(ids) <= depth_ids:
            raise ValueError("Choose existing depth traces to remove; other batches cannot be changed here")
        reason = body.get("reason", "").strip()
        if not reason:
            raise ValueError("Record why these traces are being removed")
        removed = [p for p in picks if p["trace_id"] in set(ids)]
        manifest.setdefault("removals", []).append({
            "removed_at": now(), "reason": reason, "picks": removed,
        })
        manifest["picks"] = [p for p in picks if p["trace_id"] not in set(ids)]
        # Membership changes never erase human notes, reviews, labels or scores.
        return
    elif stage == "depth":
        ids = body.get("trace_ids", [])
        if not ids or len(ids) != len(set(ids)) or set(ids) & existing:
            raise ValueError("Choose new, distinct traces for the depth batch")
        if not set(ids) <= {r["id"] for r in pool}:
            raise ValueError("Unknown trace in depth batch")
        if len(ids) + sum(p["batch"] == "depth" for p in picks) > 25:
            raise ValueError("The depth batch has 25 slots")
        reason = body.get("reason", "").strip()
        if not reason:
            raise ValueError("Record the search and why these candidates or close negatives were selected")
        new = [{"trace_id": tid, "batch": "depth", "reason": reason} for tid in ids]
    elif stage == "final":
        if any(p["batch"] == "final" for p in picks):
            raise ValueError("The final random batch already exists")
        if len(existing) != 85 or not state["modes"]:
            raise ValueError("Select the first 85 traces and draft the taxonomy before the final batch")
        if any(state["reviews"].get(t, {}).get("status", "unreviewed") == "unreviewed" for t in existing):
            raise ValueError("Finish open coding the first 85 traces before the final batch")
        if len(pool) < 15:
            raise ValueError("Not enough remaining traces")
        new = [{"trace_id": r["id"], "batch": "final", "reason": "Final uniform random check; seed 41"}
               for r in rng.sample(pool, 15)]
    else:
        raise ValueError("Unknown sampling stage")
    if stage in ("dimension", "depth") and not any(p["batch"] == "initial_random" for p in picks):
        raise ValueError("Start with the initial sample")
    picks.extend(new)
    manifest.setdefault("batches", []).append({"stage": stage, "selected_at": now(), "count": len(new)})
