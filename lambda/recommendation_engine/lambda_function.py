#!/usr/bin/env python3
"""
AWS Lambda Function for Vocabulary Recommendation Engine

Generates personalized vocabulary recommendations for students based on their
vocabulary profiles and linguistic analysis stored in DynamoDB.
"""

import json
import boto3
import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys

# Add the project root to the path so we can import our modules
sys.path.append('/opt')  # Lambda layer path

# Import our custom modules (these will be in the Lambda layer)
try:
    from recommendation_engine import RecommendationEngine
    from reference_data_loader import ReferenceDataLoader
    from auth_utils import CognitoJWTVerifier
    from schema_validation import validate_recommendation_result, ValidationError
    from openai_service import OpenAIService
except ImportError:
    # Fallback for local testing
    import sys
    sys.path.append('/Users/michaeltornaritis/Desktop/WK5_MiddleSchoolPersonalizedVocabRec')
    from recommendation_engine import RecommendationEngine
    from reference_data_loader import ReferenceDataLoader
    from auth_utils import CognitoJWTVerifier
    from schema_validation import validate_recommendation_result, ValidationError
    from openai_service import OpenAIService

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb_client = boto3.client('dynamodb')
s3_client = boto3.client('s3')
secrets_client = boto3.client('secretsmanager')

# Environment variables
PROFILES_TABLE = os.environ.get('PROFILES_TABLE', 'vocab-rec-engine-vocabulary-profiles-dev')
RECOMMENDATIONS_TABLE = os.environ.get('RECOMMENDATIONS_TABLE', 'vocab-rec-engine-vocabulary-recommendations-dev')
ANALYTICS_TABLE = os.environ.get('ANALYTICS_TABLE', 'vocab-rec-engine-recommendation-analytics-dev')
OUTPUT_BUCKET = os.environ.get('OUTPUT_BUCKET', 'vocab-rec-engine-output-reports-dev')

# OpenAI Configuration
OPENAI_API_KEY_SECRET = os.environ.get('OPENAI_API_KEY_SECRET')
USE_OPENAI_RECOMMENDATIONS = os.environ.get('USE_OPENAI_RECOMMENDATIONS', 'false').lower() == 'true'

# Cognito configuration
USER_POOL_ID = os.environ.get('USER_POOL_ID', 'us-east-1_4l091bzTD')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

def get_openai_api_key():
    """
    Retrieve OpenAI API key from AWS Secrets Manager.

    Returns:
        str: The OpenAI API key, or None if not configured/enabled
    """
    if not USE_OPENAI_RECOMMENDATIONS or not OPENAI_API_KEY_SECRET:
        return None

    try:
        response = secrets_client.get_secret_value(SecretId=OPENAI_API_KEY_SECRET)

        # Parse the secret (assuming it's stored as plain text)
        if 'SecretString' in response:
            return response['SecretString']
        else:
            # Handle binary secrets (if stored as binary)
            import base64
            return base64.b64decode(response['SecretBinary']).decode('utf-8')

    except Exception as e:
        logger.warning(f"Failed to retrieve OpenAI API key from Secrets Manager: {e}")
        return None

# Initialize JWT verifier (lazy loading for Lambda optimization)
_jwt_verifier = None

def get_jwt_verifier():
    """Get or create JWT verifier instance."""
    global _jwt_verifier
    if _jwt_verifier is None:
        _jwt_verifier = CognitoJWTVerifier(USER_POOL_ID, AWS_REGION)
    return _jwt_verifier

# Initialize reference data loader (global caching for Lambda optimization)
_reference_data_loader = None

def get_reference_data_loader():
    """Get or create reference data loader instance with global caching."""
    global _reference_data_loader
    if _reference_data_loader is None:
        try:
            _reference_data_loader = ReferenceDataLoader()
            logger.info("Initialized reference data loader with global caching")
        except Exception as e:
            logger.error(f"Failed to initialize reference data loader: {e}")
            raise
    return _reference_data_loader

