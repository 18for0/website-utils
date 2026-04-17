# State is stored in the 18for0-website-utils S3 bucket, created via
# terraform/bootstrap before the first `terraform init` in this directory.
terraform {
  backend "s3" {
    bucket       = "18for0-website-utils"
    key          = "website-utils/terraform.tfstate"
    region       = "eu-west-1"
    encrypt      = true
    use_lockfile = true
  }
}
