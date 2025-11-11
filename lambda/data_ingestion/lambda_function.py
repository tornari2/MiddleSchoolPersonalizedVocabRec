import json
import boto3
import os
import logging
from typing import Dict, List, Any
from datetime import datetime

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3_client = boto3.client('s3')
dynamodb_client = boto3.client('dynamodb')

# Environment variables
INPUT_BUCKET = os.environ['INPUT_BUCKET']
OUTPUT_BUCKET = os.environ['OUTPUT_BUCKET']
PROFILES_TABLE = os.environ['PROFILES_TABLE']
RECOMMENDATIONS_TABLE = os.environ['RECOMMENDATIONS_TABLE']

def lambda_handler(event, context):
    """
    Lambda function to process student text data from S3.

    Triggered when a new JSONL file is uploaded to the input bucket.
    Processes each student's data and initiates vocabulary analysis.
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        # Extract S3 event information
        for record in event['Records']:
            bucket_name = record['s3']['bucket']['name']
            object_key = record['s3']['object']['key']

            logger.info(f"Processing file: s3://{bucket_name}/{object_key}")

            # Process the uploaded file
            process_student_data_file(bucket_name, object_key)

        return {
            'statusCode': 200,
            'body': json.dumps('Data processing completed successfully')
        }

    except Exception as e:
        logger.error(f"Error processing data: {str(e)}")
        raise e

def process_student_data_file(bucket_name: str, object_key: str):
    """
    Process a JSONL file containing student text data.

    Args:
        bucket_name: S3 bucket name
        object_key: S3 object key (file path)
    """
    try:
        # Read the JSONL file from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        content = response['Body'].read().decode('utf-8')

        # Parse JSONL content
        samples = []
        for line in content.strip().split('\n'):
            if line.strip():
                samples.append(json.loads(line))

        logger.info(f"Loaded {len(samples)} samples from {object_key}")

        # Group samples by student
        student_data = {}
        for sample in samples:
            student_id = sample['student_id']
            if student_id not in student_data:
                student_data[student_id] = []
            student_data[student_id].append(sample)

        logger.info(f"Processing data for {len(student_data)} students")

        # Process each student's data
        for student_id, student_samples in student_data.items():
            process_student_data(student_id, student_samples)

        logger.info(f"Successfully processed data for {len(student_data)} students")

    except Exception as e:
        logger.error(f"Error processing file {object_key}: {str(e)}")
        raise e

def process_student_data(student_id: str, samples: List[Dict[str, Any]]):
    """
    Process data for a single student.

    Args:
        student_id: Unique student identifier
        samples: List of text samples for the student
    """
    try:
        logger.info(f"Processing data for student {student_id}")

        # Extract student metadata from first sample
        first_sample = samples[0]
        grade_level = first_sample.get('grade_level', 7)

        # Analyze vocabulary usage
        vocab_analysis = analyze_student_vocabulary(samples)

        # Store student profile in DynamoDB
        store_student_profile(student_id, grade_level, vocab_analysis, samples)

        # Generate vocabulary recommendations
        recommendations = generate_vocabulary_recommendations(student_id, grade_level, vocab_analysis)

        # Store recommendations in DynamoDB
        store_vocabulary_recommendations(student_id, recommendations)

        # Log processing results
        logger.info(f"Completed processing for student {student_id}: {len(samples)} samples, {len(recommendations)} recommendations")

    except Exception as e:
        logger.error(f"Error processing student {student_id}: {str(e)}")
        raise e

def analyze_student_vocabulary(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze vocabulary usage in student samples.

    Args:
        samples: List of student text samples

    Returns:
        Dictionary with vocabulary analysis results
    """
    # Simple vocabulary analysis (placeholder for more sophisticated analysis)
    all_words = []
    word_frequencies = {}

    for sample in samples:
        text = sample.get('text', '').lower()
        # Simple word extraction (would be more sophisticated in production)
        words = text.replace('.', '').replace(',', '').replace('!', '').replace('?', '').split()

        for word in words:
            if len(word) > 2:  # Skip very short words
                all_words.append(word)
                word_frequencies[word] = word_frequencies.get(word, 0) + 1

    # Sort by frequency
    sorted_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)

    return {
        'total_words': len(all_words),
        'unique_words': len(word_frequencies),
        'most_frequent_words': sorted_words[:20],  # Top 20 words
        'vocabulary_richness': len(word_frequencies) / max(len(all_words), 1),  # Type-token ratio
        'samples_analyzed': len(samples)
    }