# Initialize spaCy model (global caching for Lambda optimization)
_spacy_model = None

def get_spacy_model(model_name: str = "en_core_web_sm"):
    """Get or load spaCy model with global caching. Falls back to simple processing if spaCy unavailable."""
    global _spacy_model
    if _spacy_model is None:
        try:
            import spacy
            _spacy_model = spacy.load(model_name)
            logger.info(f"Loaded spaCy model '{model_name}' with global caching")
        except Exception as e:
            logger.warning(f"spaCy not available ({e}), using fallback processing")
            # Set a flag to indicate we're using fallback mode
            _spacy_model = "FALLBACK_MODE"
    return _spacy_model

def authenticate_request(event):
    """
    Authenticate the incoming request using JWT verification.
    Allows Step Function invocations without JWT authentication.

    Args:
        event: Lambda event (may contain Authorization header)

    Returns:
        Dict with authentication result
    """
    try:
        # Allow Step Function invocations (they come from AWS Step Functions service)
        # Check for Step Function execution context
        if ('student_id' in event and 'batch_mode' in event) or \
           event.get('source') == 'aws.states':
            logger.info("Step Function invocation detected - bypassing JWT authentication")
            return {
                'authenticated': True,
                'user_info': {
                    'user_id': 'step-function-service',
                    'user_type': 'service'
                }
            }

        # Check for Authorization header
        auth_header = None

        # Check different possible locations for the auth header
        if 'headers' in event:
            auth_header = event['headers'].get('Authorization') or event['headers'].get('authorization')
        elif 'authorizationToken' in event:
            # API Gateway Lambda authorizer format
            auth_header = event['authorizationToken']

        if not auth_header:
            return {
                'authenticated': False,
                'error': 'Missing Authorization header'
            }

        # Verify the JWT token
        verifier = get_jwt_verifier()
        auth_result = verifier.validate_request_auth(auth_header)

        return auth_result

    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return {
            'authenticated': False,
            'error': f'Authentication failed: {str(e)}'
        }

