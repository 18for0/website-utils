module "health_check" {
  source = "./modules/lambda"

  function_name   = "health_check"
  source_dir      = "${path.root}/../src"
  error_topic_arn = aws_sns_topic.errors.arn

  environment = {
    TARGET_URL = var.target_url
  }

  schedule_expression = "rate(5 minutes)"
}

module "website_health_check" {
  source = "./modules/lambda"

  function_name   = "website_health_check"
  source_dir      = "${path.root}/../src"
  error_topic_arn = aws_sns_topic.errors.arn

  environment = {
    TARGET_URL     = var.website_url
    TARGET_TIMEOUT = tostring(var.website_health_check_timeout_seconds)
  }

  # 08:00 UTC every day. EventBridge cron: minute hour day-of-month month day-of-week year.
  schedule_expression = "cron(0 8 * * ? *)"
}
