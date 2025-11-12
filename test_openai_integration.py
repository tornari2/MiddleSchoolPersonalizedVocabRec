#!/usr/bin/env python3
"""
Test OpenAI Integration for Vocabulary Recommendations

This script tests the OpenAI service integration for generating
enhanced vocabulary recommendations.
"""

import os
import sys
import json
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def test_openai_service():
    """Test basic OpenAI service functionality."""
    print("🔍 Testing OpenAI Service...")

    try:
        from openai_service import OpenAIService, RecommendationConfig

        # Initialize service
        config = RecommendationConfig(
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.2")),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "500"))
        )

        service = OpenAIService(config=config)
        print("✅ OpenAI service initialized successfully")

        # Test service availability
        if service.is_available():
            print("✅ OpenAI API key is valid and service is available")
            return service
        else:
            print("❌ OpenAI service not available - check API key")
            return None

    except Exception as e:
        print(f"❌ OpenAI service initialization failed: {e}")
        print("Make sure OPENAI_API_KEY is set in your .env file")
        return None

def test_vocabulary_recommendations(service):
    """Test vocabulary recommendation generation."""
    print("\n🧠 Testing Vocabulary Recommendations...")

    # Sample student data for testing
    student_profile = {
        "student_id": "TEST001",
        "grade_level": 7,
        "vocabulary_proficiency": 0.65,
        "common_topics": ["science", "literature", "social_studies"]
    }

    writing_samples = [
        {
            "assignment_type": "science_report",
            "vocabulary_focus": ["analyze", "hypothesis", "experiment"],
            "text": "The scientist conducted an experiment to test the hypothesis about plant growth."
        },
        {
            "assignment_type": "literature_analysis",
            "vocabulary_focus": ["theme", "character", "narrative"],
            "text": "The character's development throughout the narrative was quite interesting."
        }
    ]

    current_recommendations = [
        {"word": "analyze", "definition": "to examine carefully"},
        {"word": "hypothesis", "definition": "a proposed explanation"},
        {"word": "theme", "definition": "main idea or topic"}
    ]

    try:
        # Generate enhanced recommendations
        recommendations = service.generate_vocabulary_recommendations(
            student_profile=student_profile,
            writing_samples=writing_samples,
            current_recommendations=current_recommendations,
            grade_level=7
        )

        if recommendations:
            print(f"✅ Generated {len(recommendations)} vocabulary recommendations:")

            for i, rec in enumerate(recommendations, 1):
                print(f"\n{i}. **{rec['word']}**")
                print(f"   Definition: {rec['definition']}")
                print(f"   Context: {rec['context']}")
                print(f"   Rationale: {rec['rationale']}")
                print(f"   Difficulty: {rec['difficulty_level']}")
                print(f"   Subject: {rec['subject_area']}")

            return True
        else:
            print("❌ No recommendations generated")
            return False

    except Exception as e:
        print(f"❌ Recommendation generation failed: {e}")
        return False

def create_sample_recommendation_data():
    """Create sample data file for testing."""
    print("\n📝 Creating sample recommendation test data...")

    sample_data = {
        "student_profile": {
            "student_id": "TEST001",
            "grade_level": 7,
            "vocabulary_proficiency": 0.65,
            "writing_patterns": ["analytical", "descriptive", "narrative"]
        },
        "writing_samples": [
            {
                "timestamp": "2024-01-15T10:00:00Z",
                "assignment_type": "science_report",
                "vocabulary_focus": ["analyze", "hypothesis", "experiment"],
                "text_quality_score": 0.75
            },
            {
                "timestamp": "2024-01-20T10:00:00Z",
                "assignment_type": "literature_analysis",
                "vocabulary_focus": ["theme", "character", "narrative"],
                "text_quality_score": 0.82
            }
        ],
        "current_recommendations": [
            {
                "word": "analyze",
                "definition": "to examine carefully and in detail",
                "frequency_score": 0.85,
                "grade_appropriateness": 0.9
            }
        ]
    }

    with open("test_recommendation_data.json", "w") as f:
        json.dump(sample_data, f, indent=2)

    print("✅ Sample data saved to test_recommendation_data.json")

def main():
    """Main test function."""
    print("🧪 Testing OpenAI Integration for Vocabulary Recommendations")
    print("=" * 60)

    # Check environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key in the .env file")
        print("Example: OPENAI_API_KEY=sk-your-key-here")
        return 1

    if not api_key.startswith("sk-"):
        print("⚠️  OPENAI_API_KEY doesn't start with 'sk-' - please verify it's correct")
        return 1

    print("✅ OpenAI API key found in environment")

    # Test OpenAI service
    service = test_openai_service()
    if not service:
        return 1

    # Test recommendation generation
    if not test_vocabulary_recommendations(service):
        print("\n❌ Recommendation generation test failed")
        print("This might be due to API rate limits or content filtering")
        print("Try again in a few minutes or check your OpenAI account status")
        return 1

    # Create sample data
    create_sample_recommendation_data()

    print("\n" + "=" * 60)
    print("🎉 OpenAI Integration Test Complete!")
    print("✅ API key is valid")
    print("✅ Service is available")
    print("✅ Recommendations can be generated")
    print("✅ Sample test data created")
    print("\n🚀 Ready to enhance vocabulary recommendations with AI!")
    print("\nNext steps:")
    print("- Integrate into recommendation_engine.py")
    print("- Test with real student data")
    print("- Deploy to AWS Lambda with Secrets Manager")

    return 0

if __name__ == "__main__":
    sys.exit(main())
