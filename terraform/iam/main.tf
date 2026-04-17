locals {
  oidc_url             = "token.actions.githubusercontent.com"
  oidc_provider_arn    = "arn:aws:iam::${var.aws_account_id}:oidc-provider/${local.oidc_url}"
  oidc_subject_pattern = "repo:${var.github_repo}:ref:refs/heads/main"

  project_lambda_arn = "arn:aws:lambda:${var.aws_region}:${var.aws_account_id}:function:*"
  project_role_arn   = "arn:aws:iam::${var.aws_account_id}:role/*-role"
  project_sns_arn    = "arn:aws:sns:${var.aws_region}:${var.aws_account_id}:18for0-*"
  project_events_arn = "arn:aws:events:${var.aws_region}:${var.aws_account_id}:rule/*"
  project_log_group  = "arn:aws:logs:${var.aws_region}:${var.aws_account_id}:log-group:/aws/lambda/*"

  state_bucket_arn = "arn:aws:s3:::${var.state_bucket}"
}

# GitHub Actions OIDC identity provider.
# The thumbprint is GitHub's root (DigiCert); AWS ignores it at runtime for
# token.actions.githubusercontent.com, but the resource requires a value.
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://${local.oidc_url}"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

# Trust policy shared by both CI roles: restrict assumption to the OIDC
# principal AND to workflows running on main of this exact repo.
data "aws_iam_policy_document" "github_actions_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.oidc_url}:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "${local.oidc_url}:sub"
      values   = [local.oidc_subject_pattern]
    }
  }
}

# ---------------------------------------------------------------------------
# Bootstrap role (used by .github/workflows/bootstrap.yml).
# Scoped to admin of the Terraform state bucket only.
# ---------------------------------------------------------------------------
resource "aws_iam_role" "bootstrap" {
  name        = "github-actions-wu-bootstrap-role"
  description = "GitHub Actions OIDC role for website-utils bootstrap workflow"

  assume_role_policy = data.aws_iam_policy_document.github_actions_trust.json
}

data "aws_iam_policy_document" "bootstrap_inline" {
  statement {
    sid    = "StateBucketAdmin"
    effect = "Allow"
    actions = [
      "s3:CreateBucket",
      "s3:ListBucket",
      "s3:GetBucketLocation",
      "s3:GetBucketVersioning",
      "s3:PutBucketVersioning",
      "s3:GetEncryptionConfiguration",
      "s3:PutEncryptionConfiguration",
      "s3:GetBucketPublicAccessBlock",
      "s3:PutBucketPublicAccessBlock",
      "s3:GetBucketTagging",
      "s3:PutBucketTagging",
      # Read-only getters the AWS provider calls during aws_s3_bucket refresh.
      "s3:GetBucketPolicy",
      "s3:GetBucketAcl",
      "s3:GetBucketCORS",
      "s3:GetBucketLogging",
      "s3:GetBucketWebsite",
      "s3:GetBucketRequestPayment",
      "s3:GetBucketObjectLockConfiguration",
      "s3:GetReplicationConfiguration",
      "s3:GetLifecycleConfiguration",
      "s3:GetAccelerateConfiguration",
      "s3:GetBucketOwnershipControls",
    ]
    resources = [local.state_bucket_arn]
  }
}

resource "aws_iam_role_policy" "bootstrap_inline" {
  name   = "bootstrap-inline"
  role   = aws_iam_role.bootstrap.id
  policy = data.aws_iam_policy_document.bootstrap_inline.json
}

# ---------------------------------------------------------------------------
# Deploy role (used by .github/workflows/deploy.yml).
# Scoped to the resources the main Terraform stack creates.
# ---------------------------------------------------------------------------
resource "aws_iam_role" "deploy" {
  name        = "github-actions-wu-deploy-role"
  description = "GitHub Actions OIDC role for website-utils deploy workflow"

  assume_role_policy = data.aws_iam_policy_document.github_actions_trust.json
}

