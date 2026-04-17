output "error_topic_arn" {
  value = aws_sns_topic.errors.arn
}

output "health_check_function_name" {
  value = module.health_check.function_name
}
