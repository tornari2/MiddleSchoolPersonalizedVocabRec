# Infrastructure Setup Guide

This directory contains Terraform configuration for the Personalized Vocabulary Recommendation Engine AWS infrastructure.

## Prerequisites

1. **Install Terraform** (>= 1.0)
   ```bash
   brew install terraform  # macOS
   # Or download from https://www.terraform.io/downloads
   ```

2. **Configure AWS Credentials**
   ```bash
   aws configure
   # Enter your AWS Access Key ID, Secret Access Key, and region
   ```

3. **Verify AWS CLI Access**
   ```bash
   aws sts get-caller-identity
   ```

## Infrastructure Components

### Created Resources:

1. **S3 Buckets**
   - `vocab-rec-engine-input-data-dev` - For JSONL student text files
   - `vocab-rec-engine-output-reports-dev` - For generated reports

2. **DynamoDB Tables**
   - `vocab-rec-engine-vocabulary-profiles-dev` - Student vocabulary profiles
   - `vocab-rec-engine-vocabulary-recommendations-dev` - Generated recommendations

3. **IAM Roles & Policies**
   - Lambda execution role with S3, DynamoDB, and CloudWatch permissions
   - Step Functions execution role for workflow orchestration

4. **AWS Cognito**
   - User pool for educator authentication
   - User pool client for token-based access

## Deployment Steps

### 1. Initialize Terraform

```bash
cd infrastructure/terraform
terraform init
```

### 2. Review the Plan

```bash
terraform plan
```

This shows you what resources will be created.

### 3. Apply the Configuration

```bash
terraform apply
```

Type `yes` when prompted to confirm.

### 4. Save Outputs

After deployment, save the output values:

```bash
terraform output > ../terraform-outputs.txt
```

These outputs contain:
- S3 bucket names
- DynamoDB table names
- IAM role ARNs
- Cognito user pool IDs

## Configuration

Edit `terraform.tfvars` to customize:

```hcl
aws_region   = "us-east-1"    # Change AWS region
project_name = "vocab-rec-engine"  # Change project name
environment  = "dev"           # Environment: dev, staging, prod
```

## Updating Infrastructure

After making changes to `.tf` files:

```bash
terraform plan   # Review changes
terraform apply  # Apply changes
```

## Destroying Infrastructure

⚠️ **WARNING**: This deletes all resources and data!

```bash
terraform destroy
```

## Costs

All services use serverless/pay-per-request pricing:
- **S3**: ~$0.023/GB per month
- **DynamoDB**: $1.25 per million writes, $0.25 per million reads
- **Lambda**: Free tier: 1M requests/month, 400k GB-seconds compute
- **Cognito**: Free tier: 50k MAU

Expected monthly cost for MVP (20 students): **< $5/month**

## Troubleshooting

### Terraform Init Fails
```bash
rm -rf .terraform
terraform init
```

### AWS Permissions Error
Ensure your AWS user has permissions for:
- S3, DynamoDB, Lambda, IAM, Cognito, Step Functions

### Resource Name Conflicts
Change `project_name` or `environment` in `terraform.tfvars`

## Next Steps

After infrastructure is deployed:

1. **Create Educator User**
   ```bash
   aws cognito-idp admin-create-user \
     --user-pool-id <COGNITO_POOL_ID> \
     --username educator@example.com \
     --user-attributes Name=email,Value=educator@example.com \
     --temporary-password TempPassword123!
   ```

2. **Deploy Lambda Functions** (Task 2-5)

3. **Configure Step Functions** (Task 9)

## Resource Naming Convention

All resources follow the pattern:
```
{project_name}-{resource-type}-{environment}
```

Example: `vocab-rec-engine-input-data-dev`