def generate_vocabulary_recommendations(student_id: str, grade_level: int, vocab_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate vocabulary recommendations for a student.

    Args:
        student_id: Student identifier
        grade_level: Student's grade level
        vocab_analysis: Results from vocabulary analysis

    Returns:
        List of vocabulary recommendations
    """
    # Placeholder for vocabulary recommendation logic
    # In a real implementation, this would use the reference data and ML models

    recommendations = [
        {
            'word': 'analyze',
            'definition': 'To examine something in detail to understand its nature',
            'context': 'Scientists analyze data to find patterns.',
            'grade_level': grade_level,
            'frequency_score': 0.85,
            'academic_utility': 'high'
        },
        {
            'word': 'evaluate',
            'definition': 'To judge or calculate the quality, importance, or value of something',
            'context': 'Teachers evaluate student work regularly.',
            'grade_level': grade_level,
            'frequency_score': 0.78,
            'academic_utility': 'high'
        },
        {
            'word': 'interpret',
            'definition': 'To explain the meaning of something',
            'context': 'Historians interpret events from the past.',
            'grade_level': grade_level,
            'frequency_score': 0.72,
            'academic_utility': 'medium'
        }
    ]

    return recommendations

def store_student_profile(student_id: str, grade_level: int, vocab_analysis: Dict[str, Any], samples: List[Dict[str, Any]]):
    """
    Store student vocabulary profile in DynamoDB.

    Args:
        student_id: Student identifier
        grade_level: Student's grade level
        vocab_analysis: Vocabulary analysis results
        samples: Original text samples
    """
    try:
        item = {
            'student_id': {'S': student_id},
            'report_date': {'S': datetime.now().isoformat()},
            'grade_level': {'N': str(grade_level)},
            'vocabulary_analysis': {'S': json.dumps(vocab_analysis)},
            'sample_count': {'N': str(len(samples))},
            'total_words': {'N': str(vocab_analysis['total_words'])},
            'unique_words': {'N': str(vocab_analysis['unique_words'])},
            'vocabulary_richness': {'N': str(vocab_analysis['vocabulary_richness'])}
        }

        dynamodb_client.put_item(
            TableName=PROFILES_TABLE,
            Item=item
        )

        logger.info(f"Stored profile for student {student_id}")

    except Exception as e:
        logger.error(f"Error storing profile for student {student_id}: {str(e)}")
        raise e

def store_vocabulary_recommendations(student_id: str, recommendations: List[Dict[str, Any]]):
    """
    Store vocabulary recommendations in DynamoDB.

    Args:
        student_id: Student identifier
        recommendations: List of vocabulary recommendations
    """
    try:
        current_time = datetime.now().isoformat()

        for i, rec in enumerate(recommendations):
            item = {
                'student_id': {'S': student_id},
                'recommendation_date': {'S': current_time},
                'word': {'S': rec['word']},
                'definition': {'S': rec['definition']},
                'context': {'S': rec['context']},
                'grade_level': {'N': str(rec['grade_level'])},
                'frequency_score': {'N': str(rec['frequency_score'])},
                'academic_utility': {'S': rec['academic_utility']},
                'recommendation_id': {'S': f"{student_id}_{i}"}
            }

            dynamodb_client.put_item(
                TableName=RECOMMENDATIONS_TABLE,
                Item=item
            )

        logger.info(f"Stored {len(recommendations)} recommendations for student {student_id}")

    except Exception as e:
        logger.error(f"Error storing recommendations for student {student_id}: {str(e)}")
        raise e
