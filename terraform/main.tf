data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

data "aws_ecr_repository" "lambda_repository" {
  name = "ecr-${var.lambda_function_name}"
}

resource "aws_s3_bucket" "mlflow_artifacts" {
  bucket = "s3-mlflow-artifacts-${var.tracking_server_name}-01"

  tags = {
    Name        = "MLflow Artifacts"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "mlflow_artifacts_versioning" {
  bucket = aws_s3_bucket.mlflow_artifacts.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "mlflow_artifacts_encryption" {
  bucket = aws_s3_bucket.mlflow_artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "mlflow_artifacts_pab" {
  bucket = aws_s3_bucket.mlflow_artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_iam_role" "mlflow_tracking_server_role" {
  name = "${var.tracking_server_name}-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.tracking_server_name}-role"
    Environment = var.environment
  }
}

resource "aws_iam_policy" "mlflow_s3_access" {
  name        = "policy-${var.tracking_server_name}-s3-access"
  description = "Policy for MLflow tracking server S3 access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
           "s3:GetObject",
           "s3:PutObject",
           "s3:DeleteObject",
           "s3:ListBucket",
           "s3:GetBucketLocation",
           "s3:GetBucketVersioning",
           "s3:ListBucketVersions",
           "s3:GetObjectVersion",
           "s3:DeleteObjectVersion",
           "s3:PutBucketVersioning",
           "glue:*",
           "athena:*",
        ]
        Resource = [
          aws_s3_bucket.mlflow_artifacts.arn,
          "${aws_s3_bucket.mlflow_artifacts.arn}/*",
          "*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream", 
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "sagemaker:*"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_policy" "mlflow_ui_access" {
  name        = "${var.tracking_server_name}-ui-access"
  description = "Policy for MLflow UI access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sagemaker-mlflow:AccessUI",
          "sagemaker-mlflow:GetTrackingServer", 
          "sagemaker-mlflow:ListTrackingServers"
        ]
        Resource = aws_sagemaker_mlflow_tracking_server.mlflow_server.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "mlflow_s3_access_attachment" {
  role       = aws_iam_role.mlflow_tracking_server_role.name
  policy_arn = aws_iam_policy.mlflow_s3_access.arn
}

resource "aws_iam_role_policy_attachment" "sagemaker_execution_role_policy" {
  role       = aws_iam_role.mlflow_tracking_server_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy_attachment" "sagemaker_studio_mlflow_access" {
  role       = aws_iam_role.mlflow_tracking_server_role.name
  policy_arn = aws_iam_policy.mlflow_ui_access.arn
}

resource "aws_sagemaker_mlflow_tracking_server" "mlflow_server" {
  tracking_server_name = var.tracking_server_name
  role_arn             = aws_iam_role.mlflow_tracking_server_role.arn

  tracking_server_size = var.tracking_server_size

  artifact_store_uri = "s3://${aws_s3_bucket.mlflow_artifacts.bucket}/mlflow-artifacts"

  automatic_model_registration = true

  weekly_maintenance_window_start = "Tue:03:00"

  tags = {
    Name        = var.tracking_server_name
    Environment = var.environment
    Service     = "MLflow"
  }

  depends_on = [
    aws_iam_role_policy_attachment.mlflow_s3_access_attachment,
    aws_iam_role_policy_attachment.sagemaker_execution_role_policy
  ]
}

### lambda
resource "aws_iam_role" "lambda_exec" {
  name = "${var.lambda_function_name}-exec-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Agregar esta política para MLflow access desde Lambda
resource "aws_iam_policy" "lambda_mlflow_policy" {
  name        = "policy-${var.lambda_function_name}-mlflow"
  description = "Policy for Lambda to access MLflow tracking server"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sagemaker:*"
          # "sagemaker:DescribeMLflowTrackingServer",
          # "sagemaker:GetMLflowTrackingServerStatus",
          # "sagemaker:ListMLflowTrackingServers"
        ]
        Resource = [
          aws_sagemaker_mlflow_tracking_server.mlflow_server.arn,
          "arn:aws:sagemaker:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:mlflow-tracking-server/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sagemaker-mlflow:*"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketLocation",
          "s3:GetBucketVersioning"
        ]
        Resource = [
          aws_s3_bucket.mlflow_artifacts.arn,
          "${aws_s3_bucket.mlflow_artifacts.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "logs:GetLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Attach la nueva política al rol de Lambda
resource "aws_iam_role_policy_attachment" "lambda_mlflow_policy_attachment" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_mlflow_policy.arn
}

resource "aws_lambda_function" "mlflow_sagemaker_lambda" {
  function_name = var.lambda_function_name
  # handler       = "lambda_function.lambda_handler"
  # runtime       = "python3.9"
  role          = aws_iam_role.lambda_exec.arn
  image_uri = "${data.aws_ecr_repository.lambda_repository.repository_url}:latest"
  package_type  = "Image"
  # s3_bucket     = aws_s3_bucket.mlflow_artifacts.bucket
  # s3_key        = "src/lambda_function.zip"
  # source_code_hash = filebase64sha256("../src/lambda_function.zip")
  timeout          = 60

  environment {
    variables = {
      MLFLOW_TRACKING_URI = aws_sagemaker_mlflow_tracking_server.mlflow_server.tracking_server_url
      MLFLOW_TRACKING_SERVER_ARN = aws_sagemaker_mlflow_tracking_server.mlflow_server.arn
      GIT_PYTHON_REFRESH = "quiet"
    }
  }
  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy_attachment.lambda_mlflow_policy_attachment
  ]
}

resource "aws_api_gateway_rest_api" "api" {
  name        = var.api_gateway_name
  description = "API Gateway for MLflow and SageMaker integration"
}

resource "aws_api_gateway_resource" "lambda_resource" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "invoke"
}

resource "aws_api_gateway_method" "post" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.lambda_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_lambda_permission" "allow_api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.mlflow_sagemaker_lambda.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

resource "aws_api_gateway_integration" "lambda" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.lambda_resource.id
  http_method = aws_api_gateway_method.post.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.mlflow_sagemaker_lambda.invoke_arn
}

resource "aws_api_gateway_deployment" "api_deployment" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  depends_on = [aws_api_gateway_method.post,aws_api_gateway_integration.lambda]
}

