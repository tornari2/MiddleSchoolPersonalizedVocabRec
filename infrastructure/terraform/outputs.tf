output "input_bucket_name" {
  description = "Name of the S3 bucket for input data"
  value       = aws_s3_bucket.input_data.id
}

output "output_bucket_name" {
  description = "Name of the S3 bucket for output reports"
  value       = aws_s3_bucket.output_reports.id
}

output "vocabulary_profiles_table_name" {
  description = "Name of the DynamoDB table for vocabulary profiles"
  value       = aws_dynamodb_table.vocabulary_profiles.name
}

output "vocabulary_recommendations_table_name" {
  description = "Name of the DynamoDB table for vocabulary recommendations"
  value       = aws_dynamodb_table.vocabulary_recommendations.name
}

output "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_execution_role.arn
}

output "step_functions_role_arn" {
  description = "ARN of the Step Functions execution role"
  value       = aws_iam_role.step_functions_role.arn
}


output "step_function_arn" {
  description = "ARN of the Step Function state machine"
  value       = aws_sfn_state_machine.vocabulary_processing_workflow.arn
}

output "step_function_name" {
  description = "Name of the Step Function state machine"
  value       = aws_sfn_state_machine.vocabulary_processing_workflow.name
}
