"""Rebuild HW9's required CSV from saved development runs, without model calls."""
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = [
    ("hw8-final", "development-final-glm-5.2-20261003-123815.json"),
    ("fewer-tokens", "development-fewer-tokens-glm-5.2-20261004-143947.json"),
    ("cache-before", "development-cache-before-gpt-5.5-20261005-092103.json"),
    ("cache-after", "development-cache-after-gpt-5.5-20261005-092349.json"),
]


def dominates(a, b):
    score, cost = "development_score", "cost_per_100_conversations_usd"
    return (a[score] >= b[score] and a[cost] <= b[cost]
            and (a[score] > b[score] or a[cost] < b[cost]))


def main():
    rows, provenance = [], []
    membership = None
    for candidate, filename in SOURCES:
        path = ROOT / "optimize/results" / filename
        data = json.loads(path.read_text())
        if data["split"] != "development":
            raise ValueError("Only development results belong in this comparison")
        ids = sorted(c["case_id"] for c in data["cases"])
        if membership is not None and membership != ids:
            raise ValueError("Development cases differ across runs")
        membership = ids
        score = sum(c["pass_rate"] for c in data["cases"]) / len(ids)
        cost = data["cost_usd"] / data["evaluated_case_runs"] * 100
        if not math.isclose(score, data["score"], abs_tol=1e-6):
            raise ValueError("Saved score does not reconcile with case results")
        # Saved total cost is rounded to six decimals before this calculation.
        if not math.isclose(cost, data["cost_per_100_conversations_usd"], abs_tol=1e-5):
            raise ValueError("Saved cost per 100 does not reconcile with total cost")
        rows.append({"candidate": candidate, "model": data["model"],
                     "development_score": data["score"],
                     "write_pass_5": data["write_pass_5"],
                     "cost_per_100_conversations_usd": data["cost_per_100_conversations_usd"],
                     "median_latency_seconds": data["median_latency_seconds"]})
        provenance.append({"candidate": candidate, "source": str(path.relative_to(ROOT)),
                           "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                           "git_commit": data["git_commit"]})
    for row in rows:
        row["frontier_status"] = "dominated" if any(dominates(other, row) for other in rows) else "frontier"
    output = ROOT / "profile/results"
    with (output / "frontier.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "sources": provenance, "development_case_ids": membership,
        "rule": "Only development score and cost determine dominance; equal score and equal cost do not dominate each other.",
        "verification": "Same case membership; scores recalculated from case pass rates; costs reconciled with saved totals allowing rounding.",
        "limitations": [
            "One run per configuration, seven development cases; no statistical claim of equal model quality.",
            "Blank write_pass_5 means unavailable, not zero or verified write safety.",
            "Costs are saved agent-run estimates, excluding judge calls and retaining the original pricing assumptions.",
            "The GLM baseline predates the prompt reorder. The current GLM plus reordered prompt combination has not been measured.",
            "Scores retain the known response-detail judge limitations."
        ],
        "student_configuration_choice": (json.loads((output / "final-selection.json").read_text())["candidate"]
                                         if (output / "final-selection.json").exists() else "pending"),
        "new_model_calls": 0
    }
    (output / "frontier-method.json").write_text(json.dumps(report, indent=2) + "\n")
    print((output / "frontier.csv").read_text())


if __name__ == "__main__":
    main()
