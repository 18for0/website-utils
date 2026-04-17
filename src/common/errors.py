import functools
import traceback
from collections.abc import Callable
from typing import Any

from .logging_config import configure_logging, get_logger
from .notify import notify_failure

log = get_logger(__name__)

Handler = Callable[[dict[str, Any], Any], Any]


class LambdaError(Exception):
    """Raised for expected, domain-level failures in a Lambda.

    Optional ``subject`` and ``body`` override the generic SNS notification
    text so individual Lambdas can emit purpose-specific alerts without
    reimplementing the notification path.
    """

    def __init__(
        self,
        message: str,
        *,
        subject: str | None = None,
        body: str | None = None,
    ) -> None:
        super().__init__(message)
        self.subject = subject
        self.body = body


def handler_entrypoint(function_name: str) -> Callable[[Handler], Handler]:
    """Decorator that wraps a Lambda handler with logging + failure notification.

    - Configures structured logging once per cold start.
    - Catches every exception, logs it, notifies SNS, then re-raises so that
      Lambda marks the invocation as failed and CloudWatch records the error.
    - Forwards any ``subject`` / ``body`` attributes on the exception (see
      ``LambdaError``) to ``notify_failure`` for Lambda-specific alert copy.
    """

    def decorator(fn: Handler) -> Handler:
        @functools.wraps(fn)
        def wrapper(event: dict[str, Any], context: Any) -> Any:
            configure_logging()
            log.info(
                "lambda_invoked",
                extra={"ctx_function": function_name, "ctx_event": event},
            )
            try:
                result = fn(event, context)
            except Exception as err:
                log.exception(
                    "lambda_failed",
                    extra={"ctx_function": function_name},
                )
                try:
                    notify_failure(
                        function_name=function_name,
                        error=err,
                        event=event,
                        context=context,
                        traceback_text=traceback.format_exc(),
                        subject=getattr(err, "subject", None),
                        body=getattr(err, "body", None),
                    )
                except Exception:
                    log.exception(
                        "notify_failure_failed",
                        extra={"ctx_function": function_name},
                    )
                raise
            log.info("lambda_succeeded", extra={"ctx_function": function_name})
            return result

        return wrapper

    return decorator
