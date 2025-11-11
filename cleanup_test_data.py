#!/usr/bin/env python3
"""
Clean up any leftover test data from previous AWS integration tests.
"""

import boto3
from botocore.exceptions import ClientError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# AWS Resources
AWS_REGION = "us-east-1"
INPUT_BUCKET = "vocab-rec-engine-input-data-dev"
OUTPUT_BUCKET = "vocab-rec-engine-output-reports-dev"
PROFILES_TABLE = "vocab-rec-engine-vocabulary-profiles-dev"
RECOMMENDATIONS_TABLE = "vocab-rec-engine-vocabulary-recommendations-dev"

def cleanup_s3_buckets():
    """Clean up test objects from S3 buckets"""
    logger.info("🧹 Cleaning up S3 test data...")

    s3 = boto3.client('s3', region_name=AWS_REGION)

    try:
        # Clean input bucket
        input_objects = s3.list_objects_v2(Bucket=INPUT_BUCKET, Prefix="raw/TEST_STUDENT_")
        if 'Contents' in input_objects:
            for obj in input_objects['Contents']:
                if 'TEST_STUDENT_' in obj['Key']:
                    s3.delete_object(Bucket=INPUT_BUCKET, Key=obj['Key'])
                    logger.info(f"  Deleted: s3://{INPUT_BUCKET}/{obj['Key']}")

        # Clean output bucket
        output_objects = s3.list_objects_v2(Bucket=OUTPUT_BUCKET, Prefix="reports/TEST_STUDENT_")
        if 'Contents' in output_objects:
            for obj in output_objects['Contents']:
                if 'TEST_STUDENT_' in obj['Key']:
                    s3.delete_object(Bucket=OUTPUT_BUCKET, Key=obj['Key'])
                    logger.info(f"  Deleted: s3://{OUTPUT_BUCKET}/{obj['Key']}")

    except Exception as e:
        logger.error(f"Error cleaning S3: {e}")

def cleanup_dynamodb_tables():
    """Clean up test items from DynamoDB tables"""
    logger.info("🧹 Cleaning up DynamoDB test data...")

    dynamodb = boto3.client('dynamodb', region_name=AWS_REGION)

    try:
        # Clean profiles table
        profiles_response = dynamodb.scan(
            TableName=PROFILES_TABLE,
            FilterExpression='student_id = :sid',
            ExpressionAttributeValues={':sid': {'S': 'TEST_STUDENT_001'}}
        )

        for item in profiles_response.get('Items', []):
            dynamodb.delete_item(
                TableName=PROFILES_TABLE,
                Key={
                    'student_id': item['student_id'],
                    'report_date': item['report_date']
                }
            )
            logger.info(f"  Deleted profile: {item['student_id']['S']}")

        # Clean recommendations table
        recs_response = dynamodb.scan(
            TableName=RECOMMENDATIONS_TABLE,
            FilterExpression='student_id = :sid',
            ExpressionAttributeValues={':sid': {'S': 'TEST_STUDENT_001'}}
        )

        for item in recs_response.get('Items', []):
            dynamodb.delete_item(
                TableName=RECOMMENDATIONS_TABLE,
                Key={
                    'student_id': item['student_id'],
                    'recommendation_date': item['recommendation_date']
                }
            )
            logger.info(f"  Deleted recommendation: {item['word']['S']}")

    except Exception as e:
        logger.error(f"Error cleaning DynamoDB: {e}")

def main():
    logger.info("🚀 Starting Test Data Cleanup")
    logger.info("=" * 50)

    cleanup_s3_buckets()
    cleanup_dynamodb_tables()

    logger.info("✅ Cleanup complete!")

if __name__ == "__main__":
    main()
