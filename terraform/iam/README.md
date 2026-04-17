# terraform/iam

Codifies the IAM resources that let the GitHub Actions workflows in this repo
assume AWS roles via OIDC:

- `aws_iam_openid_connect_provider.github` — the `token.actions.githubusercontent.com` provider in the account.
- `aws_iam_role.bootstrap` + inline policy — assumed by `.github/workflows/bootstrap.yml` to create the Terraform state bucket.
- `aws_iam_role.deploy` + inline policy — assumed by `.github/workflows/deploy.yml` to apply the main stack in `../`.

State is stored in S3 (`18for0-website-utils-state`, key `iam/terraform.tfstate`) alongside the other modules, but keyed separately.

## Admin-only — no workflow

This module is **not** triggered from a GitHub Actions workflow, by design.
Applying it requires IAM-administrative credentials that neither the bootstrap
role nor the deploy role has (nor should have — a workflow that can rewrite
its own trust policy or policies is a self-escalation hazard). It is run by
hand from an operator workstation with admin AWS credentials.

## When to re-run

Re-apply this module whenever you change the trust conditions, the inline
policy actions, or the OIDC provider config — typically because a workflow
needs a new permission. Order of operations matters:

1. Edit the HCL here.
2. Apply this module manually (sequence below).
3. Only **after** the new permissions are live in AWS, merge the workflow
   change that depends on them into `main`. Merging the workflow first will
   break the deploy until the IAM change lands.

## Apply sequence

From the repo root, with admin creds loaded as the `18for0` profile:

```bash
cd terraform/iam
AWS_PROFILE=18for0 terraform init
AWS_PROFILE=18for0 terraform plan
AWS_PROFILE=18for0 terraform apply
```

Outputs print the OIDC provider ARN and both role ARNs — the role ARNs are
the values used for the `AWS_BOOTSTRAP_ROLE_ARN` and `AWS_DEPLOY_ROLE_ARN`
GitHub repository secrets.

## History

The resources were originally created via `aws iam` CLI calls during initial
project setup, then imported into this Terraform state (see the commit that
introduced this directory). No resources were recreated on import; `plan`
should be clean on a fresh checkout.
