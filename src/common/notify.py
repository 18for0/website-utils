import json
import os
from typing import Any

import boto3

from .logging_config import get_logger

log = get_logger(__name__)


def notify_failure(
    *,
    function_name: str,
    error: BaseException,
    event: dict[str, Any] | None = None,
    context: Any | None = None,
    traceback_text: str | None = None,
    subject: str | None = None,
    body: str | None = None,
) -> None:
    """Publish a failure notification to the SNS topic configured in env.

    When ``subject`` or ``body`` are provided they override the generic
    defaults, letting a Lambda emit purpose-specific alert copy. Fails loud:
    if SNS publish itself errors, the exception propagates so the Lambda run
    is still marked as failed.
    """
    topic_arn = os.environ.get("ERROR_TOPIC_ARN")
    if not topic_arn:
        log.error(
            "ERROR_TOPIC_ARN not set; cannot send failure notification",
            extra={"ctx_function": function_name},
        )
        return

    default_subject = f"[18for0-website-utils] {function_name} failed"
    default_body = build_default_body(
        function_name=function_name,
        error=error,
        event=event,
        context=context,
        traceback_text=traceback_text,
    )

    client = boto3.client("sns")
    client.publish(
        TopicArn=topic_arn,
        Subject=subject or default_subject,
        Message=body or default_body,
    )


def build_default_body(
    *,
    function_name: str,
    error: BaseException,
    event: dict[str, Any] | None = None,
    context: Any | None = None,
    traceback_text: str | None = None,
) -> str:
    """Render a human-readable, multi-line failure email body.

    Pulls identity (account/region/request id/log group-stream) from the
    Lambda context when available, and invocation source/trigger from the
    EventBridge fields of the event payload when present. Always finishes
    with the traceback (if captured) and the raw event JSON for deep dives.
    """
    header = "18for0-website-utils Lambda FAILED"
    sections: list[str] = [header, "=" * len(header), ""]

    sections.extend(
        _labeled_lines(
            {
                "Function": function_name,
                "Error type": type(error).__name__,
                "Error": str(error),
            }
        )
    )
    sections.append("")

    identity_labels = _context_labels(context)
    if identity_labels:
        sections.extend(_labeled_lines(identity_labels))
        sections.append("")

    invocation_labels = _invocation_labels(event)
    if invocation_labels:
        sections.extend(_labeled_lines(invocation_labels))
        sections.append("")

    if traceback_text:
        sections.extend(["Traceback", "---------", traceback_text.rstrip(), ""])

    sections.extend(
        [
            "Raw event",
            "---------",
            json.dumps(event, indent=2, default=str, sort_keys=True)
            if event is not None
            else "(no event)",
        ]
    )

    return "\n".join(sections)


def _labeled_lines(labels: dict[str, str]) -> list[str]:
    width = max(len(name) for name in labels)
    return [f"{name.ljust(width)} : {value}" for name, value in labels.items()]


def _context_labels(context: Any | None) -> dict[str, str]:
    if context is None:
        return {}

    labels: dict[str, str] = {}
    arn = getattr(context, "invoked_function_arn", None)
    if arn:
        parts = arn.split(":")
        if len(parts) >= 5:
            labels["Region"] = parts[3]
            labels["Account"] = parts[4]

    for field, label in (
        ("aws_request_id", "Request ID"),
        ("log_group_name", "Log group"),
        ("log_stream_name", "Log stream"),
        ("function_version", "Version"),
    ):
        value = getattr(context, field, None)
        if value:
            labels[label] = str(value)

    return labels


def _invocation_labels(event: dict[str, Any] | None) -> dict[str, str]:
    if not isinstance(event, dict):
        return {}

    labels: dict[str, str] = {}
    if event.get("time"):
        labels["Invocation time (UTC)"] = str(event["time"])

    source = event.get("source")
    detail_type = event.get("detail-type")
    if source and detail_type:
        labels["Invocation source"] = f"{source} ({detail_type})"
    elif source:
        labels["Invocation source"] = str(source)

    resources = event.get("resources")
    if isinstance(resources, list) and resources:
        labels["Triggered by"] = ", ".join(str(r) for r in resources)

    return labels
