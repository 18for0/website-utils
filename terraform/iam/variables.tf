variable "aws_region" {
  type        = string
  default     = "eu-west-1"
  description = "AWS region for project resources referenced by policies."
}

variable "aws_account_id" {
  type        = string
  default     = "487109334257"
  description = "AWS account ID hosting this project."
}

variable "github_repo" {
  type        = string
  default     = "18for0/website-utils"
  description = "GitHub repo (owner/name) allowed to assume the CI roles via OIDC."
}

variable "state_bucket" {
  type        = string
  default     = "18for0-website-utils-state"
  description = "S3 bucket holding Terraform remote state."
}
