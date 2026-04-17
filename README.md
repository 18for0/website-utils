# 18for0-website-utils

AWS Lambda maintenance jobs for the 18for0 website. Each Python module in
`src/` is an independent Lambda with a single responsibility. Terraform
provisions the Lambdas, IAM, scheduling, and an SNS topic that every Lambda
publishes failures to. GitHub Actions runs tests, validates Terraform, and
deploys on merge to `main`.

## Layout

```
src/            # one Python module per Lambda (lambda_handler entry point)
src/common/     # shared logging + SNS failure-notification helpers
tests/          # pytest unit tests mirroring src/
terraform/      # root TF config + reusable lambda module
terraform/bootstrap/  # one-time: creates the S3 state bucket
.github/workflows/    # ci.yml (PRs) and deploy.yml (main)
```

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

pytest                                      # all tests
pytest tests/test_health_check.py::test_returns_status_on_success  # one test
ruff check .
```

## Infrastructure

State is stored in the S3 bucket **`18for0-website-utils`**. The bucket itself
is created by the one-time bootstrap in `terraform/bootstrap/`:

```bash
cd terraform/bootstrap
terraform init && terraform apply
```

After the bucket exists, the root config can initialise against it:

```bash
cd terraform
terraform init
terraform plan -var="alarm_email=you@example.com" -var="target_url=https://..."
```

### Required GitHub configuration for `deploy.yml`

- Secrets: `AWS_DEPLOY_ROLE_ARN`, `ALARM_EMAIL`
- Variables: `AWS_REGION`, `TARGET_URL`

## Adding a new Lambda

1. Create `src/<name>.py` with a `lambda_handler` decorated by
   `@handler_entrypoint("<name>")` from `src.common`. The decorator wires up
   structured logging, catches exceptions, and publishes a failure message to
   SNS before re-raising.
2. Add `tests/test_<name>.py` covering the success path and at least one
   failure path (asserting `notify_failure` is called).
3. Add a module block in `terraform/lambdas.tf` using
   `./modules/lambda`, passing `function_name`, any extra `environment`, and
   an optional `schedule_expression`.

## Error handling contract

Every Lambda failure must be visible without reading logs. The
`@handler_entrypoint` decorator guarantees this by:

- catching all exceptions at the boundary,
- logging with structured context,
- publishing to the SNS topic `ERROR_TOPIC_ARN`, and
- re-raising so the invocation is recorded as failed in CloudWatch.

A CloudWatch metric alarm on each Lambda's `Errors` metric also fires into the
same SNS topic, so even a crash before the decorator runs is surfaced.
