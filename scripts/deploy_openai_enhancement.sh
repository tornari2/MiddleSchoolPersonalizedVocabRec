#!/bin/bash
# Deployment script for OpenAI-enhanced vocabulary recommendations
# This script builds and deploys the updated Lambda functions with OpenAI integration

set -e

echo "🚀 Deploying OpenAI-Enhanced Vocabulary Recommendations"
echo "======================================================="

# Configuration
PROJECT_NAME="vocab-rec-engine"
ENVIRONMENT="dev"
AWS_REGION="us-east-1"

echo "📦 Building Lambda layer with OpenAI dependencies..."

# Build the Lambda layer with OpenAI dependencies
cd lambda_layer
./build_layer.sh

echo "✅ Lambda layer built successfully"

echo "🔑 Setting up OpenAI API key in AWS Secrets Manager..."

# Check if OpenAI API key is provided
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY environment variable not set"
    echo "Please set your OpenAI API key:"
    echo "export OPENAI_API_KEY=your_api_key_here"
    exit 1
fi

# Create/update the secret in AWS Secrets Manager
aws secretsmanager create-secret \
    --name "${PROJECT_NAME}/openai-api-key-${ENVIRONMENT}" \
    --description "OpenAI API key for enhanced vocabulary recommendations" \
    --secret-string "$OPENAI_API_KEY" \
    --region "$AWS_REGION" 2>/dev/null || \
aws secretsmanager update-secret \
    --secret-id "${PROJECT_NAME}/openai-api-key-${ENVIRONMENT}" \
    --secret-string "$OPENAI_API_KEY" \
    --region "$AWS_REGION"

echo "✅ OpenAI API key stored securely in AWS Secrets Manager"

echo "🏗️ Deploying Terraform infrastructure..."

# Deploy the infrastructure changes
cd ../infrastructure/terraform
terraform init
terraform plan -var="environment=${ENVIRONMENT}"
terraform apply -auto-approve -var="environment=${ENVIRONMENT}"

echo "✅ Infrastructure deployed successfully"

echo "🧪 Testing the deployment..."

# Test the Lambda function (optional - requires test data)
echo "🔍 You can test the enhanced recommendations by:"
echo "1. Uploading student data to S3 bucket: ${PROJECT_NAME}-input-data-${ENVIRONMENT}"
echo "2. Checking enhanced recommendations in: ${PROJECT_NAME}-output-reports-${ENVIRONMENT}"
echo ""
echo "📊 Monitor OpenAI usage in your OpenAI dashboard"
echo "📈 Check Lambda logs in CloudWatch for performance metrics"

echo ""
echo "🎉 OpenAI-enhanced vocabulary recommendations deployed successfully!"
echo ""
echo "Features enabled:"
echo "✅ GPT-4o-mini integration for intelligent recommendations"
echo "✅ Secure API key storage in AWS Secrets Manager"
echo "✅ Enhanced vocabulary selection based on student writing patterns"
echo "✅ Graceful fallback to standard algorithm if AI fails"
echo "✅ Cost-effective implementation with usage monitoring"
