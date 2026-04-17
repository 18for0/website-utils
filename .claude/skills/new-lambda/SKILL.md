---
name: new-lambda
description: Scaffold and enforce structure for any new AWS Lambda or new Python code added to this repo. Invoke when the user says "new-lambda", "new lambda", "add a lambda", "new maintenance function", "new code", or as part of the user-level feature-request / "New Feature:" workflow when the feature touches Lambda code in 18for0/website-utils. Use this as the authoritative checklist — do not freelance structure.
---

# new-lambda

Authoritative structure and quality rules for every new Lambda (and any new Python code) in `18for0/website-utils`. Follow the checklist top-to-bottom; skip nothing silently.

## When to invoke

- Explicit: user types `new-lambda`, `/new-lambda`, "new lambda", "add a lambda", "new maintenance function", "new code".
- Implicit: during the user-level `feature-request` or "New Feature:" flow when the feature involves adding or substantially modifying a Lambda module.

## One-time repo bootstrap

If any of the following are missing, set them up before writing the first Lambda that uses this skill:

1. `pre-commit install` — wires `.pre-commit-config.yaml` into git.
2. `pip install pre-commit` (into `.venv`, via `requirements-dev.txt`).
3. `trufflehog` binary installed on PATH (install script: `curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh -s -- -b ~/.local/bin`). Used for secret scanning on every commit — verified-and-unknown secrets fail the commit.
4. `docs/` directory exists with `docs/lambdas/` for per-Lambda docs.
5. Root `Dockerfile.base` and `docker-compose.yml` for local Lambda invocation via the AWS Lambda Runtime Interface Emulator.

## Per-Lambda checklist

For a Lambda named `<name>`, every one of these must exist and be consistent:

- `src/<name>.py` — handler module (flat file). Promote to `src/<name>/handler.py` + helpers **only** when the module exceeds ~200 lines or needs sibling modules.
- `tests/test_<name>.py` — mirrors `src/` one-to-one.
- `docs/lambdas/<name>.md` — purpose, trigger, env vars, IAM, notification wiring, local-run instructions.
- `terraform/<name>.tf` (or entry in an existing `*.tf`) wiring the shared `lambda` module.
- `docker/<name>/Dockerfile` — uses `public.ecr.aws/lambda/python:3.13` base.
- `docker-compose.yml` service entry for `<name>` exposing the RIE port.
- `requirements.txt` updated only if a runtime dep is added. Dev/test deps go in `requirements-dev.txt`.

## Python version

- **Python 3.13.** Do not use 3.14 until Ruff and the AWS Lambda Terraform provider support it (tracked in memory; revisit when that changes).
- `pyproject.toml` pins `requires-python = ">=3.13"` and `tool.ruff.target-version = "py313"` — do not bump without updating the full toolchain.

## Handler module template

Every new Lambda file starts from this skeleton:

```python
#!/usr/bin/env python3
"""<one-line purpose>.

<longer description: what maintenance concern this owns, why it exists,
what triggers it (schedule, event source, etc.).>
"""
from __future__ import annotations

import os
from typing import Any

# Non-stdlib imports go in a guarded block so a missing dep produces a clear,
# actionable error instead of an opaque ModuleNotFoundError at cold start.
try:
    import boto3  # noqa: F401 — example; include only if actually used
except ModuleNotFoundError as err:
    raise RuntimeError(
        f"missing runtime dependency: {err.name}. "
        "Did requirements.txt drift from the deployed image?"
    ) from err

from src.common import LambdaError, get_logger, handler_entrypoint

log = get_logger(__name__)

FUNCTION_NAME = "<name>"
# Declare every env var this Lambda reads as a module-level constant.
ENV_TARGET_URL = "TARGET_URL"
DEFAULT_TIMEOUT = 10


@handler_entrypoint(FUNCTION_NAME)
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    target_url = os.environ.get(ENV_TARGET_URL)
    if not target_url:
        raise LambdaError(f"{ENV_TARGET_URL} env var is required")

    # ... do the work ...

    log.info("<name>_ok", extra={"ctx_target_url": target_url})
    return {"status": "ok"}
```

Rules the template encodes — every one is mandatory:

- **Shebang** `#!/usr/bin/env python3` on line 1 of every `.py` file in `src/`. Yes, even though Lambda imports the module rather than executing it; the shebang is required for consistency and for local CLI invocation.
- `from __future__ import annotations` — always.
- Module docstring on line 3+ explaining the maintenance concern.
- **Import safety**: every non-stdlib import sits inside a `try/except ModuleNotFoundError` with an actionable `RuntimeError`. This is the "aggressive import checking" rule.
- `log = get_logger(__name__)` — never `print`, never `logging.getLogger` directly.
- `FUNCTION_NAME` constant passed to `@handler_entrypoint`.
- Env vars referenced by **constant names** (`ENV_FOO = "FOO"`) — never magic strings scattered through the code.
- `lambda_handler` is the only public entry point. All other logic lives in private helpers (`_do_x`).
- Raise `LambdaError` for expected/domain failures; let the decorator handle logging + SNS notification. Never catch broad `Exception` inside the handler.
- Return a `dict[str, Any]` on success; raise on failure.

## Typing & style

