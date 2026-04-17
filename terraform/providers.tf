provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = "18for0-website-utils"
      ManagedBy = "terraform"
    }
  }
}
