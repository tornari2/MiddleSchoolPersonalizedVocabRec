#!/usr/bin/env python3
"""
OpenAI Service for Enhanced Vocabulary Recommendations

This module provides OpenAI integration for generating intelligent
vocabulary recommendations based on student writing analysis.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

try:
    from openai import OpenAI
    from openai import APIError, RateLimitError, AuthenticationError
except ImportError:
    print("OpenAI library not installed. Install with: pip install openai")
    raise

logger = logging.getLogger(__name__)

@dataclass
class RecommendationConfig:
    """Configuration for vocabulary recommendations."""
    model: str = "gpt-4o-mini"
    temperature: float = 0.2
    max_tokens: int = 500
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

class OpenAIService:
    """Service for generating enhanced vocabulary recommendations using OpenAI."""

    def __init__(self, api_key: Optional[str] = None, config: Optional[RecommendationConfig] = None):
        """
        Initialize the OpenAI service.

        Args:
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY environment variable.
            config: Recommendation configuration.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not provided. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter. Get your key from https://platform.openai.com/api-keys"
            )

        self.client = OpenAI(api_key=self.api_key)
        self.config = config or self._load_config_from_env()

        logger.info(f"Initialized OpenAI service for recommendations with model: {self.config.model}")

    def _load_config_from_env(self) -> RecommendationConfig:
        """Load recommendation configuration from environment variables."""
        return RecommendationConfig(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.2")),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "500")),
            top_p=float(os.getenv("OPENAI_TOP_P", "0.9")),
            frequency_penalty=float(os.getenv("OPENAI_FREQUENCY_PENALTY", "0.0")),
            presence_penalty=float(os.getenv("OPENAI_PRESENCE_PENALTY", "0.0"))
        )

    def generate_vocabulary_recommendations(
        self,
        student_profile: Dict[str, Any],
        writing_samples: List[Dict[str, Any]],
        current_recommendations: List[Dict[str, Any]],
        grade_level: int
    ) -> List[Dict[str, Any]]:
        """
        Generate enhanced vocabulary recommendations using OpenAI.

        Args:
            student_profile: Student vocabulary profile
            writing_samples: Recent writing samples
            current_recommendations: Current algorithm-based recommendations
            grade_level: Student grade level

        Returns:
            Enhanced list of vocabulary recommendations
        """
        try:
            # Prepare context for OpenAI
            context = self._prepare_recommendation_context(
                student_profile, writing_samples, current_recommendations, grade_level
            )

            # Generate recommendations using OpenAI
            prompt = self._build_recommendation_prompt(context)

            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                top_p=self.config.top_p,
                frequency_penalty=self.config.frequency_penalty,
                presence_penalty=self.config.presence_penalty
            )

            content = response.choices[0].message.content.strip()

            # Parse and validate recommendations
            recommendations = self._parse_recommendations(content)

            logger.info(f"Generated {len(recommendations)} AI-enhanced recommendations")
            return recommendations

        except AuthenticationError as e:
            logger.error(f"OpenAI authentication error: {e}")
            raise ValueError("Invalid OpenAI API key. Check your OPENAI_API_KEY environment variable.")
        except RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise RuntimeError("OpenAI API rate limit exceeded. Please try again later.")
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise RuntimeError(f"OpenAI API error: {e}")
        except Exception as e:
            logger.error(f"Error generating AI recommendations: {e}")
            # Return original recommendations as fallback
            return current_recommendations

    def _prepare_recommendation_context(
        self,
        student_profile: Dict[str, Any],
        writing_samples: List[Dict[str, Any]],
        current_recommendations: List[Dict[str, Any]],
        grade_level: int
    ) -> Dict[str, Any]:
        """Prepare context information for recommendation generation."""
        # Extract key writing patterns
        recent_topics = []
        vocabulary_usage = {}
        writing_quality_metrics = []

        for sample in writing_samples[-10:]:  # Last 10 samples
            if 'assignment_type' in sample:
                recent_topics.append(sample.get('assignment_type', 'unknown'))

            # Track vocabulary usage patterns
            vocab_focus = sample.get('vocabulary_focus', [])
            for word in vocab_focus:
                vocabulary_usage[word] = vocabulary_usage.get(word, 0) + 1

        # Get top used words
        top_words = sorted(vocabulary_usage.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            'grade_level': grade_level,
            'student_profile': student_profile,
            'recent_topics': recent_topics[:5],  # Last 5 topics
            'vocabulary_usage': top_words,
            'current_recommendations': current_recommendations[:5],  # Top 5 current recs
            'writing_sample_count': len(writing_samples)
        }

    def _get_system_prompt(self) -> str:
        """Get the system prompt for vocabulary recommendation generation."""
        return """You are an expert educational AI specializing in vocabulary development for middle school students.

Your task is to enhance vocabulary recommendations by analyzing student writing patterns and suggesting words that will:
1. Build upon their current vocabulary level
2. Address gaps in their academic writing
3. Match their grade-appropriate complexity
4. Support their specific writing needs and topics

Focus on academic and domain-specific vocabulary that appears naturally in student writing across subjects like science, social studies, literature, and general academic contexts.

Provide recommendations in JSON format with word, definition, context, and rationale."""

    def _build_recommendation_prompt(self, context: Dict[str, Any]) -> str:
        """Build the user prompt for recommendation generation."""
        grade_level = context['grade_level']
        recent_topics = ', '.join(context['recent_topics'])
        vocab_usage = ', '.join([f"{word} ({count}x)" for word, count in context['vocabulary_usage']])

        current_recs = []
        for rec in context['current_recommendations']:
            if isinstance(rec, dict) and 'word' in rec:
                current_recs.append(rec['word'])
        current_rec_text = ', '.join(current_recs) if current_recs else 'none yet'

        prompt = f"""Analyze this middle school student's vocabulary development and suggest 5 enhanced vocabulary recommendations.

STUDENT PROFILE:
- Grade Level: {grade_level}
- Writing Samples Analyzed: {context['writing_sample_count']}
- Recent Writing Topics: {recent_topics}
- Current Vocabulary Usage: {vocab_usage}
- Existing Recommendations: {current_rec_text}

REQUIREMENTS:
1. Suggest 5 new academic vocabulary words appropriate for grade {grade_level}
2. Each word should build upon their current vocabulary level
3. Consider their writing topics and common academic contexts
4. Focus on words that would naturally appear in their writing
5. Provide clear definitions and usage contexts

Return your response as a JSON array of objects with this exact format:
[
  {{
    "word": "vocabulary_word",
    "definition": "clear, student-friendly definition",
    "context": "example sentence showing usage",
    "rationale": "why this word is recommended for this student",
    "difficulty_level": "beginner|intermediate|advanced",
    "subject_area": "academic subject or general academic"
  }}
]

Ensure the JSON is valid and contains exactly 5 recommendations."""

        return prompt

    def _parse_recommendations(self, content: str) -> List[Dict[str, Any]]:
        """Parse the OpenAI response into structured recommendations."""
        try:
            import json
            import re

            # Clean the content - remove markdown code block formatting
            cleaned_content = content.strip()

            # Remove markdown code blocks if present
            if cleaned_content.startswith('```json'):
                cleaned_content = cleaned_content[7:]  # Remove ```json
            if cleaned_content.startswith('```'):
                cleaned_content = cleaned_content[3:]  # Remove ```
            if cleaned_content.endswith('```'):
                cleaned_content = cleaned_content[:-3]  # Remove trailing ```

            # Clean up any remaining whitespace
            cleaned_content = cleaned_content.strip()

            # If content is empty after cleaning, return empty list
            if not cleaned_content:
                logger.error("Content is empty after cleaning markdown formatting")
                return []

            recommendations = json.loads(cleaned_content)

            if not isinstance(recommendations, list):
                raise ValueError("Response is not a JSON array")

            # Validate and clean each recommendation
            validated_recs = []
            for rec in recommendations:
                if isinstance(rec, dict) and 'word' in rec:
                    # Ensure required fields
                    validated_rec = {
                        'word': rec.get('word', '').strip(),
                        'definition': rec.get('definition', '').strip(),
                        'context': rec.get('context', '').strip(),
                        'rationale': rec.get('rationale', '').strip(),
                        'difficulty_level': rec.get('difficulty_level', 'intermediate'),
                        'subject_area': rec.get('subject_area', 'general academic'),
                        'source': 'openai_enhanced'
                    }
                    validated_recs.append(validated_rec)

            logger.info(f"Successfully parsed {len(validated_recs)} recommendations from OpenAI response")
            return validated_recs[:5]  # Return top 5

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            logger.error(f"Cleaned response content: {cleaned_content[:500] if 'cleaned_content' in locals() else content[:500]}...")
            return []
        except Exception as e:
            logger.error(f"Error parsing recommendations: {e}")
            logger.error(f"Original content: {content[:500]}...")
            return []

    def is_available(self) -> bool:
        """Check if the OpenAI service is available and configured."""
        try:
            # Simple test request to check API key validity
            self.client.models.list()
            return True
        except AuthenticationError:
            return False
        except Exception as e:
            logger.warning(f"OpenAI service availability check failed: {e}")
            return False