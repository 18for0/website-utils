resource "aws_sns_topic" "errors" {
  name = "18for0-website-utils-errors"
}

resource "aws_sns_topic_subscription" "errors_email" {
  topic_arn = aws_sns_topic.errors.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}
