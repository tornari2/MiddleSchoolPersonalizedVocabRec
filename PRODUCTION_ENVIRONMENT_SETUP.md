# 🚀 Production Environment Setup Guide

## Overview

Your **Personalized Vocabulary Recommendation Engine** production environment has been successfully deployed and cleaned up! All development resources have been removed, leaving only production infrastructure. **No authentication is required** - the system processes student data automatically. This guide provides complete setup instructions and access information.

## ✅ What's Been Deployed

### Infrastructure Components
- **S3 Buckets**: `vocab-rec-engine-input-data-prod`, `vocab-rec-engine-output-reports-prod`
- **DynamoDB Tables**: Vocabulary profiles, recommendations, analytics, and word mastery tracking
- **Lambda Functions**: Data ingestion, recommendation engine, report generation
- **Step Functions**: Processing workflow orchestration
- **Secrets Manager**: OpenAI API key storage
- **CloudWatch**: Monitoring, alarms, and dashboards
- **IAM Roles & Policies**: Secure access management

### Monitoring & Alerting
- **CloudWatch Dashboard**: `vocab-rec-engine-system-dashboard-prod`
- **Error Alarms**: Lambda function failures, Step Function failures
- **Performance Alarms**: High duration warnings
- **Metrics**: Invocations, errors, duration, capacity usage

## 🔧 Required Setup Steps

### 1. Configure OpenAI API Key

