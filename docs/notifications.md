# Failure notifications

Every Lambda in this repo wraps its handler with `handler_entrypoint`
(`src/common/errors.py`). On any uncaught exception the decorator logs a
structured error, publishes a failure notification to the SNS topic named
in `ERROR_TOPIC_ARN`, and re-raises so Lambda records the invocation as
failed.

The shared SNS topic (`18for0-website-utils-errors`) has an email
subscription to `18for0@gmail.com`. Every failure email therefore lands
in that inbox.

## Email content

`src/common/notify.py::build_default_body` renders a human-readable,
multi-line body. Each email contains:

- **Function** — the Lambda name (`function_name` passed to the decorator).
- **Error type** / **Error** — the exception class and `str(exception)`.
- **Region** / **Account** — parsed from `context.invoked_function_arn`.
- **Request ID** — `context.aws_request_id`, the Lambda invocation ID.
- **Log group** / **Log stream** — CloudWatch Logs pointers for the
  specific invocation. Copy the request ID into CloudWatch Logs Insights
  to jump straight to the failure trace.
- **Invocation time (UTC)** / **Invocation source** / **Triggered by** —
  extracted from the EventBridge payload when the Lambda was scheduled.
- **Traceback** — the `traceback.format_exc()` captured at the point the
  decorator caught the exception.
- **Raw event** — the full event JSON, pretty-printed at the end so the
  summary stays readable.

## Per-Lambda overrides

A Lambda can raise `LambdaError(message, subject=..., body=...)` to emit
purpose-specific alert copy instead of the generic body above. This is
used by `website_health_check` to send a short, non-technical "site is
down" alert rather than a stack trace. See that Lambda's doc page for
the rationale.

When `subject` or `body` are set on the exception, they take precedence
over the defaults; otherwise the default format applies.
