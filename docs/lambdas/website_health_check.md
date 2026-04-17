# website_health_check

Daily morning reachability probe for the 18for0 public website.

## Purpose

Issues an HTTP `GET` against the configured URL. If the request fails
(connection error, DNS failure, timeout) or the server returns a status
`>= 400`, the Lambda raises `LambdaError` with a website-specific email
subject and body. The shared `handler_entrypoint` decorator routes the
failure to the project's SNS topic, which emails `18for0@gmail.com`.

## Trigger

EventBridge schedule: `cron(0 8 * * ? *)` — 08:00 UTC every day.

The expression uses UTC by design; drift relative to local time across
DST is accepted. Revisit if the business wants wall-clock-stable 08:00.

## Environment variables

| Variable          | Required | Default                         | Purpose                                    |
| ----------------- | -------- | ------------------------------- | ------------------------------------------ |
| `TARGET_URL`      | Yes      | `https://18for0.lennonsec.org`  | URL to probe. Set via Terraform.           |
| `TARGET_TIMEOUT`  | No       | `10`                            | HTTP request timeout, seconds.             |
| `ERROR_TOPIC_ARN` | Yes      | (injected by Terraform)         | SNS topic that receives failure emails.    |
| `LOG_LEVEL`       | No       | `INFO`                          | Standard log level for structured logging. |

## IAM

Inherits the shared Lambda module's policy:

- `AWSLambdaBasicExecutionRole` — CloudWatch Logs.
- `sns:Publish` on `ERROR_TOPIC_ARN` — for failure emails.

No additional permissions required; the handler only uses `urllib`.

## Notification behaviour

- **Success**: logs `website_health_check_ok` at INFO, returns
  `{"url": ..., "status": 200}`. No email sent.
- **Failure**: raises `LambdaError` carrying:
  - `subject = "[18for0] Website DOWN - morning health check failed"`
  - `body = `multi-line message stating URL and failure detail.
  The decorator catches the exception, publishes to SNS, and re-raises so
  Lambda records the invocation as failed.

Subscribers of the `18for0-website-utils-errors` SNS topic receive the
email. `18for0@gmail.com` must be confirmed-subscribed for delivery.

## Local run

```sh
docker compose build website_health_check
docker compose up -d website_health_check
curl -XPOST http://localhost:9001/2015-03-31/functions/function/invocations -d '{}'
docker compose down
```

Override `TARGET_URL` in `docker-compose.yml` or via `.env` to probe a
staging site locally.

## Failure modes

| Scenario                                | Behaviour                                                         |
| --------------------------------------- | ----------------------------------------------------------------- |
| `TARGET_URL` env var missing            | `LambdaError`, notification sent with "env var was not set".      |
| DNS failure / connection refused / TLS  | `LambdaError`, body includes `URLError` detail.                   |
| HTTP status `>= 400`                    | `LambdaError`, body includes the status code.                     |
| Non-failure invocation (2xx, 3xx)       | Returns success dict; no notification.                            |
| SNS publish failure                     | Logged at ERROR (`notify_failure_failed`); original error re-raises. |