**Get your OpenAI API key** from [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

**Option A: Set via AWS CLI (Recommended)**
```bash
aws secretsmanager update-secret \
    --secret-id "vocab-rec-engine/openai-api-key-prod" \
    --secret-string "your_openai_api_key_here"
```

**Option B: Set via Terraform (Alternative)**
```bash
# Edit prod.tfvars and uncomment the openai_api_key line:
nano infrastructure/terraform/prod.tfvars

# Then deploy the infrastructure:
cd infrastructure/terraform
terraform workspace select prod
terraform plan -var-file=prod.tfvars
terraform apply -var-file=prod.tfvars
```

⚠️ **Security Note**: Option B stores your API key in Terraform state and variables. Make sure `prod.tfvars` is in `.gitignore` and never commit it to version control.

**Verify the secret was set:**
```bash
aws secretsmanager get-secret-value \
    --secret-id "vocab-rec-engine/openai-api-key-prod" \
    --query 'SecretString'
```

### 2. Start Using the System

Your vocabulary recommendation system is now ready to use! The system processes student data automatically with no authentication required.

### 3. Enable Enhanced Recommendations (Optional)

Once the OpenAI API key is configured, enhanced recommendations are automatically enabled via Lambda environment variables.

## 📊 Production Environment Details

### Resource Names & ARNs

| Component | Name/ARN |
|-----------|----------|
| **Input S3 Bucket** | `vocab-rec-engine-input-data-prod` |
| **Output S3 Bucket** | `vocab-rec-engine-output-reports-prod` |
| **Vocabulary Profiles Table** | `vocab-rec-engine-vocabulary-profiles-prod` |
| **Recommendations Table** | `vocab-rec-engine-vocabulary-recommendations-prod` |
| **Step Function** | `vocab-rec-engine-processing-workflow-prod` |
| **Cognito User Pool** | `us-east-1_W2d38Uxeb` |
| **Cognito Client ID** | `4gbet2usdcqnae0dp6qdl718h2` |
| **CloudWatch Dashboard** | `vocab-rec-engine-system-dashboard-prod` |

### AWS Account Information
- **Region**: `us-east-1`
- **Account ID**: `971422717446`

## 🚀 Using the Production Environment

### Upload Student Data
```bash
# Upload JSONL file to trigger processing
aws s3 cp student_data.jsonl s3://vocab-rec-engine-input-data-prod/
```

### Monitor Processing
```bash
# Check Step Function executions
aws stepfunctions list-executions \
    --state-machine-arn "arn:aws:states:us-east-1:971422717446:stateMachine:vocab-rec-engine-processing-workflow-prod"

# View CloudWatch dashboard
open "https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=vocab-rec-engine-system-dashboard-prod"
```

### Download Reports
```bash
# List available reports
aws s3 ls s3://vocab-rec-engine-output-reports-prod/reports/ --recursive

# Download specific report
aws s3 cp s3://vocab-rec-engine-output-reports-prod/reports/student_001/2024-01-15_vocabulary_report.json .
```

## 🔍 Monitoring & Troubleshooting

### CloudWatch Alarms
- **Lambda Errors**: Alert when any Lambda function fails
- **Step Function Failures**: Alert when workflow executions fail
- **High Duration**: Alert when Lambda functions run longer than 5 minutes

### View Logs
```bash
# Lambda function logs
aws logs tail "/aws/lambda/vocab-rec-engine-recommendation-engine-prod" --follow

# Step Function logs
aws logs tail "/aws/states/vocab-rec-engine-processing-workflow-prod" --follow
```

### Common Issues

**Data not processing:**
1. Check S3 bucket permissions
2. Verify JSONL file format
3. Check Lambda function logs

**OpenAI recommendations failing:**
1. Verify API key is set in Secrets Manager
2. Check API key validity and quota
3. Review Lambda environment variables


## 💰 Cost Monitoring

### Expected Monthly Costs
- **S3 Storage**: ~$0.05/GB (first 50TB)
- **DynamoDB**: ~$2-5 for 100 students (on-demand pricing)
- **Lambda**: ~$0.20-1.00 (1M requests/month)
- **OpenAI API**: $0.10-0.50 (if enabled)
- **CloudWatch**: ~$1-3 (logs and metrics)
- **Cognito**: Free tier (50k MAU)

**Total Estimate**: **$3-10/month** for MVP usage

### Monitor Costs
```bash
# View billing information
aws ce get-cost-and-usage \
    --time-period Start=2024-01-01,End=2024-01-31 \
    --granularity MONTHLY \
    --metrics "BlendedCost" \
    --group-by Type=DIMENSION,Key=SERVICE
```

## 🔒 Security Features

- **Encryption**: All data encrypted at rest (S3 SSE-KMS, DynamoDB encryption)
- **IAM**: Least-privilege access policies
- **Secrets Manager**: Secure API key storage
- **VPC**: All resources isolated (when configured)

## 📈 Scaling Considerations

### Current Limits
- **Lambda Concurrency**: 1000 concurrent executions (default)
- **DynamoDB**: On-demand scaling (unlimited)
- **S3**: Unlimited storage
- **Step Functions**: 1M executions/month (free tier)

### Scaling Recommendations
- Monitor Lambda concurrency during peak usage
- Consider provisioned concurrency for consistent performance
- Use DynamoDB auto-scaling for cost optimization
- Implement API Gateway for external integrations

## 🔄 Deployment Management

### Infrastructure Management
```bash
# All infrastructure is managed in the production workspace
cd infrastructure/terraform
terraform workspace select prod
```

### Updating Infrastructure
```bash
# Make changes to main.tf, then:
terraform plan -var-file=prod.tfvars
terraform apply -var-file=prod.tfvars
```

## 📞 Support & Next Steps

### Getting Help
1. Check CloudWatch logs for detailed error information
2. Review Lambda function metrics and alarms
3. Verify data formats and permissions

### Next Steps
1. **Load test** with sample data
2. **Set up CI/CD** pipeline for updates
3. **Configure backup** policies
4. **Add API Gateway** for external access
5. **Implement caching** for performance

---

## 🎉 Your Production Environment is Ready!

**Access URLs:**
- **CloudWatch Dashboard**: [View Monitoring](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=vocab-rec-engine-system-dashboard-prod)
- **S3 Buckets**: [View Storage](https://s3.console.aws.amazon.com/s3/buckets/vocab-rec-engine-input-data-prod)
- **DynamoDB Tables**: [View Data](https://console.aws.amazon.com/dynamodbv2/home?region=us-east-1#tables)

**Quick Test:**
```bash
# Test basic connectivity
aws s3 ls s3://vocab-rec-engine-input-data-prod/
```

Your production vocabulary recommendation system is now operational! 🚀