data "aws_iam_policy_document" "deploy_inline" {
  statement {
    sid    = "TerraformStateRW"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
      "s3:GetBucketLocation",
    ]
    resources = [
      local.state_bucket_arn,
      "${local.state_bucket_arn}/*",
    ]
  }

  statement {
    sid    = "LambdaManage"
    effect = "Allow"
    actions = [
      "lambda:CreateFunction",
      "lambda:DeleteFunction",
      "lambda:Get*",
      "lambda:UpdateFunctionCode",
      "lambda:UpdateFunctionConfiguration",
      "lambda:PublishVersion",
      "lambda:ListVersionsByFunction",
      "lambda:AddPermission",
      "lambda:RemovePermission",
      "lambda:TagResource",
      "lambda:UntagResource",
      "lambda:ListTags",
    ]
    resources = [local.project_lambda_arn]
  }

  statement {
    sid       = "LambdaList"
    effect    = "Allow"
    actions   = ["lambda:ListFunctions"]
    resources = ["*"]
  }

  statement {
    sid    = "IAMForLambdaRoles"
    effect = "Allow"
    actions = [
      "iam:CreateRole",
      "iam:DeleteRole",
      "iam:GetRole",
      "iam:PassRole",
      "iam:UpdateRole",
      "iam:UpdateAssumeRolePolicy",
      "iam:AttachRolePolicy",
      "iam:DetachRolePolicy",
      "iam:PutRolePolicy",
      "iam:DeleteRolePolicy",
      "iam:GetRolePolicy",
      "iam:ListRolePolicies",
      "iam:ListAttachedRolePolicies",
      "iam:ListInstanceProfilesForRole",
      "iam:ListRoleTags",
      "iam:TagRole",
      "iam:UntagRole",
    ]
    resources = [local.project_role_arn]
  }

  statement {
    sid    = "SNSTopicManage"
    effect = "Allow"
    actions = [
      "sns:CreateTopic",
      "sns:DeleteTopic",
      "sns:GetTopicAttributes",
      "sns:SetTopicAttributes",
      "sns:ListTagsForResource",
      "sns:TagResource",
      "sns:UntagResource",
      "sns:Subscribe",
      "sns:Unsubscribe",
      "sns:GetSubscriptionAttributes",
      "sns:SetSubscriptionAttributes",
      "sns:ListSubscriptionsByTopic",
      "sns:ConfirmSubscription",
    ]
    resources = [local.project_sns_arn]
  }

  statement {
    sid       = "SNSList"
    effect    = "Allow"
    actions   = ["sns:ListTopics", "sns:ListSubscriptions"]
    resources = ["*"]
  }

  statement {
    sid    = "EventBridgeSchedule"
    effect = "Allow"
    actions = [
      "events:PutRule",
      "events:DeleteRule",
      "events:DescribeRule",
      "events:ListTagsForResource",
      "events:TagResource",
      "events:UntagResource",
      "events:PutTargets",
      "events:RemoveTargets",
      "events:ListTargetsByRule",
    ]
    resources = [local.project_events_arn]
  }

  statement {
    sid       = "EventBridgeList"
    effect    = "Allow"
    actions   = ["events:ListRules"]
    resources = ["*"]
  }

  statement {
    sid       = "CloudWatchLogsDescribe"
    effect    = "Allow"
    actions   = ["logs:DescribeLogGroups"]
    resources = ["*"]
  }

  statement {
    sid    = "CloudWatchLogsManage"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:DeleteLogGroup",
      "logs:PutRetentionPolicy",
      "logs:DeleteRetentionPolicy",
      "logs:ListTagsForResource",
      "logs:TagResource",
      "logs:UntagResource",
      "logs:TagLogGroup",
      "logs:UntagLogGroup",
      "logs:ListTagsLogGroup",
    ]
    resources = [
      local.project_log_group,
      "${local.project_log_group}:*",
    ]
  }

  statement {
    sid    = "CloudWatchAlarms"
    effect = "Allow"
    actions = [
      "cloudwatch:PutMetricAlarm",
      "cloudwatch:DeleteAlarms",
      "cloudwatch:DescribeAlarms",
      "cloudwatch:ListTagsForResource",
      "cloudwatch:TagResource",
      "cloudwatch:UntagResource",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "deploy_inline" {
  name   = "deploy-inline"
  role   = aws_iam_role.deploy.id
  policy = data.aws_iam_policy_document.deploy_inline.json
}
