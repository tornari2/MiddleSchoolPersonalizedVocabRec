#!/usr/bin/env python3
"""
AWS Infrastructure Test Script
Tests the Terraform-deployed AWS resources for the Vocabulary Recommendation Engine.

Run this script to verify your AWS setup before proceeding with Task 2.
"""

import boto3
import json
import sys
from botocore.exceptions import ClientError, NoCredentialsError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# AWS Resources to test
AWS_REGION = "us-east-1"
PROJECT_NAME = "vocab-rec-engine"
ENVIRONMENT = "dev"

RESOURCES = {
    "s3_buckets": [
        f"{PROJECT_NAME}-input-data-{ENVIRONMENT}",
        f"{PROJECT_NAME}-output-reports-{ENVIRONMENT}"
    ],
    "dynamodb_tables": [
        f"{PROJECT_NAME}-vocabulary-profiles-{ENVIRONMENT}",
        f"{PROJECT_NAME}-vocabulary-recommendations-{ENVIRONMENT}"
    ],
    "iam_roles": [
        f"{PROJECT_NAME}-lambda-execution-role-{ENVIRONMENT}",
        f"{PROJECT_NAME}-step-functions-role-{ENVIRONMENT}"
    ],
    "cognito": {
        "user_pool": f"{PROJECT_NAME}-educator-pool-{ENVIRONMENT}",
        "user_pool_client": f"{PROJECT_NAME}-educator-client-{ENVIRONMENT}"
    }
}