def lambda_handler(event, context):
    """
    Lambda function to generate vocabulary recommendations.

    Triggered by:
    1. Direct invocation with student_id
    2. EventBridge event after profile creation
    3. Step Function orchestration

    Args:
        event: Lambda event containing student information
        context: Lambda context object

    Returns:
        Dict containing recommendation results
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        # Authenticate the request
        auth_result = authenticate_request(event)
        if not auth_result['authenticated']:
            logger.warning(f"Authentication failed: {auth_result.get('error', 'Unknown error')}")
            return {
                'statusCode': 401,
                'body': json.dumps({
                    'error': 'Authentication required',
                    'message': 'Valid JWT token required in Authorization header'
                })
            }

        user_id = auth_result['user_info']['user_id']
        logger.info(f"Authenticated user: {user_id}")

        # Determine how the function was triggered
        if 'student_id' in event:
            # Direct invocation with specific student
            student_ids = [event['student_id']]
        elif 'Records' in event:
            # S3 trigger or other event source
            student_ids = extract_student_ids_from_event(event)
        elif 'students' in event:
            # Batch processing
            student_ids = event['students']
        else:
            # Default: process all recent profiles (last 24 hours)
            student_ids = get_recent_student_profiles()

        logger.info(f"Processing recommendations for {len(student_ids)} students")

        # Process recommendations for each student
        results = []
        for student_id in student_ids:
            try:
                result = process_student_recommendations(student_id)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process recommendations for student {student_id}: {e}")
                results.append({
                    'student_id': student_id,
                    'status': 'error',
                    'error': str(e)
                })

        # Aggregate analytics
        update_recommendation_analytics(results)

        # Return summary
        successful = sum(1 for r in results if r.get('status') == 'success')
        total_recommendations = sum(r.get('recommendation_count', 0) for r in results if r.get('status') == 'success')

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Recommendation generation completed',
                'processed_students': len(results),
                'successful_generations': successful,
                'total_recommendations': total_recommendations,
                'results': results
            })
        }

    except Exception as e:
        logger.error(f"Critical error in recommendation generation: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Recommendation generation failed'
            })
        }

def process_student_recommendations(student_id: str) -> Dict[str, Any]:
    """
    Generate recommendations for a single student.

    Args:
        student_id: Unique student identifier

    Returns:
        Dictionary with processing results
    """
    try:
        logger.info(f"Generating recommendations for student {student_id}")

        # Retrieve student profile from DynamoDB
        profile_data = get_student_profile(student_id)
        if not profile_data:
            raise ValueError(f"No profile found for student {student_id}")

        # Extract linguistic analysis from profile
        linguistic_analysis = extract_linguistic_analysis(profile_data)

        # Initialize recommendation engine with cached reference data loader
        reference_loader = get_reference_data_loader()

        # Enable OpenAI enhancement if configured and API key is available
        use_openai = USE_OPENAI_RECOMMENDATIONS and get_openai_api_key() is not None
        if use_openai:
            logger.info(f"Enabling OpenAI enhancement for student {student_id}")

        engine = RecommendationEngine(
            reference_data_loader=reference_loader,
            use_openai_enhancement=use_openai
        )

        # Generate recommendations
        recommendations = engine.generate_recommendations(
            student_id,
            profile_data,
            linguistic_analysis
        )

        if 'error' in recommendations:
            raise ValueError(f"Recommendation generation failed: {recommendations['error']}")

        # Validate recommendation output
        try:
            validated_recommendations = validate_recommendation_result(recommendations)
            logger.info(f"Successfully validated recommendation output for student {student_id}")
        except ValidationError as e:
            logger.error(f"Output validation failed for student {student_id}: {e.message}")
            # For now, continue with original recommendations but log the error
            # In production, you might want to fail the request
            logger.warning("Continuing with unvalidated recommendations despite validation errors")
            validated_recommendations = recommendations

        # Store recommendations in DynamoDB
        store_recommendations(validated_recommendations)

        # Store recommendations report in S3 (optional)
        store_recommendations_report(recommendations)

        recommendation_count = len(recommendations.get('recommendations', []))

        logger.info(f"Successfully generated {recommendation_count} recommendations for student {student_id}")

        return {
            'student_id': student_id,
            'status': 'success',
            'recommendation_count': recommendation_count,
            'algorithm_version': recommendations.get('recommendation_metadata', {}).get('algorithm_version'),
            'processing_timestamp': recommendations.get('recommendation_metadata', {}).get('processing_timestamp')
        }

    except Exception as e:
        logger.error(f"Error processing recommendations for student {student_id}: {e}")
        return {
            'student_id': student_id,
            'status': 'error',
            'error': str(e)
        }

def get_student_profile(student_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve student vocabulary profile from DynamoDB.

    Args:
        student_id: Student identifier

    Returns:
        Student profile data or None if not found
    """
    try:
        # Get the most recent profile for the student
        response = dynamodb_client.query(
            TableName=PROFILES_TABLE,
            KeyConditionExpression='student_id = :sid',
            ExpressionAttributeValues={
                ':sid': {'S': student_id}
            },
            ScanIndexForward=False,  # Most recent first
            Limit=1
        )

        if not response.get('Items'):
            return None

        # Convert DynamoDB format to regular dict
        item = response['Items'][0]
        profile = dynamodb_item_to_dict(item)

        logger.info(f"Retrieved profile for student {student_id}")
        return profile

    except Exception as e:
        logger.error(f"Error retrieving profile for student {student_id}: {e}")
        return None

