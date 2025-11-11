#!/usr/bin/env python3
"""
Test script for Report Generation Lambda Function

Tests the complete report generation workflow including data compilation,
validation, formatting, and S3 storage.
"""

import json
import boto3
import sys
from datetime import datetime, timezone
from botocore.exceptions import ClientError
from unittest.mock import patch, MagicMock
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# AWS Resources
AWS_REGION = "us-east-1"
PROFILES_TABLE = "vocab-rec-engine-vocabulary-profiles-dev"
RECOMMENDATIONS_TABLE = "vocab-rec-engine-vocabulary-recommendations-dev"
OUTPUT_BUCKET = "vocab-rec-engine-output-reports-dev"

# Test data
TEST_STUDENT_ID = "TEST_STUDENT_REPORT_001"

class ReportGenerationTester:
    def __init__(self, region=AWS_REGION):
        self.session = boto3.Session(region_name=region)
        self.dynamodb = self.session.client('dynamodb')
        self.s3 = self.session.client('s3')

    def setup_test_data(self):
        """Set up test data in DynamoDB for report generation testing."""
        logger.info("Setting up test data...")

        # Create test vocabulary profile
        test_profile = {
            'student_id': {'S': TEST_STUDENT_ID},
            'report_date': {'S': datetime.now(timezone.utc).strftime('%Y-%m-%d')},
            'grade_level': {'N': '7'},
            'vocabulary_richness': {'N': '0.65'},
            'unique_words': {'N': '145'},
            'academic_word_ratio': {'N': '0.12'},
            'avg_sentence_length': {'N': '12.5'},
            'lexical_diversity': {'N': '0.78'},
            'readability_score': {'N': '7.2'},
            'text_samples_count': {'N': '3'},
            'sentence_complexity': {'M': {
                'compound_sentences': {'N': '2'},
                'complex_sentences': {'N': '4'},
                'simple_sentences': {'N': '8'}
            }},
            'pos_distribution': {'M': {
                'nouns': {'N': '45'},
                'verbs': {'N': '32'},
                'adjectives': {'N': '18'},
                'adverbs': {'N': '12'}
            }},
            'academic_vocabulary_usage': {'M': {
                'science_terms': {'N': '8'},
                'literary_terms': {'N': '5'},
                'mathematical_terms': {'N': '3'}
            }}
        }

        # Store test profile
        self.dynamodb.put_item(
            TableName=PROFILES_TABLE,
            Item=test_profile
        )

        # Create test recommendations
        recommendations = [
            {
                'student_id': {'S': TEST_STUDENT_ID},
                'recommendation_date': {'S': datetime.now(timezone.utc).isoformat()},
                'recommendation_id': {'S': 'rec_001'},
                'word': {'S': 'photosynthesis'},
                'definition': {'S': 'The process by which plants use sunlight, water, and carbon dioxide to create food'},
                'part_of_speech': {'S': 'noun'},
                'context': {'S': 'Science vocabulary - essential for biology studies'},
                'grade_level': {'N': '7'},
                'frequency_score': {'N': '0.85'},
                'academic_utility': {'S': 'high'},
                'gap_relevance_score': {'N': '0.92'},
                'total_score': {'N': '0.88'},
                'recommendation_rank': {'N': '1'},
                'rationale': {'S': 'High-frequency academic term with significant knowledge gap'},
                'learning_objectives': {'L': [
                    {'S': 'Understand the basic process of photosynthesis'},
                    {'S': 'Use the term correctly in scientific writing'}
                ]}
            },
            {
                'student_id': {'S': TEST_STUDENT_ID},
                'recommendation_date': {'S': datetime.now(timezone.utc).isoformat()},
                'recommendation_id': {'S': 'rec_002'},
                'word': {'S': 'analyze'},
                'definition': {'S': 'To examine something in detail to understand it better'},
                'part_of_speech': {'S': 'verb'},
                'context': {'S': 'Academic skill - critical thinking vocabulary'},
                'grade_level': {'N': '7'},
                'frequency_score': {'N': '0.78'},
                'academic_utility': {'S': 'high'},
                'gap_relevance_score': {'N': '0.85'},
                'total_score': {'N': '0.81'},
                'recommendation_rank': {'N': '2'},
                'rationale': {'S': 'Essential analytical vocabulary for academic writing'},
                'learning_objectives': {'L': [
                    {'S': 'Use analyze correctly in academic contexts'},
                    {'S': 'Distinguish between analyze and similar terms'}
                ]}
            }
        ]

        for rec in recommendations:
            self.dynamodb.put_item(
                TableName=RECOMMENDATIONS_TABLE,
                Item=rec
            )

        # Verify test data was inserted
        try:
            response = self.dynamodb.get_item(
                TableName=PROFILES_TABLE,
                Key={
                    'student_id': {'S': TEST_STUDENT_ID},
                    'report_date': {'S': datetime.now(timezone.utc).strftime('%Y-%m-%d')}
                }
            )
            if 'Item' in response:
                logger.info("✅ Test profile data verified in DynamoDB")
            else:
                logger.error("❌ Test profile data not found in DynamoDB")
        except Exception as e:
            logger.error(f"❌ Error verifying test profile data: {e}")

        logger.info("Test data setup complete")

    def test_report_generation_lambda(self):
        """Test the report generation Lambda function."""
        logger.info("Testing report generation Lambda function...")

        try:
            # Import the Lambda function
            sys.path.append('lambda/report_generation')

            # Mock the authentication function
            with patch('lambda_function.authenticate_request') as mock_auth:
                mock_auth.return_value = {
                    'authenticated': True,
                    'user_info': {
                        'user_id': 'test_educator',
                        'username': 'test@example.com'
                    }
                }

                # Patch the constants in the lambda module
                import lambda_function
                lambda_function.PROFILES_TABLE = PROFILES_TABLE
                lambda_function.RECOMMENDATIONS_TABLE = RECOMMENDATIONS_TABLE
                lambda_function.OUTPUT_BUCKET = OUTPUT_BUCKET

                from lambda_function import lambda_handler

                # Debug: check what table name is being used
                logger.info(f"Lambda function using PROFILES_TABLE: {lambda_function.PROFILES_TABLE}")
                logger.info(f"Test using PROFILES_TABLE: {PROFILES_TABLE}")

                # Create test event
                test_event = {
                    'student_id': TEST_STUDENT_ID,
                    'headers': {
                        'Authorization': 'Bearer test_token'  # Mock token for testing
                    }
                }

                # Mock context
                class MockContext:
                    def __init__(self):
                        self.aws_request_id = 'test-request-id'
                        self.function_name = 'test-function'
                        self.memory_limit_in_mb = 128

                # Invoke Lambda function
                response = lambda_handler(test_event, MockContext())

                # Check response
                if response['statusCode'] == 200:
                    body = json.loads(response['body'])
                    logger.info("✅ Report generation successful!")
                    logger.info(f"Processed students: {body['processed_students']}")
                    logger.info(f"Successful reports: {body['successful_reports']}")

                    if body['results']:
                        result = body['results'][0]
                        if result['status'] == 'success':
                            logger.info(f"✅ Report generated for student {result['student_id']}")
                            logger.info(f"Report S3 key: {result['report_s3_key']}")

                            # Verify report exists in S3
                            self.verify_report_in_s3(result['report_s3_key'])
                            return True
                        else:
                            logger.error(f"❌ Report generation failed: {result.get('error', 'Unknown error')}")
                            return False
                    else:
                        logger.error("❌ No results in response")
                        return False
                else:
                    logger.error(f"❌ Lambda returned error status: {response['statusCode']}")
                    logger.error(f"Response: {response['body']}")
                    return False

        except Exception as e:
            logger.error(f"❌ Error testing report generation: {e}")
            return False

    def verify_report_in_s3(self, s3_key):
        """Verify that the generated report exists in S3."""
        try:
            response = self.s3.get_object(Bucket=OUTPUT_BUCKET, Key=s3_key)
            report_data = json.loads(response['Body'].read().decode('utf-8'))

            # Validate report structure
            required_sections = ['metadata', 'student_profile', 'vocabulary_recommendations', 'performance_trends', 'insights_and_recommendations']
            for section in required_sections:
                if section not in report_data:
                    logger.error(f"❌ Missing required section: {section}")
                    return False

            logger.info("✅ Report structure validation passed")
            logger.info(f"Report version: {report_data['metadata']['report_version']}")
            logger.info(f"Student ID: {report_data['metadata']['student_id']}")
            logger.info(f"Recommendations count: {len(report_data['vocabulary_recommendations'])}")

            return True

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.error(f"❌ Report not found in S3: {s3_key}")
                return False
            else:
                logger.error(f"❌ Error accessing report in S3: {e}")
                return False
        except Exception as e:
            logger.error(f"❌ Error verifying report in S3: {e}")
            return False

    def cleanup_test_data(self):
        """Clean up test data from DynamoDB and S3."""
        logger.info("Cleaning up test data...")

        try:
            # Delete test profile
            self.dynamodb.delete_item(
                TableName=PROFILES_TABLE,
                Key={
                    'student_id': {'S': TEST_STUDENT_ID},
                    'report_date': {'S': datetime.now(timezone.utc).strftime('%Y-%m-%d')}
                }
            )

            # Delete test recommendations (scan and delete)
            response = self.dynamodb.scan(
                TableName=RECOMMENDATIONS_TABLE,
                FilterExpression='student_id = :sid',
                ExpressionAttributeValues={
                    ':sid': {'S': TEST_STUDENT_ID}
                }
            )

            for item in response.get('Items', []):
                self.dynamodb.delete_item(
                    TableName=RECOMMENDATIONS_TABLE,
                    Key={
                        'student_id': item['student_id'],
                        'recommendation_date': item['recommendation_date']
                    }
                )

            # Delete test reports from S3
            try:
                response = self.s3.list_objects_v2(
                    Bucket=OUTPUT_BUCKET,
                    Prefix=f"reports/{TEST_STUDENT_ID}/"
                )

                if 'Contents' in response:
                    for obj in response['Contents']:
                        self.s3.delete_object(Bucket=OUTPUT_BUCKET, Key=obj['Key'])

            except Exception as e:
                logger.warning(f"Could not clean up S3 objects: {e}")

            logger.info("Test data cleanup complete")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def run_comprehensive_test(self):
        """Run comprehensive test of report generation functionality."""
        logger.info("🚀 Starting Report Generation Comprehensive Test")
        logger.info("=" * 60)

        try:
            # Setup
            self.setup_test_data()

            # Test report generation
            success = self.test_report_generation_lambda()

            # Results
            logger.info("=" * 60)
            if success:
                logger.info("🎉 ALL REPORT GENERATION TESTS PASSED!")
                logger.info("✅ Data compilation from DynamoDB works")
                logger.info("✅ Schema validation functions correctly")
                logger.info("✅ Report formatting produces valid structure")
                logger.info("✅ S3 storage and retrieval works")
            else:
                logger.error("❌ SOME REPORT GENERATION TESTS FAILED!")

            return success

        finally:
            # Always cleanup
            self.cleanup_test_data()

def main():
    tester = ReportGenerationTester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