class AWSSetupTester:
    def __init__(self, region=AWS_REGION):
        try:
            self.session = boto3.Session(region_name=region)
            self.s3 = self.session.client('s3')
            self.dynamodb = self.session.client('dynamodb')
            self.iam = self.session.client('iam')
            self.cognito = self.session.client('cognito-idp')
            logger.info("✓ AWS credentials found and configured")
        except NoCredentialsError:
            logger.error("✗ No AWS credentials found. Please configure AWS CLI or set environment variables.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"✗ Error initializing AWS clients: {e}")
            sys.exit(1)

    def test_s3_buckets(self):
        """Test S3 bucket existence and permissions"""
        logger.info("\n=== Testing S3 Buckets ===")
        all_passed = True

        for bucket_name in RESOURCES["s3_buckets"]:
            try:
                # Check if bucket exists
                self.s3.head_bucket(Bucket=bucket_name)
                logger.info(f"✓ S3 Bucket '{bucket_name}' exists")

                # Test write permissions (create a test object)
                test_key = "test-connection.txt"
                self.s3.put_object(
                    Bucket=bucket_name,
                    Key=test_key,
                    Body=b"Test connection from AWS setup tester"
                )

                # Test read permissions
                response = self.s3.get_object(Bucket=bucket_name, Key=test_key)
                content = response['Body'].read().decode('utf-8')
                if "Test connection" in content:
                    logger.info(f"✓ S3 Bucket '{bucket_name}' read/write permissions OK")
                else:
                    logger.warning(f"⚠ S3 Bucket '{bucket_name}' content mismatch")

                # Clean up test object
                self.s3.delete_object(Bucket=bucket_name, Key=test_key)

            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    logger.error(f"✗ S3 Bucket '{bucket_name}' does not exist")
                elif e.response['Error']['Code'] == '403':
                    logger.error(f"✗ S3 Bucket '{bucket_name}' access denied")
                else:
                    logger.error(f"✗ S3 Bucket '{bucket_name}' error: {e}")
                all_passed = False
            except Exception as e:
                logger.error(f"✗ Unexpected error testing S3 bucket '{bucket_name}': {e}")
                all_passed = False

        return all_passed

    def test_dynamodb_tables(self):
        """Test DynamoDB table existence and structure"""
        logger.info("\n=== Testing DynamoDB Tables ===")
        all_passed = True

        for table_name in RESOURCES["dynamodb_tables"]:
            try:
                # Get table description
                response = self.dynamodb.describe_table(TableName=table_name)
                table = response['Table']

                logger.info(f"✓ DynamoDB Table '{table_name}' exists")
                logger.info(f"  - Status: {table['TableStatus']}")
                logger.info(f"  - Billing mode: {table['BillingModeSummary']['BillingMode']}")

                # Check key schema
                key_schema = table['KeySchema']
                hash_key = None
                range_key = None

                for key in key_schema:
                    if key['KeyType'] == 'HASH':
                        hash_key = key['AttributeName']
                    elif key['KeyType'] == 'RANGE':
                        range_key = key['AttributeName']

                logger.info(f"  - Hash key: {hash_key}")
                if range_key:
                    logger.info(f"  - Range key: {range_key}")

                # Verify expected schema
                if table_name.endswith('vocabulary-profiles-dev'):
                    if hash_key != 'student_id' or range_key != 'report_date':
                        logger.error(f"✗ Table '{table_name}' has incorrect key schema")
                        all_passed = False
                    else:
                        logger.info(f"✓ Table '{table_name}' key schema is correct")
                elif table_name.endswith('vocabulary-recommendations-dev'):
                    if hash_key != 'student_id' or range_key != 'recommendation_date':
                        logger.error(f"✗ Table '{table_name}' has incorrect key schema")
                        all_passed = False
                    else:
                        logger.info(f"✓ Table '{table_name}' key schema is correct")

                # Test read/write permissions with a test item
                test_item = {
                    'student_id': {'S': 'TEST_STUDENT'},
                    'timestamp': {'S': '2024-01-01T00:00:00Z'},
                    'test_data': {'S': 'Test connection from AWS setup tester'}
                }

                if range_key:
                    test_item[range_key] = {'S': '2024-01-01'}

                # Put test item
                self.dynamodb.put_item(TableName=table_name, Item=test_item)
                logger.info(f"✓ Table '{table_name}' write permissions OK")

                # Get test item
                key_condition = {'student_id': {'S': 'TEST_STUDENT'}}
                if range_key:
                    key_condition[range_key] = {'S': '2024-01-01'}

                response = self.dynamodb.get_item(
                    TableName=table_name,
                    Key=key_condition
                )

                if 'Item' in response:
                    logger.info(f"✓ Table '{table_name}' read permissions OK")
                else:
                    logger.warning(f"⚠ Table '{table_name}' item not found after write")

                # Clean up test item
                self.dynamodb.delete_item(
                    TableName=table_name,
                    Key=key_condition
                )

            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    logger.error(f"✗ DynamoDB Table '{table_name}' does not exist")
                else:
                    logger.error(f"✗ DynamoDB Table '{table_name}' error: {e}")
                all_passed = False
            except Exception as e:
                logger.error(f"✗ Unexpected error testing DynamoDB table '{table_name}': {e}")
                all_passed = False

        return all_passed

    def test_iam_roles(self):
        """Test IAM role existence"""
        logger.info("\n=== Testing IAM Roles ===")
        all_passed = True

        for role_name in RESOURCES["iam_roles"]:
            try:
                response = self.iam.get_role(RoleName=role_name)
                role = response['Role']

                logger.info(f"✓ IAM Role '{role_name}' exists")
                logger.info(f"  - ARN: {role['Arn']}")
                logger.info(f"  - Created: {role['CreateDate']}")

                # Check if role has attached policies
                policies_response = self.iam.list_attached_role_policies(RoleName=role_name)
                attached_policies = policies_response['AttachedPolicies']

                if attached_policies:
                    logger.info(f"  - Attached policies: {len(attached_policies)}")
                    for policy in attached_policies:
                        logger.info(f"    * {policy['PolicyName']}")
                else:
                    logger.warning(f"⚠ IAM Role '{role_name}' has no attached policies")

            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchEntity':
                    logger.error(f"✗ IAM Role '{role_name}' does not exist")
                else:
                    logger.error(f"✗ IAM Role '{role_name}' error: {e}")
                all_passed = False
            except Exception as e:
                logger.error(f"✗ Unexpected error testing IAM role '{role_name}': {e}")
                all_passed = False

        return all_passed

    def test_cognito_setup(self):
        """Test Cognito User Pool and Client"""
        logger.info("\n=== Testing Cognito Setup ===")
        all_passed = True

        user_pool_name = RESOURCES["cognito"]["user_pool"]
        user_pool_client_name = RESOURCES["cognito"]["user_pool_client"]

        try:
            # List user pools and find our pool
            pools_response = self.cognito.list_user_pools(MaxResults=60)
            user_pool = None

            for pool in pools_response['UserPools']:
                if pool['Name'] == user_pool_name:
                    user_pool = pool
                    break

            if user_pool:
                logger.info(f"✓ Cognito User Pool '{user_pool_name}' exists")
                logger.info(f"  - ID: {user_pool['Id']}")
                logger.info(f"  - Created: {user_pool.get('CreationDate', 'Unknown')}")

                # Test user pool client
                clients_response = self.cognito.list_user_pool_clients(
                    UserPoolId=user_pool['Id'],
                    MaxResults=60
                )

                user_pool_client = None
                for client in clients_response['UserPoolClients']:
                    if client['ClientName'] == user_pool_client_name:
                        user_pool_client = client
                        break

                if user_pool_client:
                    logger.info(f"✓ Cognito User Pool Client '{user_pool_client_name}' exists")
                    logger.info(f"  - ID: {user_pool_client['ClientId']}")
                else:
                    logger.error(f"✗ Cognito User Pool Client '{user_pool_client_name}' not found")
                    all_passed = False
            else:
                logger.error(f"✗ Cognito User Pool '{user_pool_name}' not found")
                all_passed = False

        except ClientError as e:
            logger.error(f"✗ Cognito error: {e}")
            all_passed = False
        except Exception as e:
            logger.error(f"✗ Unexpected error testing Cognito: {e}")
            all_passed = False

        return all_passed

    def run_all_tests(self):
        """Run all AWS infrastructure tests"""
        logger.info("🚀 Starting AWS Infrastructure Tests")
        logger.info(f"Region: {AWS_REGION}")
        logger.info(f"Project: {PROJECT_NAME}")
        logger.info(f"Environment: {ENVIRONMENT}")
        logger.info("=" * 50)

        results = {
            "s3_buckets": self.test_s3_buckets(),
            "dynamodb_tables": self.test_dynamodb_tables(),
            "iam_roles": self.test_iam_roles(),
            "cognito": self.test_cognito_setup()
        }

        logger.info("\n" + "=" * 50)
        logger.info("📊 TEST RESULTS SUMMARY")

        all_passed = True
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            logger.info(f"{test_name.replace('_', ' ').title()}: {status}")
            if not passed:
                all_passed = False

        if all_passed:
            logger.info("\n🎉 ALL TESTS PASSED! Your AWS infrastructure is ready.")
            logger.info("You can now proceed to Task 2: Create Reference and Synthetic Data Generator")
        else:
            logger.error("\n⚠️  SOME TESTS FAILED. Please check your Terraform deployment.")
            logger.info("Run 'terraform apply' in the infrastructure/terraform directory")

        return all_passed

def main():
    tester = AWSSetupTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
