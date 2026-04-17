provider "aws" {
  region = var.aws_region

  # No default_tags: the live IAM resources imported here were created via
  # the AWS CLI without tags. Adding default_tags would show as drift that
  # an apply would silently reconcile. If tags are ever wanted, add them
  # deliberately in a follow-up change and apply manually.
}
