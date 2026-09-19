"""Offline checks: Part C must not mutate the student's source database."""

import sqlite3
import subprocess
import sys
import textwrap

import pytest

from analysis.workshop_runner import copy_world, main


def test_workshop_snapshot_includes_wal_and_isolates_writes(tmp_path):
    source, target = tmp_path / "world.db", tmp_path / "copy.db"
    with sqlite3.connect(source) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE orders (id INTEGER, status TEXT)")
        conn.execute("INSERT INTO orders VALUES (1, 'placed')")
        conn.commit()
        copy_world(source, target)
        with sqlite3.connect(target) as copied:
            assert copied.execute("SELECT status FROM orders").fetchone() == ("placed",)
            copied.execute("UPDATE orders SET status='cancelled'")
        assert conn.execute("SELECT status FROM orders").fetchone() == ("placed",)


def test_workshop_rejects_remote_destination_before_network(monkeypatch, tmp_path):
    monkeypatch.setattr("sys.argv", ["workshop_runner", "support-0140", "--output", str(tmp_path / "run.json"),
                                   "--workshop-url", "https://example.com"])
    monkeypatch.setattr("analysis.workshop_runner.urlopen", lambda *a, **kw: pytest.fail("Network must not run"))
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2


def test_workshop_tool_payloads_through_sdk_export_pipeline():
    """Exercise the real SDK end hook without model calls or network exports."""
    pytest.importorskip("raindrop")
    # Traceloop/Raindrop own process singletons. Isolate this integration test
    # so it cannot replace tracing processors used by other tests.
    code = textwrap.dedent('''
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor
        from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
        from raindrop import Raindrop
        from analysis.workshop_runner import workshop_tool_payloads

        provider = TracerProvider()
        trace.set_tracer_provider(provider)
        existing_exporter = InMemorySpanExporter()
        provider.add_span_processor(SimpleSpanProcessor(existing_exporter))
        workshop_exporter = InMemorySpanExporter()
        client = Raindrop(api_key="local-workshop", endpoint="http://localhost:5899/v1/",
            local_workshop_url=None, tracing_enabled=True, auto_instrument=False,
            exporter=workshop_exporter, span_postprocess_callback=workshop_tool_payloads)
        assert trace.get_tracer_provider() is provider
        tracer = trace.get_tracer("workshop-payload-regression")
        for name, extra in (
            ("success", {"gen_ai.tool.call.arguments": '{"query":"webcam"}',
                         "gen_ai.tool.call.result": '{"ok":true,"products":[]}'}),
            ("denied", {"gen_ai.tool.call.arguments": '{"order_id":4127}',
                        "gen_ai.tool.call.result": '{"error":"permission_denied"}',
                        "cartwheel.permission_denied": True}),
            ("content_disabled", {}),
            ("existing_payload", {"gen_ai.tool.call.arguments": 'new',
                                  "traceloop.entity.input": 'original'}),
        ):
            with tracer.start_as_current_span(name, attributes={
                "gen_ai.operation.name": "execute_tool", **extra}):
                pass
        with tracer.start_as_current_span("model", attributes={
            "gen_ai.operation.name": "chat", "gen_ai.tool.call.arguments": 'ignore'}):
            pass
        provider.force_flush()
        old = existing_exporter.get_finished_spans()
        new = workshop_exporter.get_finished_spans()
        assert len(old) == len(new) == 5
        assert [s.context for s in old] == [s.context for s in new]
        spans = {s.name: dict(s.attributes) for s in new}
        for name in ("success", "denied"):
            a = spans[name]
            assert a["traceloop.entity.input"] == a["gen_ai.tool.call.arguments"]
            assert a["traceloop.entity.output"] == a["gen_ai.tool.call.result"]
        assert spans["denied"]["cartwheel.permission_denied"] is True
        assert "traceloop.entity.input" not in spans["content_disabled"]
        assert "traceloop.entity.input" not in spans["model"]
        assert spans["existing_payload"]["traceloop.entity.input"] == 'original'
        client.shutdown()
        provider.shutdown()
    ''')
    subprocess.run([sys.executable, "-c", code], check=True, timeout=30)
