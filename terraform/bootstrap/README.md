# Terraform state bootstrap

Creates the S3 bucket `18for0-website-utils-state` that the root
Terraform configuration uses as its remote backend.

**Run once** when provisioning a new AWS account. Two ways:

## Option 1: GitHub Actions (preferred)

Trigger the `bootstrap` workflow manually from the Actions tab
(`workflow_dispatch`). Requirements:

- Repository secret `AWS_BOOTSTRAP_ROLE_ARN` — OIDC role with permission
  to create the S3 bucket and attach versioning / SSE / public-access-block.
- Repository variable `AWS_REGION` (already set for `deploy.yml`).
- A `production` environment with any required approval gates.

The workflow is idempotent: a pre-flight `s3api head-bucket` skips the
apply if the bucket already exists, so re-runs are safe despite the
bootstrap module using local state (discarded with the runner).

## Option 2: Local

```bash
cd terraform/bootstrap
terraform init
terraform apply
```

## Why no backend block?

Bootstrap must keep its own state local because it is what creates the
remote-state bucket. Adding a backend block would create a
chicken-and-egg problem.
