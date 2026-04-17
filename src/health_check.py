"""Example Lambda: HTTP health-check of the managed website.

Replace the target URL / success criteria with the real checks the website
needs. Kept small on purpose — one maintenance concern per Lambda.
"""

import os
from typing import Any
from urllib import error, request

from src.common import LambdaError, browser_request, get_logger, handler_entrypoint

log = get_logger(__name__)

FUNCTION_NAME = "health_check"
DEFAULT_TIMEOUT = 10


@handler_entrypoint(FUNCTION_NAME)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    url = os.environ.get("TARGET_URL")
    if not url:
        raise LambdaError("TARGET_URL env var is required")

    timeout = int(os.environ.get("TARGET_TIMEOUT", DEFAULT_TIMEOUT))

    try:
        with request.urlopen(browser_request(url), timeout=timeout) as resp:
            status = resp.status
    except error.URLError as err:
        raise LambdaError(f"health check request failed: {err}") from err

    if status >= 400:
        raise LambdaError(f"health check returned HTTP {status}")

    log.info("health_check_ok", extra={"ctx_url": url, "ctx_status": status})
    return {"url": url, "status": status}
