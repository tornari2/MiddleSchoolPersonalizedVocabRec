#!/usr/bin/env python3
"""
Simple Schema Validation for Personalized Vocabulary Recommendation Engine

This module provides simple validation functions without heavy dependencies.
These functions ensure basic data integrity for the vocabulary recommendation system.
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import json


def validate_student_text_sample(data: Dict[str, Any]) -> Dict[str, Any]:
    """Simple validation for student text samples."""
    required_fields = ['student_id', 'grade_level', 'timestamp', 'assignment_type', 'text']

    # Check required fields
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    # Basic type checking
    if not isinstance(data['student_id'], str) or len(data['student_id']) == 0:
        raise ValueError("student_id must be a non-empty string")

    if not isinstance(data['grade_level'], int) or not (6 <= data['grade_level'] <= 8):
        raise ValueError("grade_level must be an integer between 6 and 8")

    if not isinstance(data['text'], str) or len(data['text']) == 0 or len(data['text']) > 10000:
        raise ValueError("text must be a string with 1-10000 characters")

    return data


def validate_recommendation_result(data: Dict[str, Any]) -> Dict[str, Any]:
    """Simple validation for recommendation results."""
    required_fields = ['student_id', 'recommendations', 'recommendation_metadata']

    # Check required fields
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    # Basic structure validation
    if not isinstance(data['student_id'], str):
        raise ValueError("student_id must be a string")

    if not isinstance(data['recommendations'], list):
        raise ValueError("recommendations must be a list")

    if not isinstance(data['recommendation_metadata'], dict):
        raise ValueError("recommendation_metadata must be a dict")

    return data


def validate_student_report(data: Dict[str, Any]) -> Dict[str, Any]:
    """Simple validation for student reports."""
    required_fields = ['student_id', 'report_data', 'generated_at']

    # Check required fields
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    # Basic structure validation
    if not isinstance(data['student_id'], str):
        raise ValueError("student_id must be a string")

    if not isinstance(data['report_data'], dict):
        raise ValueError("report_data must be a dict")

    if not isinstance(data['generated_at'], str):
        raise ValueError("generated_at must be a string")

    return data


class ValidationError(ValueError):
    """Custom validation error."""
    pass