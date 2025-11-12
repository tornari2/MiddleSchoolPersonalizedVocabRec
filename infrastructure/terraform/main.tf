terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# S3 Bucket for Input Data (JSONL files)
resource "aws_s3_bucket" "input_data" {
  bucket = "${var.project_name}-input-data-${var.environment}"

  tags = {
    Name        = "Student Text Input Data"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_s3_bucket_versioning" "input_data" {
  bucket = aws_s3_bucket.input_data.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "input_data" {
  bucket = aws_s3_bucket.input_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Bucket for Output Reports
resource "aws_s3_bucket" "output_reports" {
  bucket = "${var.project_name}-output-reports-${var.environment}"

  tags = {
    Name        = "Student Reports Output"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_s3_bucket_versioning" "output_reports" {
  bucket = aws_s3_bucket.output_reports.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "output_reports" {
  bucket = aws_s3_bucket.output_reports.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# DynamoDB Table for Student Vocabulary Profiles
resource "aws_dynamodb_table" "vocabulary_profiles" {
  name           = "${var.project_name}-vocabulary-profiles-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "student_id"
  range_key      = "report_date"

  attribute {
    name = "student_id"
    type = "S"
  }

  attribute {
    name = "report_date"
    type = "S"
  }

  tags = {
    Name        = "Student Vocabulary Profiles"
    Environment = var.environment
    Project     = var.project_name
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }
}

# DynamoDB Table for Vocabulary Recommendations
resource "aws_dynamodb_table" "vocabulary_recommendations" {
  name           = "${var.project_name}-vocabulary-recommendations-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "student_id"
  range_key      = "recommendation_date"

  attribute {
    name = "student_id"
    type = "S"
  }

  attribute {
    name = "recommendation_date"
    type = "S"
  }

  # GSI for querying recommendations by grade level
  attribute {
    name = "grade_level"
    type = "N"
  }

  # GSI for querying recommendations by word
  attribute {
    name = "word"
    type = "S"
  }

  # GSI for querying by academic utility
  attribute {
    name = "academic_utility"
    type = "S"
  }

  attribute {
    name = "frequency_score"
    type = "N"
  }

  # Global Secondary Indexes for enhanced querying
  global_secondary_index {
    name               = "recommendations_by_grade"
    hash_key           = "grade_level"
    range_key          = "recommendation_date"
    projection_type    = "ALL"
  }

  global_secondary_index {
    name               = "recommendations_by_word"
    hash_key           = "word"
    range_key          = "recommendation_date"
    projection_type    = "KEYS_ONLY"
  }

  global_secondary_index {
    name               = "recommendations_by_utility"
    hash_key           = "academic_utility"
    range_key          = "frequency_score"
    projection_type    = "INCLUDE"
    non_key_attributes = ["student_id", "grade_level", "word"]
  }

  tags = {
    Name        = "Vocabulary Recommendations"
    Environment = var.environment
    Project     = var.project_name
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }
}

# DynamoDB Table for Recommendation Analytics
resource "aws_dynamodb_table" "recommendation_analytics" {
  name           = "${var.project_name}-recommendation-analytics-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "analytics_date"
  range_key      = "metric_type"

  attribute {
    name = "analytics_date"
    type = "S"
  }

  attribute {
    name = "metric_type"
    type = "S"
  }

  tags = {
    Name        = "Recommendation Analytics"
    Environment = var.environment
    Project     = var.project_name
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }
}

# DynamoDB Table for Word Mastery Tracking
resource "aws_dynamodb_table" "word_mastery_tracking" {
  name           = "${var.project_name}-word-mastery-tracking-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "student_id"
  range_key      = "word"

  attribute {
    name = "student_id"
    type = "S"
  }

  attribute {
    name = "word"
    type = "S"
  }

  # GSI for querying mastery by date
  attribute {
    name = "mastery_date"
    type = "S"
  }

  global_secondary_index {
    name               = "mastery_by_date"
    hash_key           = "mastery_date"
    range_key          = "student_id"
    projection_type    = "ALL"
  }

  tags = {
    Name        = "Word Mastery Tracking"
    Environment = var.environment
    Project     = var.project_name
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }
}

# IAM Role for Lambda Execution
resource "aws_iam_role" "lambda_execution_role" {
  name = "${var.project_name}-lambda-execution-role-${var.environment}"

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

  tags = {
    Name        = "Lambda Execution Role"
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM Policy for Lambda to access S3, DynamoDB, and CloudWatch
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy-${var.environment}"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.input_data.arn,
          "${aws_s3_bucket.input_data.arn}/*",
          aws_s3_bucket.output_reports.arn,
          "${aws_s3_bucket.output_reports.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchWriteItem"
        ]
        Resource = [
          aws_dynamodb_table.vocabulary_profiles.arn,
          aws_dynamodb_table.vocabulary_recommendations.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey",
          "kms:GenerateDataKeyWithoutPlaintext",
          "kms:DescribeKey"
        ]
        Resource = "arn:aws:kms:${var.aws_region}:${data.aws_caller_identity.current.account_id}:key/*"
      }
    ]
  })
}


# OpenAI API Key Secret for Enhanced Recommendations
resource "aws_secretsmanager_secret" "openai_api_key" {
  name                    = "${var.project_name}/openai-api-key-${var.environment}"
  description             = "OpenAI API key for enhanced vocabulary recommendations"
  recovery_window_in_days = 7

  tags = {
    Name        = "OpenAI API Key"
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM Policy for Lambda to access OpenAI secret
resource "aws_iam_policy" "lambda_openai_secrets" {
  name        = "${var.project_name}-lambda-openai-secrets-${var.environment}"
  description = "Allow Lambda functions to access OpenAI API key"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.openai_api_key.arn
      }
    ]
  })
}

