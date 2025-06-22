# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "tracking_server_name" {
  description = "Nombre del MLflow tracking server"
  type        = string
  default     = "mlflow-tracking-server-grupo5"
}

variable "instance_type" {
  description = "Tipo de instancia para el MLflow server"
  type        = string
  default     = "ml.t3.medium"

  validation {
    condition = contains([
      "ml.t3.medium", "ml.t3.large", "ml.t3.xlarge",
      "ml.m5.large", "ml.m5.xlarge", "ml.m5.2xlarge"
    ], var.instance_type)
    error_message = "Instance type must be a valid SageMaker MLflow instance type."
  }
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}