resource "aws_api_gateway_stage" "test" {
  stage_name    = "test"
  rest_api_id   = aws_api_gateway_rest_api.api.id
  deployment_id = aws_api_gateway_deployment.api_deployment.id
}

output "api_gateway_invoke_url" {
  value = "https://${aws_api_gateway_rest_api.api.id}.execute-api.${data.aws_region.current.id}.amazonaws.com/${aws_api_gateway_stage.test.stage_name}/invoke"
}

output "lambda_function_arn" {
  value = aws_lambda_function.mlflow_sagemaker_lambda.arn
}

# Outputs
output "mlflow_tracking_server_arn" {
  description = "ARN del MLflow tracking server"
  value       = aws_sagemaker_mlflow_tracking_server.mlflow_server.arn
}

output "mlflow_tracking_server_url" {
  description = "URL del MLflow tracking server"
  value       = aws_sagemaker_mlflow_tracking_server.mlflow_server.tracking_server_url
}

output "mlflow_tracking_server_name" {
  description = "Nombre del MLflow tracking server"
  value       = aws_sagemaker_mlflow_tracking_server.mlflow_server.tracking_server_name
}

output "s3_artifacts_bucket" {
  description = "S3 bucket para artefactos de MLflow"
  value       = aws_s3_bucket.mlflow_artifacts.bucket
}

output "s3_artifacts_uri" {
  description = "URI completa para artefactos de MLflow"
  value       = "s3://${aws_s3_bucket.mlflow_artifacts.bucket}/mlflow-artifacts"
}