# Attach OpenAI secrets policy to Lambda execution role
resource "aws_iam_role_policy_attachment" "lambda_openai_secrets" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = aws_iam_policy.lambda_openai_secrets.arn
}


# IAM Role for Step Functions
resource "aws_iam_role" "step_functions_role" {
  name = "${var.project_name}-step-functions-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "Step Functions Execution Role"
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM Policy for Step Functions
resource "aws_iam_role_policy" "step_functions_policy" {
  name = "${var.project_name}-step-functions-policy-${var.environment}"
  role = aws_iam_role.step_functions_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = "arn:aws:lambda:${var.aws_region}:*:function:${var.project_name}-*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Step Function State Machine
resource "aws_sfn_state_machine" "vocabulary_processing_workflow" {
  name     = "${var.project_name}-processing-workflow-${var.environment}"
  role_arn = aws_iam_role.step_functions_role.arn

  definition = jsonencode({
    Comment = "Vocabulary Recommendation Engine Processing Workflow"
    StartAt = "ProcessStudentData"
    States = {
      ProcessStudentData = {
        Type = "Task"
        Resource = "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${var.project_name}-recommendation-engine-${var.environment}"
        Parameters = {
          "student_id.$" = "$.student_id"
          "batch_mode.$" = "$.batch_mode"
        }
        ResultPath = "$.recommendation_results"
        Next = "GenerateReports"
        Catch = [
          {
            ErrorEquals = ["States.TaskFailed"]
            Next = "HandleError"
            ResultPath = "$.error"
          }
        ]
      }
      GenerateReports = {
        Type = "Task"
        Resource = "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${var.project_name}-report-generation-${var.environment}"
        Parameters = {
          "student_id.$" = "$.student_id"
          "students.$" = "$.students"
          "batch_mode.$" = "$.batch_mode"
        }
        ResultPath = "$.report_results"
        Next = "Success"
        Catch = [
          {
            ErrorEquals = ["States.TaskFailed"]
            Next = "HandleError"
            ResultPath = "$.error"
          }
        ]
      }
      HandleError = {
        Type = "Task"
        Resource = "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${var.project_name}-error-handler-${var.environment}"
        Parameters = {
          "error.$" = "$.error"
          "execution_arn.$" = "$$.Execution.Id"
        }
        End = true
      }
      Success = {
        Type = "Succeed"
      }
    }
  })

  tags = {
    Name        = "Vocabulary Processing Workflow"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Error Handler Lambda Function (placeholder for now)
resource "aws_lambda_function" "error_handler" {
  function_name = "${var.project_name}-error-handler-${var.environment}"
  runtime       = "python3.12"
  handler       = "lambda_function.lambda_handler"
  role          = aws_iam_role.lambda_execution_role.arn
  timeout       = 30

  # Placeholder code for error handling
  filename         = data.archive_file.placeholder_lambda_zip.output_path
  source_code_hash = data.archive_file.placeholder_lambda_zip.output_base64sha256

  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }

  tags = {
    Name        = "Error Handler Lambda"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Data Ingestion Lambda Function
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../../lambda/data_ingestion"
  output_path = "${path.module}/lambda_function.zip"
}

# Placeholder Lambda ZIP for error handler
data "archive_file" "placeholder_lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/placeholder_lambda_function.zip"

  source {
    content  = <<EOF
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Placeholder error handler Lambda function.
    Replace with actual error handling logic.
    """
    logger.info(f"Error handler received event: {json.dumps(event)}")

    # Placeholder error handling logic
    error_info = event.get('error', {})
    execution_arn = event.get('execution_arn', '')

    logger.error(f"Step Function error in execution {execution_arn}: {error_info}")

    # TODO: Implement proper error handling (notifications, retries, etc.)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Error handled',
            'execution_arn': execution_arn,
            'error_info': error_info
        })
    }
EOF
    filename = "lambda_function.py"
  }
}

# Lambda function source code (removed - using source_dir instead)

# Lambda function source code (removed - using source_dir instead)

resource "aws_lambda_function" "data_ingestion" {
  function_name    = "${var.project_name}-data-ingestion-${var.environment}"
  runtime         = "python3.9"
  handler         = "lambda_function.lambda_handler"
  timeout         = 300
  memory_size     = 512

  role             = aws_iam_role.lambda_execution_role.arn

  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      INPUT_BUCKET         = aws_s3_bucket.input_data.bucket
      OUTPUT_BUCKET        = aws_s3_bucket.output_reports.bucket
      PROFILES_TABLE       = aws_dynamodb_table.vocabulary_profiles.name
      RECOMMENDATIONS_TABLE = aws_dynamodb_table.vocabulary_recommendations.name
    }
  }

  tags = {
    Name        = "Data Ingestion Lambda"
    Environment = var.environment
    Project     = var.project_name
  }
}

# S3 Bucket Notification to trigger Lambda
resource "aws_s3_bucket_notification" "input_data_notification" {
  bucket = aws_s3_bucket.input_data.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.data_ingestion.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = ""
    filter_suffix       = ".jsonl"
  }

  depends_on = [
    aws_lambda_permission.allow_s3_to_invoke_lambda
  ]
}

# Lambda Permission for S3 to invoke
    resource "aws_lambda_permission" "allow_s3_to_invoke_lambda" {
      statement_id  = "AllowS3Invoke"
      action        = "lambda:InvokeFunction"
      function_name = aws_lambda_function.data_ingestion.function_name
      principal     = "s3.amazonaws.com"
      source_arn    = aws_s3_bucket.input_data.arn
    }

# Recommendation Engine Lambda Function
data "archive_file" "recommendation_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../../lambda/recommendation_engine"
  output_path = "${path.module}/recommendation_lambda_function.zip"
}

# Report Generation Lambda ZIP
data "archive_file" "report_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../../lambda/report_generation"
  output_path = "${path.module}/report_lambda_function.zip"
}

# Lambda functions use source_dir instead of local_file resources

resource "aws_lambda_function" "recommendation_engine" {
  function_name    = "${var.project_name}-recommendation-engine-${var.environment}"
  runtime         = "python3.9"
  handler         = "lambda_function.lambda_handler"
  timeout         = 600
  memory_size     = 1024

  role             = aws_iam_role.lambda_execution_role.arn

  filename         = data.archive_file.recommendation_lambda_zip.output_path
  source_code_hash = data.archive_file.recommendation_lambda_zip.output_base64sha256

  environment {
    variables = {
      PROFILES_TABLE       = aws_dynamodb_table.vocabulary_profiles.name
      RECOMMENDATIONS_TABLE = aws_dynamodb_table.vocabulary_recommendations.name
      ANALYTICS_TABLE      = aws_dynamodb_table.recommendation_analytics.name
      OUTPUT_BUCKET        = aws_s3_bucket.output_reports.bucket
      # OpenAI Configuration for Enhanced Recommendations
      OPENAI_API_KEY_SECRET = aws_secretsmanager_secret.openai_api_key.name
      OPENAI_MODEL         = "gpt-4o-mini"
      OPENAI_TEMPERATURE   = "0.2"
      OPENAI_MAX_TOKENS    = "500"
      USE_OPENAI_RECOMMENDATIONS = "true"
    }
  }

  layers = [
    aws_lambda_layer_version.recommendation_dependencies.arn
  ]

  tags = {
    Name        = "Recommendation Engine Lambda"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Report Generation Lambda Function
resource "aws_lambda_function" "report_generation" {
  function_name    = "${var.project_name}-report-generation-${var.environment}"
  runtime         = "python3.9"
  handler         = "lambda_function.lambda_handler"
  timeout         = 600
  memory_size     = 1024

  role             = aws_iam_role.lambda_execution_role.arn

  filename         = data.archive_file.report_lambda_zip.output_path
  source_code_hash = data.archive_file.report_lambda_zip.output_base64sha256

  environment {
    variables = {
      PROFILES_TABLE       = aws_dynamodb_table.vocabulary_profiles.name
      RECOMMENDATIONS_TABLE = aws_dynamodb_table.vocabulary_recommendations.name
      OUTPUT_BUCKET        = aws_s3_bucket.output_reports.bucket
    }
  }

  layers = [
    aws_lambda_layer_version.recommendation_dependencies.arn
  ]

  tags = {
    Name        = "Report Generation Lambda"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Lambda Layer for Recommendation Dependencies
resource "aws_lambda_layer_version" "recommendation_dependencies" {
  layer_name          = "${var.project_name}-recommendation-deps-${var.environment}"
  description         = "Dependencies for recommendation engine (custom modules and reference data)"
  compatible_runtimes = ["python3.9"]

  filename         = "${path.module}/recommendation_layer.zip"
  source_code_hash = filebase64sha256("${path.module}/recommendation_layer.zip")
}

# CloudWatch Alarms for System Monitoring

# Lambda Function Error Alarms
resource "aws_cloudwatch_metric_alarm" "lambda_data_ingestion_errors" {
  alarm_name          = "${var.project_name}-data-ingestion-errors-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1"
  alarm_description   = "Alert when Data Ingestion Lambda function has errors"
  alarm_actions       = []

  dimensions = {
    FunctionName = aws_lambda_function.data_ingestion.function_name
  }

  tags = {
    Name        = "Data Ingestion Lambda Errors Alarm"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_recommendation_engine_errors" {
  alarm_name          = "${var.project_name}-recommendation-engine-errors-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1"
  alarm_description   = "Alert when Recommendation Engine Lambda function has errors"
  alarm_actions       = []

  dimensions = {
    FunctionName = aws_lambda_function.recommendation_engine.function_name
  }

  tags = {
    Name        = "Recommendation Engine Lambda Errors Alarm"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_report_generation_errors" {
  alarm_name          = "${var.project_name}-report-generation-errors-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1"
  alarm_description   = "Alert when Report Generation Lambda function has errors"
  alarm_actions       = []

  dimensions = {
    FunctionName = aws_lambda_function.report_generation.function_name
  }

  tags = {
    Name        = "Report Generation Lambda Errors Alarm"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Step Function Failure Alarm
resource "aws_cloudwatch_metric_alarm" "step_function_failures" {
  alarm_name          = "${var.project_name}-step-function-failures-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ExecutionsFailed"
  namespace           = "AWS/States"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1"
  alarm_description   = "Alert when Step Function executions fail"
  alarm_actions       = []

  dimensions = {
    StateMachineArn = aws_sfn_state_machine.vocabulary_processing_workflow.arn
  }

  tags = {
    Name        = "Step Function Failures Alarm"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Lambda Function Duration Alarms (High Latency)
resource "aws_cloudwatch_metric_alarm" "lambda_high_duration" {
  alarm_name          = "${var.project_name}-lambda-high-duration-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Average"
  threshold           = "300000"  # 5 minutes in milliseconds
  alarm_description   = "Alert when Lambda functions take too long to execute"
  alarm_actions       = []

  dimensions = {
    FunctionName = aws_lambda_function.recommendation_engine.function_name
  }

  tags = {
    Name        = "Lambda High Duration Alarm"
    Environment = var.environment
    Project     = var.project_name
  }
}

# CloudWatch Dashboard for System Monitoring
resource "aws_cloudwatch_dashboard" "vocabulary_system_dashboard" {
  dashboard_name = "${var.project_name}-system-dashboard-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      # Lambda Functions Performance
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", aws_lambda_function.data_ingestion.function_name, { "label": "Data Ingestion Duration" }],
            [".", ".", ".", aws_lambda_function.recommendation_engine.function_name, { "label": "Recommendation Engine Duration" }],
            [".", ".", ".", aws_lambda_function.report_generation.function_name, { "label": "Report Generation Duration" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Lambda Function Duration (ms)"
          period  = 300
        }
      },
      # Lambda Functions Invocations
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.data_ingestion.function_name, { "label": "Data Ingestion Invocations" }],
            [".", ".", ".", aws_lambda_function.recommendation_engine.function_name, { "label": "Recommendation Engine Invocations" }],
            [".", ".", ".", aws_lambda_function.report_generation.function_name, { "label": "Report Generation Invocations" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Lambda Function Invocations"
          period  = 300
        }
      },
      # Lambda Functions Errors
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Lambda", "Errors", "FunctionName", aws_lambda_function.data_ingestion.function_name, { "label": "Data Ingestion Errors" }],
            [".", ".", ".", aws_lambda_function.recommendation_engine.function_name, { "label": "Recommendation Engine Errors" }],
            [".", ".", ".", aws_lambda_function.report_generation.function_name, { "label": "Report Generation Errors" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Lambda Function Errors"
          period  = 300
        }
      },
      # Step Functions Executions
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/States", "ExecutionsStarted", "StateMachineArn", aws_sfn_state_machine.vocabulary_processing_workflow.arn, { "label": "Workflow Executions Started" }],
            [".", "ExecutionsSucceeded", ".", ".", { "label": "Workflow Executions Succeeded" }],
            [".", "ExecutionsFailed", ".", ".", { "label": "Workflow Executions Failed" }],
            [".", "ExecutionsTimedOut", ".", ".", { "label": "Workflow Executions Timed Out" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Step Functions Workflow Status"
          period  = 300
        }
      },
      # DynamoDB Performance
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", aws_dynamodb_table.vocabulary_profiles.name, { "label": "Profiles Read Capacity" }],
            [".", "ConsumedWriteCapacityUnits", ".", ".", { "label": "Profiles Write Capacity" }],
            [".", "ConsumedReadCapacityUnits", "TableName", aws_dynamodb_table.vocabulary_recommendations.name, { "label": "Recommendations Read Capacity" }],
            [".", "ConsumedWriteCapacityUnits", ".", ".", { "label": "Recommendations Write Capacity" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "DynamoDB Capacity Units"
          period  = 300
        }
      },
      # S3 Bucket Metrics
      {
        type   = "metric"
        x      = 12
        y      = 12
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/S3", "NumberOfObjects", "BucketName", aws_s3_bucket.input_data.bucket, "StorageType", "AllStorageTypes", { "label": "Input Data Objects" }],
            [".", ".", "BucketName", aws_s3_bucket.output_reports.bucket, ".", ".", { "label": "Output Reports Objects" }],
            [".", "BucketSizeBytes", "BucketName", aws_s3_bucket.input_data.bucket, "StorageType", "StandardStorage", { "label": "Input Data Size (Bytes)" }],
            [".", ".", "BucketName", aws_s3_bucket.output_reports.bucket, ".", ".", { "label": "Output Reports Size (Bytes)" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "S3 Bucket Metrics"
          period  = 3600
        }
      }
    ]
  })

}
