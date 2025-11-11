#!/usr/bin/env python3
"""
AWS Lambda Function for Student Report Generation

Generates comprehensive student reports combining vocabulary profiles,
recommendations, and performance analytics. Reports are stored in S3
for educator access and analysis.
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
    from reference_data_loader import ReferenceDataLoader
    from auth_utils import CognitoJWTVerifier
except ImportError:
    # Fallback for local testing
    import sys
    sys.path.append('/Users/michaeltornaritis/Desktop/WK5_MiddleSchoolPersonalizedVocabRec')
    from reference_data_loader import ReferenceDataLoader
    from auth_utils import CognitoJWTVerifier

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb_client = boto3.client('dynamodb')
s3_client = boto3.client('s3')

# Environment variables
PROFILES_TABLE = os.environ.get('PROFILES_TABLE', 'vocab-rec-engine-vocabulary-profiles-dev')
RECOMMENDATIONS_TABLE = os.environ.get('RECOMMENDATIONS_TABLE', 'vocab-rec-engine-vocabulary-recommendations-dev')
OUTPUT_BUCKET = os.environ.get('OUTPUT_BUCKET', 'vocab-rec-engine-output-reports-dev')

# Cognito configuration
USER_POOL_ID = os.environ.get('USER_POOL_ID', 'us-east-1_4l091bzTD')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# Initialize JWT verifier (lazy loading for Lambda optimization)
_jwt_verifier = None

def get_jwt_verifier():
    """Get or create JWT verifier instance."""
    global _jwt_verifier
    if _jwt_verifier is None:
        _jwt_verifier = CognitoJWTVerifier(USER_POOL_ID, AWS_REGION)
    return _jwt_verifier

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
        if ('student_id' in event and 'students' in event and 'batch_mode' in event) or \
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
    Lambda function to generate student reports.

    Triggered by:
    1. Direct invocation with student_id
    2. EventBridge event after recommendation generation
    3. Step Function orchestration
    4. Scheduled batch processing

    Args:
        event: Lambda event containing student information
        context: Lambda context object

    Returns:
        Dict containing report generation results
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

        logger.info(f"Generating reports for {len(student_ids)} students")

        # Process reports for each student
        results = []
        for student_id in student_ids:
            try:
                result = generate_student_report(student_id)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to generate report for student {student_id}: {e}")
                results.append({
                    'student_id': student_id,
                    'status': 'error',
                    'error': str(e)
                })

        # Return summary
        successful = sum(1 for r in results if r.get('status') == 'success')

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Report generation completed',
                'processed_students': len(results),
                'successful_reports': successful,
                'results': results
            })
        }

    except Exception as e:
        logger.error(f"Critical error in report generation: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Report generation failed'
            })
        }

def generate_student_report(student_id: str) -> Dict[str, Any]:
    """
    Generate a comprehensive report for a single student.

    Args:
        student_id: Unique student identifier

    Returns:
        Dictionary with report generation results
    """
    try:
        logger.info(f"Generating report for student {student_id}")

        # Compile student data from DynamoDB
        student_data = compile_student_data(student_id)
        if not student_data:
            raise ValueError(f"No data found for student {student_id}")

        # Validate data against schema
        validation_result = validate_student_data(student_data)
        if not validation_result['valid']:
            logger.warning(f"Data validation failed for student {student_id}: {validation_result['errors']}")
            # Continue with report generation but log warnings

        # Generate formatted report
        report = format_student_report(student_data, validation_result)

        # Store report in S3
        s3_key = store_report_in_s3(report)

        logger.info(f"Successfully generated and stored report for student {student_id}")

        return {
            'student_id': student_id,
            'status': 'success',
            'report_s3_key': s3_key,
            'report_url': f"s3://{OUTPUT_BUCKET}/{s3_key}",
            'data_validation_warnings': validation_result.get('warnings', []),
            'generation_timestamp': report['metadata']['generated_at']
        }

    except Exception as e:
        logger.error(f"Error generating report for student {student_id}: {e}")
        return {
            'student_id': student_id,
            'status': 'error',
            'error': str(e)
        }

def compile_student_data(student_id: str) -> Optional[Dict[str, Any]]:
    """
    Compile all available data for a student from DynamoDB.

    Args:
        student_id: Student identifier

    Returns:
        Compiled student data dictionary or None if no data found
    """
    try:
        # Get latest vocabulary profile
        profile = get_student_profile(student_id)
        if not profile:
            logger.warning(f"No vocabulary profile found for student {student_id}")
            return None

        # Get latest recommendations
        recommendations = get_student_recommendations(student_id)

        # Get historical data (last 30 days)
        historical_profiles = get_historical_profiles(student_id, days=30)

        # Compile all data
        student_data = {
            'student_id': student_id,
            'current_profile': profile,
            'current_recommendations': recommendations,
            'historical_profiles': historical_profiles,
            'data_compilation_timestamp': datetime.now().isoformat(),
            'data_sources': {
                'vocabulary_profile': bool(profile),
                'recommendations': bool(recommendations),
                'historical_data': bool(historical_profiles)
            }
        }

        logger.info(f"Compiled data for student {student_id}: profile={bool(profile)}, recommendations={len(recommendations) if recommendations else 0}, historical={len(historical_profiles) if historical_profiles else 0}")
        return student_data

    except Exception as e:
        logger.error(f"Error compiling data for student {student_id}: {e}")
        return None

def get_student_profile(student_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve the most recent student vocabulary profile from DynamoDB.

    Args:
        student_id: Student identifier

    Returns:
        Student profile data or None if not found
    """
    try:
        # Query for the most recent profile
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

        return profile

    except Exception as e:
        logger.error(f"Error retrieving profile for student {student_id}: {e}")
        return None

