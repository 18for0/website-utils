# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Python 3.13+ AWS Lambda functions that perform maintenance tasks on a website hosted in AWS. Each module in `src/` is an independent Lambda with a single responsibility. Terraform provisions the Lambdas and supporting AWS resources; GitHub Actions invokes Terraform and runs tests.

## Layout

- `src/` — one Python module per Lambda; each exposes a `lambda_handler(event, context)` entry point.
- `tests/` — pytest unit tests mirroring the `src/` layout.
- `terraform/` — IaC for Lambdas, IAM, and notification plumbing.
- `.github/workflows/` — CI (tests/lint) and CD (terraform plan/apply) pipelines.

## Terraform state

Remote state lives in S3 bucket **`18for0-website-utils`**. The bucket must be created (via a one-time bootstrap) before `terraform init` can succeed — treat it as a prerequisite, not something a normal plan/apply creates. The backend config should reference this bucket.

## Commands

- Run all tests: `pytest`
- Run a single test: `pytest tests/path/to/test_file.py::test_name`
- Terraform: `cd terraform && terraform init && terraform plan`

## Conventions

- **Error handling is load-bearing.** Every Lambda must catch exceptions at the handler boundary, log structured context, and emit a failure notification through the project's notification channel (SNS / CloudWatch alarm — whichever is wired in `terraform/`). Silent failures are not acceptable: a failed run must be visible without anyone reading logs.
- **Single purpose per Lambda.** Don't bundle unrelated maintenance jobs into one function; add a new module and a new Terraform resource instead.
- **Python 3.13+.** Use modern typing (`list[str]`, `X | None`) and `match` where it reads cleanly.
- **Deterministic packaging.** Lambda dependencies should be pinned (requirements.txt or lockfile) so CI builds match what Terraform ships.
