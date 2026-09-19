"""Run one existing scenario with local Workshop and Langfuse tracing.

uv run --extra workshop python -m analysis.workshop_runner support-0140 \
    --output /tmp/workshop-support-0140.json

Uses a temporary copy of the current world and a fresh session database. Recorded
results are new executions, not reproductions of the original HW3 database state.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sqlite3
import tempfile
import uuid
from contextlib import closing
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

from observability.instrument import REPO_ROOT, load_env, setup_tracing


def copy_world(source: Path, destination: Path) -> None:
    """Take a consistent, read-only snapshot, including committed WAL content."""
    with closing(sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)) as src:
        with closing(sqlite3.connect(destination)) as dst:
            src.backup(dst)


def workshop_tool_payloads(span) -> None:
    """Expose OpenLLMetry tool payloads in Workshop 0.1.21's detail panels.

    Raindrop's postprocess hook receives an ended span with writable attributes.
    Workshop recognizes the tool kind but does not yet read the newer GenAI
    argument/result keys as payloads. Retain those keys and add legacy aliases;
    do not create a second span or record any content that was not captured.
    """
    attributes = span._attributes
    if not attributes or attributes.get("gen_ai.operation.name") != "execute_tool":
        return
    for source, target in (
        ("gen_ai.tool.call.arguments", "traceloop.entity.input"),
        ("gen_ai.tool.call.result", "traceloop.entity.output"),
    ):
        if source in attributes and target not in attributes:
            attributes[target] = attributes[source]


async def run(scenario: dict, directory: Path, endpoint: str) -> dict:
    from langfuse import get_client
    from opentelemetry import trace
    from opentelemetry.sdk.trace import SpanProcessor
    from raindrop import Raindrop

    from server import app as server_app

    # Keep the existing server route, authentication and agent/tool behaviour.
    server_app.SESSIONS_DB = directory / "sessions.db"
    if not setup_tracing():
        raise RuntimeError("The existing Langfuse configuration must be available")
    provider = trace.get_tracer_provider()
    roots = []

    class CaptureRoots(SpanProcessor):
        def on_end(self, span):
            if span.name == "cartwheel.session_message":
                roots.append(format(span.context.trace_id, "032x"))

    provider.add_span_processor(CaptureRoots())
    # Local-only destination. A non-secret local key enables the SDK's tool
    # tracing; explicit endpoint and disabled mirroring prevent cloud export.
    client = Raindrop(
        api_key="local-workshop",
        endpoint=endpoint + "/v1/",
        local_workshop_url=None,
        tracing_enabled=True,
        auto_instrument=False,
        span_postprocess_callback=workshop_tool_payloads,
    )
    if trace.get_tracer_provider() is not provider:
        raise RuntimeError("Workshop replaced the existing tracer provider")
    identity = scenario["tuple"]
    created = server_app.create_session(server_app.SessionCreate(
        role=identity["role"], user_id=identity["user_id"],
    ))
    batch_id = str(uuid.uuid4())
    result = {
        "batch_id": batch_id, "source_scenario_id": scenario["id"],
        "role": identity["role"], "user_id": identity["user_id"],
        "session_id": created["session_id"], "database": "temporary snapshot of current world",
        "turns": [],
    }
    try:
        for number, message in enumerate([scenario["opening_message"], *scenario.get("followups", [])], 1):
            name = f"hw4-workshop/{scenario['id']}/{batch_id}/turn-{number}"
            record = {"turn": number, "workshop_name": name, "input": message}
            root_count = len(roots)
            # Reuse OpenLLMetry's existing model/tool spans. Registering the
            # framework wrapper as well would duplicate every tool execution.
            interaction = client.begin(
                user_id=str(identity["user_id"]), event=name, input=message,
                convo_id=created["session_id"],
                properties={"role": identity["role"], "source_scenario_id": scenario["id"]},
            )
            record["workshop_event_id"] = interaction.id
            # Let the server establish its request span before Runner creates
            # the SDK workflow, keeping both in the same Langfuse trace.
            try:
                response = await asyncio.wait_for(server_app.post_message(
                    created["session_id"],
                    server_app.MessageIn(message=message, scenario_id="hw4-workshop-" + scenario["id"]),
                    authorization="Bearer " + created["token"],
                ), timeout=240)
                record.update(reply=response["reply"], prompt_version=response["prompt_version"])
            except Exception as exc:
                record["error"] = {"type": type(exc).__name__, "message": str(exc)}
            interaction.finish(output=record.get("reply") or json.dumps(record.get("error")))
            record["langfuse_trace_ids"] = roots[root_count:]
            result["turns"].append(record)
            client.flush()
            provider.force_flush()
            get_client().flush()
            print(json.dumps({"scenario": scenario["id"], "turn": number, "error": record.get("error"),
                              "langfuse_trace_ids": record["langfuse_trace_ids"]}), flush=True)
            if "error" in record:
                break
    finally:
        client.flush()
        provider.force_flush()
        get_client().flush()
        client.shutdown()
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario_id")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workshop-url", default="http://localhost:5899")
    args = parser.parse_args()
    url = urlparse(args.workshop_url)
    if url.scheme != "http" or url.hostname not in {"localhost", "127.0.0.1"} or url.username or url.password or url.path not in {"", "/"} or url.query or url.fragment:
        parser.error("Workshop must be a local loopback HTTP address")
    if args.output.exists():
        parser.error("Output already exists; choose a new path to preserve earlier runs")
    endpoint = args.workshop_url.rstrip("/")
    with urlopen(endpoint + "/health", timeout=5) as response:
        if response.status != 200:
            raise RuntimeError("Workshop is not healthy")
    scenarios = [json.loads(line) for line in (REPO_ROOT / "scenarios/support_scenarios.jsonl").read_text().splitlines() if line.strip()]
    scenario = next((s for s in scenarios if s["id"] == args.scenario_id), None)
    if scenario is None:
        parser.error("Unknown scenario ID")
    load_env()
    # Part C captures full fictional course traces only into local stores.
    for key in ("LANGFUSE_HOST", "LANGFUSE_BASE_URL"):
        value = os.environ.get(key)
        if value and urlparse(value).hostname not in {"localhost", "127.0.0.1"}:
            parser.error(f"{key} must point to local Langfuse for this runner")
    if not (os.environ.get("LANGFUSE_HOST") or os.environ.get("LANGFUSE_BASE_URL")):
        parser.error("A local Langfuse host must be explicitly configured")
    source = Path(os.environ.get("CARTWHEEL_DB", REPO_ROOT / "data/cartwheel.db"))
    with tempfile.TemporaryDirectory(prefix="cartwheel-workshop-") as tmp:
        directory = Path(tmp)
        copy_world(source, directory / "world.db")
        os.environ["CARTWHEEL_DB"] = str(directory / "world.db")
        os.environ["TRACELOOP_TRACE_CONTENT"] = "true"
        result = asyncio.run(run(scenario, directory, endpoint))
        with args.output.open("x") as output:
            json.dump(result, output, indent=2, ensure_ascii=False)
            output.write("\n")


if __name__ == "__main__":
    main()