- Modern typing only: `list[str]`, `dict[str, Any]`, `X | None`. No `typing.List`, no `Optional`.
- Public functions fully typed. `Any` requires an inline comment explaining why.
- `match` statements for event-shape dispatch where they read cleanly.
- Meaningful variable names: `target_url`, not `u`; `response_status`, not `rs`. Single-letter names only for trivial loop indices.
- Small, focused functions; early returns over nested conditionals.
- DRY: extract to `src/common/` the moment a second Lambda would copy it.

## Logging & errors

- `LOG_LEVEL` env var controls level at cold start (already honored in `src/common/logging_config.py::configure_logging`). Valid: `DEBUG`, `INFO`, `WARNING`, `ERROR`.
- Log via structured fields: `log.info("event_name", extra={"ctx_key": value})`. The `ctx_` prefix is stripped by `JsonFormatter`; do not interpolate variables into the message string.
- Event names are `snake_case` verbs (`health_check_ok`, `db_snapshot_started`, `cleanup_failed`).
- Any exception escaping the handler will be caught by `handler_entrypoint`, logged at `ERROR`, and routed to SNS via `notify_failure`. Do not reimplement this.

## Configuration

- All config via environment variables, read at module import into typed constants (names) and at handler runtime into values. Fail fast with `LambdaError` when a required var is missing.
- **No AWS SDK calls at import time.** Construct `boto3` clients lazily inside functions. This keeps cold starts fast and unit tests mock-friendly.
- Document every env var in `docs/lambdas/<name>.md`.

## Dependencies & packaging

- `requirements.txt` — **runtime only**. This is what the container/Lambda zip is built from.
- `requirements-dev.txt` — begins with `-r requirements.txt`, then adds test/lint tooling. Never installed into the container image.
- Pin exact versions (`==`) for reproducibility.
- `.venv/` at repo root — already in `.gitignore` and `.dockerignore`. Never commit it.

## Local runnability (Docker)

Every Lambda must be runnable locally via the AWS Lambda Runtime Interface Emulator. `docker/<name>/Dockerfile`:

```dockerfile
FROM public.ecr.aws/lambda/python:3.13

COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

COPY src/ ${LAMBDA_TASK_ROOT}/src/

CMD ["src.<name>.lambda_handler"]
```

`docker-compose.yml` service entry:

```yaml
services:
  <name>:
    build:
      context: .
      dockerfile: docker/<name>/Dockerfile
    ports:
      - "9000:8080"
    environment:
      LOG_LEVEL: DEBUG
      # other env vars the Lambda reads
```

Invoke locally: `curl -XPOST http://localhost:9000/2015-03-31/functions/function/invocations -d '{}'`.

Document the exact invoke command in `docs/lambdas/<name>.md`.

## Tests

- `tests/test_<name>.py` mirrors `src/<name>.py` one-to-one.
- Minimum three tests per Lambda:
  1. **Happy path** — valid event, expected return value.
  2. **Failure path** — asserts `notify_failure` is called (patch `src.common.notify.notify_failure`) and the exception re-raises.
  3. **Env-var validation** — missing required env var raises `LambdaError`.
- Use `moto` for any `boto3` interaction — never hit real AWS.
- No sleeps, no network, no filesystem writes outside `tmp_path`.
- Run the full suite locally before every commit: `pytest` (the pre-commit hook enforces this).

## Terraform wiring

- New Lambda uses the shared module in `terraform/modules/lambda/` — do not write a raw `aws_lambda_function` resource.
- Each Lambda gets its own `terraform/<name>.tf` (or module call in an existing file) with: function name, env vars, IAM policy, schedule/trigger, SNS failure-notification wiring.
- Runtime is `python3.13` everywhere.

## Documentation (`docs/`)

Every code change that adds or alters a Lambda **must** update documentation in the same commit. The pre-commit `docs-freshness` hook enforces this.

- `docs/lambdas/<name>.md` — per-Lambda: purpose, trigger, env vars (with defaults), IAM permissions, notification behavior, local-run command, failure modes.
- `docs/architecture.md` — update when cross-cutting conventions change.
- `README.md` — update only for repo-level changes (bootstrap, CI, new top-level directories).

## Pre-commit gate (`.pre-commit-config.yaml`)

Every commit must pass, in this order:

1. **Ruff lint + format** — no warnings.
2. **Pytest** — full suite green.
3. **trufflehog** — scans staged changes since `HEAD`; fails on any verified or unknown secret.
4. **docs-freshness** — a staged change in `src/` requires a staged change in `docs/`.

Never bypass with `--no-verify`. A failing hook is a real problem; fix the root cause.

## Definition of done

A new Lambda is done only when **all** of the following are true:

- [ ] Handler module matches the template above (shebang, guarded imports, decorator, constants, structured logging).
- [ ] Tests cover happy path, failure path (asserts SNS notify), env-var validation.
- [ ] `pytest` green; `ruff check` clean; `ruff format --check` clean.
- [ ] `docker compose build <name>` succeeds; RIE invoke returns expected shape.
- [ ] `terraform -chdir=terraform validate` clean; `terraform plan` shows only the intended resources.
- [ ] `docs/lambdas/<name>.md` exists and is accurate.
- [ ] Pre-commit hooks all pass on staged changes.
- [ ] `.venv/` not committed; no secrets in diff.