def extract_linguistic_analysis(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract linguistic analysis from profile data.

    Args:
        profile_data: Student profile from DynamoDB

    Returns:
        Linguistic analysis dictionary
    """
    # The profile contains aggregated analysis
    analysis = {
        'vocabulary_richness': float(profile_data.get('vocabulary_richness', '0.5')),
        'academic_word_ratio': float(profile_data.get('academic_word_ratio', '0.1')),
        'avg_sentence_length': float(profile_data.get('avg_sentence_length', '8.0')),
        'unique_words': int(profile_data.get('unique_words', '50'))
    }

    return analysis

def store_recommendations(recommendations: Any):
    """
    Store generated recommendations in DynamoDB.

    Args:
        recommendations: Validated RecommendationResult object or dict to store
    """
    try:
        # Handle both Pydantic objects and dictionaries
        if hasattr(recommendations, 'student_id'):
            student_id = recommendations.student_id
            base_timestamp = recommendations.recommendation_metadata.processing_timestamp
            recs = recommendations.recommendations
        else:
            student_id = recommendations['student_id']
            base_timestamp = recommendations['recommendation_metadata']['processing_timestamp']
            recs = recommendations['recommendations']

        # Store each recommendation with unique timestamp
        for i, rec in enumerate(recs):
            # Handle both Pydantic objects and dictionaries
            if hasattr(rec, 'word'):
                rec_data = {
                    'recommendation_id': rec.recommendation_id,
                    'word': rec.word,
                    'definition': rec.definition,
                    'part_of_speech': rec.part_of_speech,
                    'context': rec.context,
                    'grade_level': rec.grade_level,
                    'frequency_score': rec.frequency_score,
                    'academic_utility': rec.academic_utility,
                    'gap_relevance_score': rec.gap_relevance_score,
                    'total_score': rec.total_score,
                    'recommendation_rank': rec.recommendation_rank,
                    'algorithm_version': rec.algorithm_version,
                    'scoring_factors': rec.scoring_factors,
                    'rationale': rec.rationale,
                    'learning_objectives': rec.learning_objectives,
                    'is_viewed': rec.is_viewed,
                    'is_practiced': rec.is_practiced,
                    'created_at': rec.created_at
                }
            else:
                rec_data = rec

            # Add microseconds to make each recommendation timestamp unique
            unique_timestamp = f"{base_timestamp[:-6]}{str(i).zfill(6)}"  # Replace microseconds with counter
            logger.info(f"Storing recommendation {i+1}/10: {rec_data['word']} with timestamp {unique_timestamp}")
            item = {
                'student_id': {'S': student_id},
                'recommendation_date': {'S': unique_timestamp},
                'recommendation_id': {'S': rec_data['recommendation_id']},
                'word': {'S': rec_data['word']},
                'definition': {'S': rec_data['definition']},
                'part_of_speech': {'S': rec_data.get('part_of_speech', 'noun')},
                'context': {'S': rec_data.get('context', '')},
                'grade_level': {'N': str(rec_data['grade_level'])},
                'frequency_score': {'N': str(rec_data['frequency_score'])},
                'academic_utility': {'S': rec_data['academic_utility']},
                'gap_relevance_score': {'N': str(rec_data.get('gap_relevance_score', 0.5))},
                'total_score': {'N': str(rec_data['total_score'])},
                'recommendation_rank': {'N': str(rec_data['recommendation_rank'])},
                'algorithm_version': {'S': rec_data.get('algorithm_version', '1.0')},
                'scoring_factors': {'S': json.dumps(rec_data.get('scoring_factors', {}))},
                'rationale': {'S': rec_data.get('rationale', '')},
                'learning_objectives': {'S': json.dumps(rec_data.get('learning_objectives', []))},
                'is_viewed': {'BOOL': False},
                'is_practiced': {'BOOL': False},
                'created_at': {'S': rec_data.get('created_at', datetime.now().isoformat())}
            }

            dynamodb_client.put_item(
                TableName=RECOMMENDATIONS_TABLE,
                Item=item
            )

        rec_count = len(recs) if 'recs' in locals() else len(recommendations.get('recommendations', []))
        logger.info(f"Stored {rec_count} recommendations for student {student_id}")

    except Exception as e:
        logger.error(f"Error storing recommendations: {e}")
        raise

def store_recommendations_report(recommendations: Dict[str, Any]):
    """
    Store a detailed recommendations report in S3.

    Args:
        recommendations: Complete recommendation data
    """
    try:
        student_id = recommendations['student_id']
        timestamp = recommendations['recommendation_metadata']['processing_timestamp'][:19].replace(':', '-')

        # Create S3 key
        s3_key = f"recommendations/{student_id}/{timestamp}_recommendations.json"

        # Store in S3
        s3_client.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=s3_key,
            Body=json.dumps(recommendations, indent=2),
            ContentType='application/json'
        )

        logger.info(f"Stored recommendations report in S3: s3://{OUTPUT_BUCKET}/{s3_key}")

    except Exception as e:
        logger.error(f"Error storing recommendations report in S3: {e}")
        # Don't raise - S3 storage is optional

def update_recommendation_analytics(results: List[Dict[str, Any]]):
    """
    Update recommendation analytics in DynamoDB.

    Args:
        results: List of recommendation generation results
    """
    try:
        # Calculate daily metrics
        analytics_date = datetime.now().strftime('%Y-%m-%d')
        successful_generations = sum(1 for r in results if r.get('status') == 'success')
        total_recommendations = sum(r.get('recommendation_count', 0) for r in results if r.get('status') == 'success')

        analytics_item = {
            'analytics_date': {'S': analytics_date},
            'metric_type': {'S': 'daily_recommendation_generation'},
            'total_students_processed': {'N': str(len(results))},
            'successful_generations': {'N': str(successful_generations)},
            'total_recommendations_generated': {'N': str(total_recommendations)},
            'average_recommendations_per_student': {'N': str(total_recommendations / max(successful_generations, 1))},
            'processing_timestamp': {'S': datetime.now().isoformat()}
        }

        dynamodb_client.put_item(
            TableName=ANALYTICS_TABLE,
            Item=analytics_item
        )

        logger.info(f"Updated recommendation analytics for {analytics_date}")

    except Exception as e:
        logger.error(f"Error updating recommendation analytics: {e}")
        # Don't raise - analytics are optional

def extract_student_ids_from_event(event: Dict[str, Any]) -> List[str]:
    """
    Extract student IDs from various event formats.

    Args:
        event: Lambda event

    Returns:
        List of student IDs
    """
    # This is a placeholder - implement based on actual event sources
    # Could be from Step Functions, EventBridge, etc.
    return []

def get_recent_student_profiles() -> List[str]:
    """
    Get student IDs for profiles created in the last 24 hours.

    Returns:
        List of student IDs
    """
    # This is a placeholder - implement based on actual requirements
    # Would scan profiles table for recent entries
    return []

def dynamodb_item_to_dict(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert DynamoDB item format to regular Python dict.

    Args:
        item: DynamoDB item

    Returns:
        Regular Python dictionary
    """
    result = {}
    for key, value in item.items():
        if 'S' in value:
            result[key] = value['S']
        elif 'N' in value:
            # Try to convert to int/float
            try:
                if '.' in value['N']:
                    result[key] = float(value['N'])
                else:
                    result[key] = int(value['N'])
            except ValueError:
                result[key] = value['N']
        elif 'BOOL' in value:
            result[key] = value['BOOL']
        elif 'L' in value:
            result[key] = [dynamodb_item_to_dict(subitem) if isinstance(subitem, dict) and ('S' in subitem or 'N' in subitem) else subitem for subitem in value['L']]
        elif 'M' in value:
            result[key] = dynamodb_item_to_dict(value['M'])
        else:
            result[key] = value
    return result
