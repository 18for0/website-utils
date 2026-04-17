# State for the GitHub OIDC provider + CI roles lives alongside the main
# project state in 18for0-website-utils-state, under a distinct key so it
# can be managed independently. The state bucket is created by
# terraform/bootstrap, which is the sole module whose state is local.
terraform {
  backend "s3" {
    bucket       = "18for0-website-utils-state"
    key          = "iam/terraform.tfstate"
    region       = "eu-west-1"
    encrypt      = true
    use_lockfile = true
  }
}
