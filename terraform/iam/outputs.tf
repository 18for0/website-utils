output "oidc_provider_arn" {
  value       = aws_iam_openid_connect_provider.github.arn
  description = "ARN of the GitHub Actions OIDC identity provider."
}

output "bootstrap_role_arn" {
  value       = aws_iam_role.bootstrap.arn
  description = "Value to set as the AWS_BOOTSTRAP_ROLE_ARN GitHub secret."
}

output "deploy_role_arn" {
  value       = aws_iam_role.deploy.arn
  description = "Value to set as the AWS_DEPLOY_ROLE_ARN GitHub secret."
}
