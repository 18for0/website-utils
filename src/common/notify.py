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
    default_body = json.dumps(
        {
            "function": function_name,
            "error_type": type(error).__name__,
            "error": str(error),
            "event": event,
        },
        default=str,
    )

    client = boto3.client("sns")
    client.publish(
        TopicArn=topic_arn,
        Subject=subject or default_subject,
        Message=body or default_body,
    )