def get_student_recommendations(student_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve the most recent recommendations for a student from DynamoDB.

    Args:
        student_id: Student identifier

    Returns:
        List of recommendation dictionaries
    """
    try:
        # Query for the most recent recommendations
        response = dynamodb_client.query(
            TableName=RECOMMENDATIONS_TABLE,
            KeyConditionExpression='student_id = :sid',
            ExpressionAttributeValues={
                ':sid': {'S': student_id}
            },
            ScanIndexForward=False,  # Most recent first
            Limit=10  # Get top 10 most recent recommendations
        )

        recommendations = []
        for item in response.get('Items', []):
            rec = dynamodb_item_to_dict(item)
            recommendations.append(rec)

        return recommendations

    except Exception as e:
        logger.error(f"Error retrieving recommendations for student {student_id}: {e}")
        return []

def get_historical_profiles(student_id: str, days: int = 30) -> List[Dict[str, Any]]:
    """
    Retrieve historical vocabulary profiles for trend analysis.

    Args:
        student_id: Student identifier
        days: Number of days of historical data to retrieve

    Returns:
        List of historical profile dictionaries
    """
    try:
        # For now, just get the last few profiles
        # In a production system, you might want to use a GSI or scan with date filtering
        response = dynamodb_client.query(
            TableName=PROFILES_TABLE,
            KeyConditionExpression='student_id = :sid',
            ExpressionAttributeValues={
                ':sid': {'S': student_id}
            },
            ScanIndexForward=False,  # Most recent first
            Limit=10  # Get last 10 profiles
        )

        historical = []
        for item in response.get('Items', []):
            profile = dynamodb_item_to_dict(item)
            historical.append(profile)

        return historical

    except Exception as e:
        logger.error(f"Error retrieving historical profiles for student {student_id}: {e}")
        return []

def validate_student_data(student_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate student data against expected schema and business rules.

    Args:
        student_data: Compiled student data

    Returns:
        Validation result with validity status and any errors/warnings
    """
    errors = []
    warnings = []

    try:
        # Check required fields
        if not student_data.get('student_id'):
            errors.append("Missing student_id")

        if not student_data.get('current_profile'):
            errors.append("Missing current vocabulary profile")
        else:
            profile = student_data['current_profile']

            # Validate profile structure
            required_profile_fields = ['student_id', 'report_date', 'vocabulary_richness', 'unique_words']
            for field in required_profile_fields:
                if field not in profile:
                    errors.append(f"Missing required profile field: {field}")

            # Validate data types and ranges
            if 'vocabulary_richness' in profile:
                richness = profile['vocabulary_richness']
                if not isinstance(richness, (int, float)) or not (0 <= richness <= 1):
                    errors.append("vocabulary_richness must be a number between 0 and 1")

            if 'unique_words' in profile:
                unique_words = profile['unique_words']
                if not isinstance(unique_words, int) or unique_words < 0:
                    errors.append("unique_words must be a non-negative integer")

        # Check recommendations structure
        recommendations = student_data.get('current_recommendations', [])
        if not isinstance(recommendations, list):
            errors.append("current_recommendations must be a list")
        else:
            for i, rec in enumerate(recommendations):
                if not isinstance(rec, dict):
                    errors.append(f"Recommendation {i} must be a dictionary")
                elif 'word' not in rec:
                    warnings.append(f"Recommendation {i} missing word field")

        # Business rule validations
        if student_data.get('current_profile') and student_data.get('current_recommendations'):
            profile = student_data['current_profile']
            recommendations = student_data['current_recommendations']

            # Check if recommendations are appropriate for grade level
            if 'grade_level' in profile and recommendations:
                student_grade = profile['grade_level']
                for rec in recommendations:
                    if 'grade_level' in rec and abs(rec['grade_level'] - student_grade) > 1:
                        warnings.append(f"Recommendation grade level ({rec['grade_level']}) differs significantly from student grade ({student_grade})")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'validation_timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error during data validation: {e}")
        return {
            'valid': False,
            'errors': [f"Validation failed: {str(e)}"],
            'warnings': warnings,
            'validation_timestamp': datetime.now().isoformat()
        }

def format_student_report(student_data: Dict[str, Any], validation_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format the compiled student data into a comprehensive report structure.

    Args:
        student_data: Compiled student data
        validation_result: Data validation results

    Returns:
        Formatted report dictionary
    """
    try:
        student_id = student_data['student_id']
        profile = student_data.get('current_profile', {})
        recommendations = student_data.get('current_recommendations', [])
        historical = student_data.get('historical_profiles', [])

        # Extract key metrics from current profile
        current_metrics = extract_profile_metrics(profile)

        # Calculate trends from historical data
        trends = calculate_performance_trends(historical, profile)

        # Format recommendations
        formatted_recommendations = format_recommendations(recommendations)

        # Generate insights and recommendations
        insights = generate_student_insights(current_metrics, trends, recommendations)

        # Create report structure
        report = {
            'metadata': {
                'student_id': student_id,
                'generated_at': datetime.now().isoformat(),
                'report_version': '1.0',
                'data_compilation_timestamp': student_data.get('data_compilation_timestamp'),
                'data_sources': student_data.get('data_sources', {}),
                'validation_status': 'valid' if validation_result['valid'] else 'invalid',
                'validation_warnings': validation_result.get('warnings', []),
                'validation_errors': validation_result.get('errors', [])
            },
            'student_profile': {
                'basic_info': {
                    'student_id': student_id,
                    'grade_level': profile.get('grade_level', 'Unknown'),
                    'report_date': profile.get('report_date', 'Unknown'),
                    'text_samples_analyzed': profile.get('text_samples_count', 0)
                },
                'vocabulary_metrics': current_metrics,
                'linguistic_features': extract_linguistic_features(profile)
            },
            'vocabulary_recommendations': formatted_recommendations,
            'performance_trends': trends,
            'insights_and_recommendations': insights,
            'learning_plan': generate_learning_plan(insights, recommendations)
        }

        return report

    except Exception as e:
        logger.error(f"Error formatting student report: {e}")
        raise

def extract_profile_metrics(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract key vocabulary metrics from a profile.

    Args:
        profile: Student profile dictionary

    Returns:
        Dictionary of key metrics
    """
    return {
        'vocabulary_richness': profile.get('vocabulary_richness', 0.0),
        'unique_words': profile.get('unique_words', 0),
        'academic_word_ratio': profile.get('academic_word_ratio', 0.0),
        'avg_sentence_length': profile.get('avg_sentence_length', 0.0),
        'lexical_diversity': profile.get('lexical_diversity', 0.0),
        'readability_score': profile.get('readability_score', 0.0),
        'grade_level_equivalent': profile.get('grade_level', 0)
    }

def calculate_performance_trends(historical: List[Dict[str, Any]], current_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate performance trends from historical data.

    Args:
        historical: List of historical profiles
        current_profile: Current profile

    Returns:
        Dictionary with trend analysis
    """
    if not historical:
        return {
            'trend_available': False,
            'message': 'No historical data available for trend analysis'
        }

    try:
        # Calculate trends for key metrics
        current_richness = current_profile.get('vocabulary_richness', 0)
        current_unique = current_profile.get('unique_words', 0)

        # Get previous values
        prev_profiles = sorted(historical, key=lambda x: x.get('report_date', ''), reverse=True)[:3]  # Last 3 profiles

        if prev_profiles:
            avg_prev_richness = sum(p.get('vocabulary_richness', 0) for p in prev_profiles) / len(prev_profiles)
            avg_prev_unique = sum(p.get('unique_words', 0) for p in prev_profiles) / len(prev_profiles)

            richness_trend = current_richness - avg_prev_richness
            unique_trend = current_unique - avg_prev_unique

            return {
                'trend_available': True,
                'vocabulary_richness_change': richness_trend,
                'vocabulary_richness_trend': 'improving' if richness_trend > 0.05 else 'stable' if richness_trend > -0.05 else 'declining',
                'unique_words_change': unique_trend,
                'unique_words_trend': 'increasing' if unique_trend > 5 else 'stable' if unique_trend > -5 else 'decreasing',
                'historical_period_days': 30,
                'data_points_analyzed': len(prev_profiles)
            }
        else:
            return {
                'trend_available': False,
                'message': 'Insufficient historical data for trend analysis'
            }

    except Exception as e:
        logger.error(f"Error calculating performance trends: {e}")
        return {
            'trend_available': False,
            'message': f'Error calculating trends: {str(e)}'
        }

def format_recommendations(recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format recommendations for the report.

    Args:
        recommendations: Raw recommendation data

    Returns:
        Formatted recommendations list
    """
    formatted = []

    for rec in recommendations:
        formatted_rec = {
            'word': rec.get('word', ''),
            'definition': rec.get('definition', ''),
            'part_of_speech': rec.get('part_of_speech', 'noun'),
            'context': rec.get('context', ''),
            'grade_level': rec.get('grade_level', 0),
            'frequency_score': rec.get('frequency_score', 0.0),
            'academic_utility': rec.get('academic_utility', 'general'),
            'gap_relevance_score': rec.get('gap_relevance_score', 0.0),
            'total_score': rec.get('total_score', 0.0),
            'recommendation_rank': rec.get('recommendation_rank', 0),
            'rationale': rec.get('rationale', ''),
            'learning_objectives': rec.get('learning_objectives', []),
            'is_viewed': rec.get('is_viewed', False),
            'is_practiced': rec.get('is_practiced', False)
        }
        formatted.append(formatted_rec)

    return formatted

def extract_linguistic_features(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract linguistic features from profile for detailed analysis.

    Args:
        profile: Student profile

    Returns:
        Dictionary of linguistic features
    """
    return {
        'sentence_complexity': profile.get('sentence_complexity', {}),
        'pos_distribution': profile.get('pos_distribution', {}),
        'named_entities': profile.get('named_entities', []),
        'academic_vocabulary_usage': profile.get('academic_vocabulary_usage', {}),
        'text_coherence_score': profile.get('text_coherence_score', 0.0)
    }

def generate_student_insights(metrics: Dict[str, Any], trends: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate educational insights based on student data.

    Args:
        metrics: Current vocabulary metrics
        trends: Performance trends
        recommendations: Current recommendations

    Returns:
        Dictionary with insights and analysis
    """
    insights = {
        'strengths': [],
        'areas_for_improvement': [],
        'vocabulary_level_assessment': '',
        'learning_style_indicators': [],
        'recommended_interventions': []
    }

    try:
        # Assess vocabulary level
        richness = metrics.get('vocabulary_richness', 0)
        if richness > 0.7:
            insights['vocabulary_level_assessment'] = 'Advanced vocabulary user'
            insights['strengths'].append('Strong vocabulary diversity and richness')
        elif richness > 0.5:
            insights['vocabulary_level_assessment'] = 'Developing vocabulary user'
            insights['areas_for_improvement'].append('Continue building vocabulary diversity')
        else:
            insights['vocabulary_level_assessment'] = 'Emerging vocabulary user'
            insights['areas_for_improvement'].append('Focus on vocabulary expansion')

        # Analyze trends
        if trends.get('trend_available'):
            richness_trend = trends.get('vocabulary_richness_trend', '')
            if richness_trend == 'improving':
                insights['strengths'].append('Consistent vocabulary growth over time')
            elif richness_trend == 'declining':
                insights['areas_for_improvement'].append('Vocabulary growth has slowed - consider intervention')

        # Analyze recommendations
        if recommendations:
            academic_count = sum(1 for r in recommendations if r.get('academic_utility') == 'high')
            if academic_count > len(recommendations) * 0.6:
                insights['learning_style_indicators'].append('Strong focus on academic vocabulary needed')
                insights['recommended_interventions'].append('Incorporate more academic vocabulary practice')

        # Generate recommended interventions
        if metrics.get('unique_words', 0) < 100:
            insights['recommended_interventions'].append('Daily vocabulary practice with word lists')
        if metrics.get('academic_word_ratio', 0) < 0.1:
            insights['recommended_interventions'].append('Focus on academic and domain-specific vocabulary')

    except Exception as e:
        logger.error(f"Error generating student insights: {e}")
        insights['errors'] = [str(e)]

    return insights

def generate_learning_plan(insights: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a personalized learning plan based on insights.

    Args:
        insights: Student insights
        recommendations: Current recommendations

    Returns:
        Learning plan dictionary
    """
    return {
        'short_term_goals': [
            'Master top 10 recommended vocabulary words this week',
            'Practice using new vocabulary in writing assignments',
            'Review vocabulary definitions daily'
        ],
        'long_term_goals': [
            'Increase vocabulary richness score by 10% in 4 weeks',
            'Improve academic word usage in writing',
            'Build consistent vocabulary learning habits'
        ],
        'recommended_activities': [
            'Daily vocabulary flashcards',
            'Weekly writing assignments incorporating new words',
            'Vocabulary games and interactive exercises',
            'Reading comprehension with vocabulary focus'
        ],
        'assessment_schedule': [
            'Weekly vocabulary quizzes',
            'Bi-weekly writing assessments',
            'Monthly comprehensive vocabulary evaluation'
        ],
        'support_resources': [
            'Vocabulary building apps',
            'Online vocabulary games',
            'Word study worksheets',
            'Teacher-guided vocabulary discussions'
        ]
    }

def store_report_in_s3(report: Dict[str, Any]) -> str:
    """
    Store the generated report in S3.

    Args:
        report: Formatted report dictionary

    Returns:
        S3 key where report was stored
    """
    try:
        student_id = report['metadata']['student_id']
        timestamp = report['metadata']['generated_at'][:19].replace(':', '-')

        # Create S3 key
        s3_key = f"reports/{student_id}/{timestamp}_vocabulary_report.json"

        # Store in S3
        s3_client.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=s3_key,
            Body=json.dumps(report, indent=2),
            ContentType='application/json',
            Metadata={
                'student_id': student_id,
                'generated_at': report['metadata']['generated_at'],
                'report_version': report['metadata']['report_version']
            }
        )

        logger.info(f"Stored student report in S3: s3://{OUTPUT_BUCKET}/{s3_key}")
        return s3_key

    except Exception as e:
        logger.error(f"Error storing report in S3: {e}")
        raise

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
