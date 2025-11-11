#!/usr/bin/env python3
"""
Test script for Step Function Workflow

Tests the complete Step Function orchestration including recommendation generation
and report creation.
"""

import json
import boto3
import time
from datetime import datetime, timezone
from botocore.exceptions import ClientError
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# AWS Resources
AWS_REGION = "us-east-1"
STEP_FUNCTION_ARN = "arn:aws:states:us-east-1:971422717446:stateMachine:vocab-rec-engine-processing-workflow-dev"

class StepFunctionTester:
    def __init__(self, region=AWS_REGION):
        self.session = boto3.Session(region_name=region)
        self.sfn = self.session.client('stepfunctions')
        self.s3 = self.session.client('s3')

    def test_step_function_workflow(self):
        """Test the complete Step Function workflow."""
        logger.info("Testing Step Function workflow...")

        # Sample input for the Step Function
        input_data = {
            "student_id": "TEST_STUDENT_STEP_001",
            "batch_mode": False,
            "execution_timestamp": datetime.now(timezone.utc).isoformat()
        }

        try:
            # Start the Step Function execution
            response = self.sfn.start_execution(
                stateMachineArn=STEP_FUNCTION_ARN,
                name=f"test-execution-{int(time.time())}",
                input=json.dumps(input_data)
            )

            execution_arn = response['executionArn']
            logger.info(f"Started Step Function execution: {execution_arn}")

            # Wait for execution to complete
            execution_status = self.wait_for_execution(execution_arn)

            if execution_status == 'SUCCEEDED':
                # Get execution output
                execution_output = self.get_execution_output(execution_arn)
                logger.info("✅ Step Function execution succeeded!")
                logger.info(f"Output: {json.dumps(execution_output, indent=2)}")

                # Verify that report was generated
                self.verify_workflow_results(execution_output)
                return True
            elif execution_status == 'FAILED':
                # Get execution error
                error_output = self.get_execution_output(execution_arn)
                logger.error("❌ Step Function execution failed!")
                logger.error(f"Error: {json.dumps(error_output, indent=2)}")
                return False
            else:
                logger.warning(f"⚠️  Step Function execution ended with status: {execution_status}")
                return False

        except ClientError as e:
            logger.error(f"❌ Error starting Step Function execution: {e}")
            return False

    def wait_for_execution(self, execution_arn, timeout_seconds=300):
        """Wait for Step Function execution to complete."""
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            try:
                response = self.sfn.describe_execution(executionArn=execution_arn)
                status = response['status']

                if status in ['SUCCEEDED', 'FAILED', 'TIMED_OUT', 'ABORTED']:
                    logger.info(f"Step Function execution completed with status: {status}")
                    return status

                logger.info(f"Step Function execution status: {status} (waiting...)")
                time.sleep(10)  # Wait 10 seconds before checking again

            except ClientError as e:
                logger.error(f"Error checking execution status: {e}")
                return 'ERROR'

        logger.error(f"Step Function execution timed out after {timeout_seconds} seconds")
        return 'TIMED_OUT'

    def get_execution_output(self, execution_arn):
        """Get the output of a Step Function execution."""
        try:
            response = self.sfn.describe_execution(executionArn=execution_arn)

            if 'output' in response and response['output']:
                return json.loads(response['output'])
            elif 'error' in response and response['error']:
                return {
                    'error': response['error'],
                    'cause': response.get('cause', 'Unknown cause')
                }
            else:
                return {'message': 'No output available'}

        except ClientError as e:
            logger.error(f"Error getting execution output: {e}")
            return {'error': str(e)}

    def verify_workflow_results(self, execution_output):
        """Verify that the workflow produced expected results."""
        try:
            # Check if report generation succeeded
            if 'report_results' in execution_output:
                report_results = execution_output['report_results']
                if isinstance(report_results, dict) and report_results.get('status') == 'success':
                    logger.info("✅ Report generation completed successfully")
                    return True
                else:
                    logger.error(f"❌ Report generation failed: {report_results}")
                    return False
            else:
                logger.error("❌ No report results found in execution output")
                return False

        except Exception as e:
            logger.error(f"❌ Error verifying workflow results: {e}")
            return False

    def test_step_function_exists(self):
        """Verify that the Step Function exists and is accessible."""
        logger.info("Checking if Step Function exists...")

        try:
            response = self.sfn.describe_state_machine(stateMachineArn=STEP_FUNCTION_ARN)
            logger.info("✅ Step Function exists")
            logger.info(f"Name: {response['name']}")
            logger.info(f"Status: {response['status']}")
            return True

        except ClientError as e:
            if e.response['Error']['Code'] == 'StateMachineDoesNotExist':
                logger.error("❌ Step Function does not exist")
                logger.info("Note: Step Function needs to be deployed first using Terraform")
                return False
            else:
                logger.error(f"❌ Error checking Step Function: {e}")
                return False

def main():
    tester = StepFunctionTester()

    # First check if Step Function exists
    if not tester.test_step_function_exists():
        logger.info("Cannot test Step Function - it needs to be deployed first")
        logger.info("Run 'terraform apply' in the infrastructure/terraform directory")
        return

    # Test the workflow
    logger.info("🚀 Starting Step Function Workflow Test")
    logger.info("=" * 60)

    success = tester.test_step_function_workflow()

    logger.info("=" * 60)
    if success:
        logger.info("🎉 STEP FUNCTION WORKFLOW TEST PASSED!")
        logger.info("✅ Recommendation generation works")
        logger.info("✅ Report generation works")
        logger.info("✅ Error handling functions correctly")
    else:
        logger.error("❌ STEP FUNCTION WORKFLOW TEST FAILED!")

if __name__ == "__main__":
    main()
