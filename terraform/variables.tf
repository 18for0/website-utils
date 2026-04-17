variable "aws_region" {
  type        = string
  default     = "eu-west-1"
  description = "AWS region for all resources."
}

variable "alarm_email" {
  type        = string
  description = "Email address subscribed to the failure-notification SNS topic."
}

variable "target_url" {
  type        = string
  description = "URL the health_check Lambda will probe."
}

variable "website_url" {
  type        = string
  default     = "https://18for0.lennonsec.org"
  description = "URL the website_health_check Lambda probes every morning."
}

variable "website_health_check_timeout_seconds" {
  type        = number
  default     = 10
  description = "HTTP request timeout used by website_health_check."
}
