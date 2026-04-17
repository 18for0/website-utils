variable "function_name" {
  type        = string
  description = "Lambda function name (also used as the src/ module name)."
}

variable "handler" {
  type        = string
  default     = null
  description = "Handler entrypoint; defaults to src.<function_name>.lambda_handler."
}

variable "source_dir" {
  type        = string
  description = "Absolute path to the repo's src/ directory."
}

variable "error_topic_arn" {
  type        = string
  description = "SNS topic ARN that the Lambda publishes failures to."
}

variable "environment" {
  type        = map(string)
  default     = {}
  description = "Extra environment variables merged into the Lambda config."
}

variable "timeout" {
  type    = number
  default = 30
}

variable "memory_size" {
  type    = number
  default = 256
}

variable "schedule_expression" {
  type        = string
  default     = null
  description = "Optional EventBridge schedule (e.g. \"rate(5 minutes)\")."
}
