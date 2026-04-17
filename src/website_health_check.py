#!/usr/bin/env python3
"""Morning reachability check for the 18for0 public website.

Runs daily at 08:00 UTC via EventBridge, issues an HTTP GET against the
configured target URL, and raises a ``LambdaError`` carrying a
website-specific email subject/body when the site is unreachable or
returns a non-2xx status. The email is delivered via the shared SNS
failure-notification topic subscribed to 18for0@gmail.com.
"""

from __future__ import annotations

import os
from typing import Any
from urllib import error, request

from src.common import LambdaError, get_logger, handler_entrypoint

log = get_logger(__name__)

FUNCTION_NAME = "website_health_check"
ENV_TARGET_URL = "TARGET_URL"
ENV_TARGET_TIMEOUT = "TARGET_TIMEOUT"
DEFAULT_TIMEOUT_SECONDS = 10
EMAIL_SUBJECT = "[18for0] Website DOWN - morning health check failed"


def _down_email_body(target_url: str, detail: str) -> str:
    return (
        "The 18for0 website appears to be DOWN.\n\n"
        f"URL checked : {target_url}\n"
        f"Detail      : {detail}\n\n"
        "This alert was produced by the automated morning health check "
        "(website_health_check Lambda). Investigate immediately; the public "
        "site is unreachable or returning an error status."
    )


@handler_entrypoint(FUNCTION_NAME)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    target_url = os.environ.get(ENV_TARGET_URL)
    if not target_url:
        raise LambdaError(
            f"{ENV_TARGET_URL} env var is required",
            subject=EMAIL_SUBJECT,
            body=_down_email_body(
                target_url="<unset>",
                detail=f"{ENV_TARGET_URL} environment variable was not set.",
            ),
        )

    timeout_seconds = int(os.environ.get(ENV_TARGET_TIMEOUT, DEFAULT_TIMEOUT_SECONDS))

    try:
        with request.urlopen(target_url, timeout=timeout_seconds) as response:
            response_status = response.status
    except error.URLError as err:
        raise LambdaError(
            f"website request failed: {err}",
            subject=EMAIL_SUBJECT,
            body=_down_email_body(target_url, f"request failed ({type(err).__name__}): {err}"),
        ) from err

    if response_status >= 400:
        raise LambdaError(
            f"website returned HTTP {response_status}",
            subject=EMAIL_SUBJECT,
            body=_down_email_body(target_url, f"returned HTTP {response_status}"),
        )

    log.info(
        "website_health_check_ok",
        extra={"ctx_url": target_url, "ctx_status": response_status},
    )
    return {"url": target_url, "status": response_status}
