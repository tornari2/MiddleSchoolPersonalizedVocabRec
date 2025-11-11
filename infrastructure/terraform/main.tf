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
      }
    ]
  })
}

# Cognito User Pool
resource "aws_cognito_user_pool" "educator_pool" {
  name = "${var.project_name}-educator-pool-${var.environment}"

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = true
  }

  auto_verified_attributes = ["email"]

  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = false
  }

  tags = {
    Name        = "Educator User Pool"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Cognito User Pool Client
resource "aws_cognito_user_pool_client" "educator_client" {
  name         = "${var.project_name}-educator-client-${var.environment}"
  user_pool_id = aws_cognito_user_pool.educator_pool.id

  generate_secret = false

  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ]

  token_validity_units {
    id_token      = "hours"
    access_token  = "hours"
    refresh_token = "days"
  }

  id_token_validity      = 24
  access_token_validity  = 24
  refresh_token_validity = 30
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
          "students.$" = "$.students"
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

  depends_on = [
    local_file.lambda_function
  ]
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

# Lambda function source code
resource "local_file" "lambda_function" {
  filename = "${path.module}/../../lambda/data_ingestion/lambda_function.py"
  content  = <<EOF
import json
import boto3
import os
import logging
from typing import Dict, List, Any
from datetime import datetime

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3_client = boto3.client('s3')
dynamodb_client = boto3.client('dynamodb')

# Environment variables
INPUT_BUCKET = os.environ['INPUT_BUCKET']
OUTPUT_BUCKET = os.environ['OUTPUT_BUCKET']
PROFILES_TABLE = os.environ['PROFILES_TABLE']
RECOMMENDATIONS_TABLE = os.environ['RECOMMENDATIONS_TABLE']

def lambda_handler(event, context):
    """
    Lambda function to process student text data from S3.

    Triggered when a new JSONL file is uploaded to the input bucket.
    Processes each student's data and initiates vocabulary analysis.
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        # Extract S3 event information
        for record in event['Records']:
            bucket_name = record['s3']['bucket']['name']
            object_key = record['s3']['object']['key']

            logger.info(f"Processing file: s3://{bucket_name}/{object_key}")

            # Process the uploaded file
            process_student_data_file(bucket_name, object_key)

        return {
            'statusCode': 200,
            'body': json.dumps('Data processing completed successfully')
        }

    except Exception as e:
        logger.error(f"Error processing data: {str(e)}")
        raise e

def process_student_data_file(bucket_name: str, object_key: str):
    """
    Process a JSONL file containing student text data.

    Args:
        bucket_name: S3 bucket name
        object_key: S3 object key (file path)
    """
    try:
        # Read the JSONL file from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        content = response['Body'].read().decode('utf-8')

        # Parse JSONL content
        samples = []
        for line in content.strip().split('\n'):
            if line.strip():
                samples.append(json.loads(line))

        logger.info(f"Loaded {len(samples)} samples from {object_key}")

        # Group samples by student
        student_data = {}
        for sample in samples:
            student_id = sample['student_id']
            if student_id not in student_data:
                student_data[student_id] = []
            student_data[student_id].append(sample)

        logger.info(f"Processing data for {len(student_data)} students")

        # Process each student's data
        for student_id, student_samples in student_data.items():
            process_student_data(student_id, student_samples)

        logger.info(f"Successfully processed data for {len(student_data)} students")

    except Exception as e:
        logger.error(f"Error processing file {object_key}: {str(e)}")
        raise e

def process_student_data(student_id: str, samples: List[Dict[str, Any]]):
    """
    Process data for a single student.

    Args:
        student_id: Unique student identifier
        samples: List of text samples for the student
    """
    try:
        logger.info(f"Processing data for student {student_id}")

        # Extract student metadata from first sample
        first_sample = samples[0]
        grade_level = first_sample.get('grade_level', 7)

        # Analyze vocabulary usage
        vocab_analysis = analyze_student_vocabulary(samples)

        # Store student profile in DynamoDB
        store_student_profile(student_id, grade_level, vocab_analysis, samples)

        # Generate vocabulary recommendations
        recommendations = generate_vocabulary_recommendations(student_id, grade_level, vocab_analysis)

        # Store recommendations in DynamoDB
        store_vocabulary_recommendations(student_id, recommendations)

        # Log processing results
        logger.info(f"Completed processing for student {student_id}: {len(samples)} samples, {len(recommendations)} recommendations")

    except Exception as e:
        logger.error(f"Error processing student {student_id}: {str(e)}")
        raise e

def analyze_student_vocabulary(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze vocabulary usage in student samples.

    Args:
        samples: List of student text samples

    Returns:
        Dictionary with vocabulary analysis results
    """
    # Simple vocabulary analysis (placeholder for more sophisticated analysis)
    all_words = []
    word_frequencies = {}

    for sample in samples:
        text = sample.get('text', '').lower()
        # Simple word extraction (would be more sophisticated in production)
        words = text.replace('.', '').replace(',', '').replace('!', '').replace('?', '').split()

        for word in words:
            if len(word) > 2:  # Skip very short words
                all_words.append(word)
                word_frequencies[word] = word_frequencies.get(word, 0) + 1

    # Sort by frequency
    sorted_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)

    return {
        'total_words': len(all_words),
        'unique_words': len(word_frequencies),
        'most_frequent_words': sorted_words[:20],  # Top 20 words
        'vocabulary_richness': len(word_frequencies) / max(len(all_words), 1),  # Type-token ratio
        'samples_analyzed': len(samples)
    }

def generate_vocabulary_recommendations(student_id: str, grade_level: int, vocab_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate vocabulary recommendations for a student.

    Args:
        student_id: Student identifier
        grade_level: Student's grade level
        vocab_analysis: Results from vocabulary analysis

    Returns:
        List of vocabulary recommendations
    """
    # Placeholder for vocabulary recommendation logic
    # In a real implementation, this would use the reference data and ML models

    recommendations = [
        {
            'word': 'analyze',
            'definition': 'To examine something in detail to understand its nature',
            'context': 'Scientists analyze data to find patterns.',
            'grade_level': grade_level,
            'frequency_score': 0.85,
            'academic_utility': 'high'
        },
        {
            'word': 'evaluate',
            'definition': 'To judge or calculate the quality, importance, or value of something',
            'context': 'Teachers evaluate student work regularly.',
            'grade_level': grade_level,
            'frequency_score': 0.78,
            'academic_utility': 'high'
        },
        {
            'word': 'interpret',
            'definition': 'To explain the meaning of something',
            'context': 'Historians interpret events from the past.',
            'grade_level': grade_level,
            'frequency_score': 0.72,
            'academic_utility': 'medium'
        }
    ]

    return recommendations

def store_student_profile(student_id: str, grade_level: int, vocab_analysis: Dict[str, Any], samples: List[Dict[str, Any]]):
    """
    Store student vocabulary profile in DynamoDB.

    Args:
        student_id: Student identifier
        grade_level: Student's grade level
        vocab_analysis: Vocabulary analysis results
        samples: Original text samples
    """
    try:
        item = {
            'student_id': {'S': student_id},
            'report_date': {'S': datetime.now().isoformat()},
            'grade_level': {'N': str(grade_level)},
            'vocabulary_analysis': {'S': json.dumps(vocab_analysis)},
            'sample_count': {'N': str(len(samples))},
            'total_words': {'N': str(vocab_analysis['total_words'])},
            'unique_words': {'N': str(vocab_analysis['unique_words'])},
            'vocabulary_richness': {'N': str(vocab_analysis['vocabulary_richness'])}
        }

        dynamodb_client.put_item(
            TableName=PROFILES_TABLE,
            Item=item
        )

        logger.info(f"Stored profile for student {student_id}")

    except Exception as e:
        logger.error(f"Error storing profile for student {student_id}: {str(e)}")
        raise e

def store_vocabulary_recommendations(student_id: str, recommendations: List[Dict[str, Any]]):
    """
    Store vocabulary recommendations in DynamoDB.

    Args:
        student_id: Student identifier
        recommendations: List of vocabulary recommendations
    """
    try:
        current_time = datetime.now().isoformat()

        for i, rec in enumerate(recommendations):
            item = {
                'student_id': {'S': student_id},
                'recommendation_date': {'S': current_time},
                'word': {'S': rec['word']},
                'definition': {'S': rec['definition']},
                'context': {'S': rec['context']},
                'grade_level': {'N': str(rec['grade_level'])},
                'frequency_score': {'N': str(rec['frequency_score'])},
                'academic_utility': {'S': rec['academic_utility']},
                'recommendation_id': {'S': f"{student_id}_{i}"}
            }

            dynamodb_client.put_item(
                TableName=RECOMMENDATIONS_TABLE,
                Item=item
            )

        logger.info(f"Stored {len(recommendations)} recommendations for student {student_id}")

    except Exception as e:
        logger.error(f"Error storing recommendations for student {student_id}: {str(e)}")
        raise e
EOF
}

resource "aws_lambda_function" "data_ingestion" {
  function_name    = "${var.project_name}-data-ingestion-${var.environment}"
  runtime         = "python3.9"
  handler         = "lambda_function.lambda_handler"
  timeout         = 300
  memory_size     = 256

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

  depends_on = [
    local_file.recommendation_lambda_function
  ]
}

# Report Generation Lambda ZIP
data "archive_file" "report_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../../lambda/report_generation"
  output_path = "${path.module}/report_lambda_function.zip"

  depends_on = [
    local_file.report_lambda_function
  ]
}

# Recommendation Lambda function source code
resource "local_file" "recommendation_lambda_function" {
  filename = "${path.module}/../../lambda/recommendation_engine/lambda_function.py"
  content  = file("${path.module}/../../lambda/recommendation_engine/lambda_function.py")
}

# Report Generation Lambda function source code
resource "local_file" "report_lambda_function" {
  filename = "${path.module}/../../lambda/report_generation/lambda_function.py"
  content  = file("${path.module}/../../lambda/report_generation/lambda_function.py")
}

resource "aws_lambda_function" "recommendation_engine" {
  function_name    = "${var.project_name}-recommendation-engine-${var.environment}"
  runtime         = "python3.9"
  handler         = "lambda_function.lambda_handler"
  timeout         = 300
  memory_size     = 512

  role             = aws_iam_role.lambda_execution_role.arn

  filename         = data.archive_file.recommendation_lambda_zip.output_path
  source_code_hash = data.archive_file.recommendation_lambda_zip.output_base64sha256

  environment {
    variables = {
      PROFILES_TABLE       = aws_dynamodb_table.vocabulary_profiles.name
      RECOMMENDATIONS_TABLE = aws_dynamodb_table.vocabulary_recommendations.name
      ANALYTICS_TABLE      = aws_dynamodb_table.recommendation_analytics.name
      OUTPUT_BUCKET        = aws_s3_bucket.output_reports.bucket
      USER_POOL_ID         = aws_cognito_user_pool.educator_pool.id
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
  timeout         = 300
  memory_size     = 512

  role             = aws_iam_role.lambda_execution_role.arn

  filename         = data.archive_file.report_lambda_zip.output_path
  source_code_hash = data.archive_file.report_lambda_zip.output_base64sha256

  environment {
    variables = {
      PROFILES_TABLE       = aws_dynamodb_table.vocabulary_profiles.name
      RECOMMENDATIONS_TABLE = aws_dynamodb_table.vocabulary_recommendations.name
      OUTPUT_BUCKET        = aws_s3_bucket.output_reports.bucket
      USER_POOL_ID         = aws_cognito_user_pool.educator_pool.id
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
