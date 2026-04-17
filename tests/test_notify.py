from types import SimpleNamespace

from src.common.notify import build_default_body


def _context() -> SimpleNamespace:
    return SimpleNamespace(
        invoked_function_arn="arn:aws:lambda:eu-west-1:487109334257:function:health_check",
        aws_request_id="req-abc-123",
        log_group_name="/aws/lambda/health_check",
        log_stream_name="2026/04/17/[$LATEST]abcd1234",
        function_version="$LATEST",
    )


def _event() -> dict:
    return {
        "version": "0",
        "id": "e569f7d5-9558-433a-4cf0-d36f1a7f5160",
        "detail-type": "Scheduled Event",
        "source": "aws.events",
        "account": "487109334257",
        "time": "2026-04-17T14:55:37Z",
        "region": "eu-west-1",
        "resources": ["arn:aws:events:eu-west-1:487109334257:rule/health_check-schedule"],
        "detail": {},
    }


def test_body_includes_function_error_and_message():
    body = build_default_body(
        function_name="health_check",
        error=RuntimeError("boom"),
        event={},
        context=None,
    )
    assert "Function" in body
    assert "health_check" in body
    assert "Error type" in body
    assert "RuntimeError" in body
    assert "boom" in body


def test_body_pulls_region_and_account_from_context_arn():
    body = build_default_body(
        function_name="health_check",
        error=RuntimeError("boom"),
        event={},
        context=_context(),
    )
    assert "Region" in body
    assert "eu-west-1" in body
    assert "Account" in body
    assert "487109334257" in body
    assert "Request ID" in body
    assert "req-abc-123" in body
    assert "Log group" in body
    assert "/aws/lambda/health_check" in body


def test_body_surfaces_eventbridge_invocation_source_and_trigger():
    body = build_default_body(
        function_name="health_check",
        error=RuntimeError("boom"),
        event=_event(),
        context=None,
    )
    assert "Invocation time (UTC)" in body
    assert "2026-04-17T14:55:37Z" in body
    assert "aws.events (Scheduled Event)" in body
    assert "Triggered by" in body
    assert "rule/health_check-schedule" in body


def test_body_includes_traceback_when_provided():
    tb = (
        "Traceback (most recent call last):\n"
        "  File ..., line 1, in <module>\n"
        "RuntimeError: boom"
    )
    body = build_default_body(
        function_name="health_check",
        error=RuntimeError("boom"),
        event=None,
        traceback_text=tb,
    )
    assert "Traceback" in body
    assert "RuntimeError: boom" in body


def test_body_pretty_prints_raw_event_at_end():
    body = build_default_body(
        function_name="health_check",
        error=RuntimeError("boom"),
        event={"source": "aws.events", "detail": {}},
    )
    assert body.rstrip().endswith("}")
    assert '"source": "aws.events"' in body


def test_body_handles_missing_context_and_event():
    body = build_default_body(
        function_name="health_check",
        error=RuntimeError("boom"),
        event=None,
        context=None,
    )
    assert "health_check" in body
    assert "(no event)" in body
