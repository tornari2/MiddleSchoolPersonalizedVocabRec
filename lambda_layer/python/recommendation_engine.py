#!/usr/bin/env python3
"""
Recommendation Engine for Personalized Vocabulary Recommendations

This module implements a hybrid content-knowledge based recommendation algorithm
that generates personalized vocabulary recommendations for middle school students.

Key Features:
- Hybrid algorithm combining content-based and knowledge-based approaches
- Multi-factor scoring system with weighted components
- Grade-appropriate recommendations (6-8)
- Academic utility and frequency-based selection
- Integration with reference data and student profiles
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import math
import random

from reference_data_loader import ReferenceDataLoader

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """
    Generates personalized vocabulary recommendations using hybrid algorithm.

    Combines content-based analysis of student gaps with knowledge-based
    educational standards to recommend the most appropriate vocabulary words.
    """

    def __init__(self, reference_data_loader: Optional[ReferenceDataLoader] = None):
        """
        Initialize the recommendation engine.

        Args:
            reference_data_loader: Pre-loaded reference data, or None to load automatically
        """
        self.reference_loader = reference_data_loader or ReferenceDataLoader()

        # Algorithm configuration
        self.algorithm_config = {
            'version': '1.0',
            'scoring_weights': {
                'gap_relevance': 0.40,      # How well word addresses student's gaps
                'grade_appropriateness': 0.25,  # Optimal difficulty for grade level
                'academic_utility': 0.20,   # Educational value and frequency
                'contextual_fit': 0.10,     # Relevance to student's subjects
                'pronunciation_ease': 0.05  # Phonetic accessibility
            },
            'target_recommendations': 10,
            'grade_ranges': {
                6: {'min_freq': 0.1, 'max_freq': 0.8, 'academic_boost': 1.0},
                7: {'min_freq': 0.15, 'max_freq': 0.85, 'academic_boost': 1.1},
                8: {'min_freq': 0.2, 'max_freq': 0.9, 'academic_boost': 1.2}
            }
        }

        # Academic word list (subset for efficiency)
        self.academic_words = {
            'analysis', 'approach', 'benefit', 'challenge', 'communicate', 'compare',
            'component', 'concept', 'context', 'create', 'culture', 'design', 'develop',
            'environment', 'establish', 'evaluate', 'evidence', 'factor', 'feature',
            'function', 'identify', 'impact', 'implement', 'individual', 'influence',
            'interpret', 'involve', 'issue', 'maintain', 'method', 'occur', 'policy',
            'principle', 'process', 'provide', 'require', 'research', 'resource',
            'respond', 'result', 'section', 'significant', 'similar', 'solution',
            'strategy', 'structure', 'technology', 'theory', 'variable', 'version'
        }

        # Grade-level complexity mappings
        self.complexity_map = {
            'basic': {'min_freq': 0.5, 'academic_ratio': 0.1},
            'intermediate': {'min_freq': 0.3, 'academic_ratio': 0.2},
            'advanced': {'min_freq': 0.1, 'academic_ratio': 0.4}
        }

        logger.info("Recommendation engine initialized")

    def generate_recommendations(self, student_id: str, student_profile: Dict[str, Any],
                               linguistic_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate personalized vocabulary recommendations for a student.

        Args:
            student_id: Unique student identifier
            student_profile: Student profile data
            linguistic_analysis: Linguistic analysis results

        Returns:
            Dictionary containing recommendations and metadata
        """
        try:
            grade_level = student_profile.get('grade_level', 7)
            logger.info(f"Generating recommendations for student {student_id} (Grade {grade_level})")

            # Step 1: Identify vocabulary gaps from linguistic analysis
            vocabulary_gaps = self._identify_vocabulary_gaps(linguistic_analysis, grade_level)

            # Step 2: Select candidate words from reference data
            candidate_words = self._select_candidate_words(grade_level, vocabulary_gaps)

            # Step 3: Score candidates using multi-factor algorithm
            scored_candidates = self._score_candidates(
                candidate_words, vocabulary_gaps, student_profile, linguistic_analysis
            )

            # Step 4: Select top 10 recommendations
            recommendations = self._select_top_recommendations(scored_candidates, grade_level)

            # Step 5: Format recommendations with metadata
            formatted_recommendations = self._format_recommendations(
                student_id, recommendations, grade_level, vocabulary_gaps
            )

            logger.info(f"Generated {len(formatted_recommendations['recommendations'])} recommendations for student {student_id}")

            return formatted_recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations for student {student_id}: {e}")
            return {
                'student_id': student_id,
                'error': str(e),
                'recommendations': [],
                'recommendation_metadata': {
                    'algorithm_version': self.algorithm_config['version'],
                    'processing_timestamp': datetime.now().isoformat(),
                    'error_occurred': True
                }
            }

    def _identify_vocabulary_gaps(self, linguistic_analysis: Dict[str, Any], grade_level: int) -> Dict[str, Any]:
        """
        Identify vocabulary gaps from linguistic analysis.

        Args:
            linguistic_analysis: Results from vocabulary profiler
            grade_level: Student's grade level

        Returns:
            Dictionary describing vocabulary gaps and needs
        """
        # Extract key metrics from linguistic analysis
        vocab_richness = linguistic_analysis.get('vocabulary_richness', 0.5)
        academic_ratio = linguistic_analysis.get('academic_word_ratio', 0.1)
        avg_sentence_length = linguistic_analysis.get('avg_sentence_length', 8)
        unique_words = linguistic_analysis.get('unique_words', 50)

        # Determine gap areas based on grade-level expectations
        grade_expectations = {
            6: {'target_vocab_richness': 0.4, 'target_academic_ratio': 0.08, 'target_sentence_length': 10},
            7: {'target_vocab_richness': 0.5, 'target_academic_ratio': 0.12, 'target_sentence_length': 12},
            8: {'target_vocab_richness': 0.6, 'target_academic_ratio': 0.15, 'target_sentence_length': 15}
        }

        expectations = grade_expectations.get(grade_level, grade_expectations[7])

        # Calculate gap scores (higher = bigger gap)
        gaps = {
            'vocabulary_diversity_gap': max(0, expectations['target_vocab_richness'] - vocab_richness),
            'academic_vocabulary_gap': max(0, expectations['target_academic_ratio'] - academic_ratio),
            'sentence_complexity_gap': max(0, expectations['target_sentence_length'] - avg_sentence_length) / 10,
            'lexical_depth_gap': max(0, 100 - unique_words) / 100
        }

        # Determine primary focus areas
        primary_gaps = sorted(gaps.items(), key=lambda x: x[1], reverse=True)

        return {
            'gap_scores': gaps,
            'primary_gap_areas': [gap[0] for gap in primary_gaps[:2]],  # Top 2 gap areas
            'overall_gap_severity': sum(gaps.values()) / len(gaps),
            'grade_expectations': expectations,
            'current_metrics': {
                'vocabulary_richness': vocab_richness,
                'academic_ratio': academic_ratio,
                'sentence_length': avg_sentence_length,
                'unique_words': unique_words
            }
        }

    def _select_candidate_words(self, grade_level: int, vocabulary_gaps: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Select candidate words from reference data based on grade level and gaps.

        Args:
            grade_level: Student's grade level
            vocabulary_gaps: Identified vocabulary gaps

        Returns:
            List of candidate word dictionaries
        """
        candidates = []

        # Get grade-appropriate words from reference data
        grade_range = range(max(6, grade_level - 1), min(8, grade_level + 1) + 1)  # ±1 grade range, stay within 6-8

        for grade in grade_range:
            grade_data = self.reference_loader.get_all_grade_words(grade)
            if grade_data:
                # Convert the dictionary format to list of word dictionaries
                for level, words in grade_data.items():
                    for word in words:
                        # Get additional word data
                        freq_data = self.reference_loader.get_word_frequency(word)
                        def_data = self.reference_loader.get_word_definition(word)

                        candidate = {
                            'word': word,
                            'grade': grade,
                            'level': level,
                            'frequency_score': freq_data.get('frequency_score', 0.5) if freq_data else 0.5,
                            'definition': def_data.get('definition', '') if def_data else '',
                            'part_of_speech': def_data.get('part_of_speech', 'noun') if def_data else 'noun',
                            'context': def_data.get('example_sentence', '') if def_data else ''
                        }
                        candidates.append(candidate)

        # Filter and prioritize based on gap areas
        primary_gaps = vocabulary_gaps.get('primary_gap_areas', [])

        filtered_candidates = []
        for word_data in candidates:
            word = word_data.get('word', '').lower()
            frequency_score = word_data.get('frequency_score', 0.5)

            # Boost academic words if academic gap is primary
            if 'academic_vocabulary_gap' in primary_gaps and word in self.academic_words:
                frequency_score *= 1.2

            # Boost less common words if vocabulary diversity gap exists
            if 'vocabulary_diversity_gap' in primary_gaps and frequency_score < 0.4:
                frequency_score *= 1.1

            word_data['adjusted_frequency_score'] = min(1.0, frequency_score)
            filtered_candidates.append(word_data)

        # Remove duplicates and sort by adjusted frequency
        seen_words = set()
        unique_candidates = []
        for candidate in filtered_candidates:
            word = candidate['word'].lower()
            if word not in seen_words:
                seen_words.add(word)
                unique_candidates.append(candidate)

        # Sort by adjusted frequency score (descending)
        unique_candidates.sort(key=lambda x: x.get('adjusted_frequency_score', 0), reverse=True)

        # Return top candidates (more than needed for scoring variety)
        return unique_candidates[:50]  # Return more than 10 for better selection

    def _score_candidates(self, candidates: List[Dict[str, Any]], vocabulary_gaps: Dict[str, Any],
                         student_profile: Dict[str, Any], linguistic_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Score candidate words using multi-factor algorithm.

        Args:
            candidates: List of candidate word dictionaries
            vocabulary_gaps: Identified vocabulary gaps
            student_profile: Student profile data
            linguistic_analysis: Linguistic analysis results

        Returns:
            List of candidates with scoring information
        """
        grade_level = student_profile.get('grade_level', 7)
        gap_scores = vocabulary_gaps.get('gap_scores', {})
        weights = self.algorithm_config['scoring_weights']

        scored_candidates = []

        for candidate in candidates:
            word = candidate.get('word', '').lower()
            base_freq_score = candidate.get('adjusted_frequency_score', 0.5)

            # Factor 1: Gap Relevance Score (40%)
            gap_relevance = self._calculate_gap_relevance(word, gap_scores, candidate)
            gap_relevance_score = min(1.0, gap_relevance)

            # Factor 2: Grade Appropriateness Score (25%)
            grade_appropriateness = self._calculate_grade_appropriateness(word, grade_level, base_freq_score)
            grade_appropriateness_score = min(1.0, grade_appropriateness)

            # Factor 3: Academic Utility Score (20%)
            academic_utility = self._calculate_academic_utility(word, candidate)
            academic_utility_score = min(1.0, academic_utility)

            # Factor 4: Contextual Fit Score (10%)
            contextual_fit = self._calculate_contextual_fit(word, linguistic_analysis)
            contextual_fit_score = min(1.0, contextual_fit)

            # Factor 5: Pronunciation Ease Score (5%)
            pronunciation_ease = self._calculate_pronunciation_ease(word, candidate)
            pronunciation_ease_score = min(1.0, pronunciation_ease)

            # Calculate weighted total score
            total_score = (
                gap_relevance_score * weights['gap_relevance'] +
                grade_appropriateness_score * weights['grade_appropriateness'] +
                academic_utility_score * weights['academic_utility'] +
                contextual_fit_score * weights['contextual_fit'] +
                pronunciation_ease_score * weights['pronunciation_ease']
            )

            scored_candidate = {
                **candidate,
                'scoring_factors': {
                    'gap_relevance': round(gap_relevance_score, 3),
                    'grade_appropriateness': round(grade_appropriateness_score, 3),
                    'academic_utility': round(academic_utility_score, 3),
                    'contextual_fit': round(contextual_fit_score, 3),
                    'pronunciation_ease': round(pronunciation_ease_score, 3)
                },
                'total_score': round(total_score, 3),
                'gap_relevance_score': round(gap_relevance_score, 3),  # For backward compatibility
                'rationale': self._generate_rationale(word, gap_relevance_score, grade_level, academic_utility_score)
            }

            scored_candidates.append(scored_candidate)

        # Sort by total score (descending)
        scored_candidates.sort(key=lambda x: x['total_score'], reverse=True)

        return scored_candidates

    def _calculate_gap_relevance(self, word: str, gap_scores: Dict[str, float],
                               candidate: Dict[str, Any]) -> float:
        """Calculate how well word addresses identified gaps."""
        relevance_score = 0.5  # Base score

        # Academic vocabulary gap
        if gap_scores.get('academic_vocabulary_gap', 0) > 0.1:
            if word in self.academic_words:
                relevance_score += 0.3

        # Vocabulary diversity gap
        if gap_scores.get('vocabulary_diversity_gap', 0) > 0.1:
            freq_score = candidate.get('adjusted_frequency_score', 0.5)
            if freq_score < 0.4:  # Less common words
                relevance_score += 0.2

        # Sentence complexity gap
        if gap_scores.get('sentence_complexity_gap', 0) > 0.2:
            # Words that could help build more complex sentences
            definition = candidate.get('definition', '')
            if any(term in definition.lower() for term in ['analyze', 'explain', 'describe', 'compare']):
                relevance_score += 0.15

        return min(1.0, relevance_score)

    def _calculate_grade_appropriateness(self, word: str, grade_level: int, freq_score: float) -> float:
        """Calculate how appropriate word is for student's grade level."""
        grade_config = self.algorithm_config['grade_ranges'].get(grade_level, self.algorithm_config['grade_ranges'][7])

        # Check if frequency score is in optimal range for grade
        min_freq = grade_config['min_freq']
        max_freq = grade_config['max_freq']

        if min_freq <= freq_score <= max_freq:
            return 0.9  # Optimal range
        elif freq_score < min_freq:
            # Too difficult - reduce score based on how far below
            return max(0.3, 0.9 - (min_freq - freq_score) * 2)
        else:
            # Too easy - reduce score based on how far above
            return max(0.4, 0.9 - (freq_score - max_freq) * 1.5)

    def _calculate_academic_utility(self, word: str, candidate: Dict[str, Any]) -> float:
        """Calculate academic utility based on word characteristics."""
        utility_score = candidate.get('adjusted_frequency_score', 0.5)

        # Boost for academic words
        if word in self.academic_words:
            utility_score *= 1.3

        # Boost for words with academic definitions
        definition = candidate.get('definition', '').lower()
        academic_indicators = ['analyze', 'evaluate', 'explain', 'describe', 'compare',
                             'contrast', 'identify', 'demonstrate', 'illustrate']

        if any(indicator in definition for indicator in academic_indicators):
            utility_score *= 1.1

        return min(1.0, utility_score)

    def _calculate_contextual_fit(self, word: str, linguistic_analysis: Dict[str, Any]) -> float:
        """Calculate how well word fits student's linguistic context."""
        # This is a simplified version - in production, this would analyze
        # student's writing samples for thematic/contextual patterns
        return 0.7  # Neutral score for MVP

    def _calculate_pronunciation_ease(self, word: str, candidate: Dict[str, Any]) -> float:
        """Calculate pronunciation ease based on phonetic features."""
        # Simplified scoring based on word length and common patterns
        word_length = len(word)

        if word_length <= 4:
            return 0.9  # Short words are easier
        elif word_length <= 7:
            return 0.7  # Medium words
        else:
            return 0.5  # Long words are harder

    def _generate_rationale(self, word: str, gap_score: float, grade_level: int,
                          academic_score: float) -> str:
        """Generate human-readable rationale for recommendation."""
        rationales = []

        if gap_score > 0.7:
            rationales.append("addresses key vocabulary gap")
        elif gap_score > 0.5:
            rationales.append("helps fill vocabulary gap")

        if academic_score > 0.8:
            rationales.append("high academic utility")
        elif academic_score > 0.6:
            rationales.append("useful in academic contexts")

        grade_descriptors = {
            6: "appropriate for 6th grade",
            7: "appropriate for 7th grade",
            8: "appropriate for 8th grade"
        }

        rationales.append(grade_descriptors.get(grade_level, "grade-appropriate"))

        return f"Word {word}: {' and '.join(rationales)}"

    def _select_top_recommendations(self, scored_candidates: List[Dict[str, Any]],
                                  grade_level: int) -> List[Dict[str, Any]]:
        """Select top 10 recommendations with diversity considerations."""
        if len(scored_candidates) <= 10:
            return scored_candidates

        # Select top candidates with diversity
        selected = []
        academic_count = 0
        content_count = 0

        for candidate in scored_candidates:
            if len(selected) >= 10:
                break

            word = candidate.get('word', '').lower()
            is_academic = word in self.academic_words

            # Ensure balance between academic and content words
            if is_academic and academic_count >= 6:  # Max 6 academic words
                continue
            elif not is_academic and content_count >= 6:  # Max 6 content words
                continue

            selected.append(candidate)
            if is_academic:
                academic_count += 1
            else:
                content_count += 1

        # Add rank information
        for i, candidate in enumerate(selected, 1):
            candidate['recommendation_rank'] = i

        return selected

    def _format_recommendations(self, student_id: str, recommendations: List[Dict[str, Any]],
                              grade_level: int, vocabulary_gaps: Dict[str, Any]) -> Dict[str, Any]:
        """Format recommendations with complete metadata."""
        formatted_recommendations = []

        for rec in recommendations:
            formatted_rec = {
                'word': rec.get('word', ''),
                'definition': rec.get('definition', ''),
                'part_of_speech': rec.get('part_of_speech', 'noun'),
                'context': rec.get('context', ''),
                'grade_level': grade_level,
                'frequency_score': rec.get('adjusted_frequency_score', 0.5),
                'academic_utility': 'high' if rec.get('word', '').lower() in self.academic_words else 'medium',
                'gap_relevance_score': rec.get('gap_relevance_score', 0.5),
                'total_score': rec.get('total_score', 0.5),
                'recommendation_rank': rec.get('recommendation_rank', 1),
                'recommendation_id': f"{student_id}_{rec.get('recommendation_rank', 1)}",
                'algorithm_version': self.algorithm_config['version'],
                'scoring_factors': rec.get('scoring_factors', {}),
                'rationale': rec.get('rationale', ''),
                'learning_objectives': ['vocabulary_expansion', 'academic_language'],
                'is_viewed': False,
                'is_practiced': False,
                'created_at': datetime.now().isoformat()
            }
            formatted_recommendations.append(formatted_rec)

        return {
            'student_id': student_id,
            'recommendations': formatted_recommendations,
            'recommendation_metadata': {
                'algorithm_version': self.algorithm_config['version'],
                'processing_timestamp': datetime.now().isoformat(),
                'total_candidates_evaluated': len(recommendations) * 5,  # Estimate
                'scoring_factors': list(self.algorithm_config['scoring_weights'].keys()),
                'vocabulary_gaps_addressed': vocabulary_gaps.get('primary_gap_areas', []),
                'grade_level': grade_level,
                'recommendation_count': len(formatted_recommendations)
            }
        }

def main():
    """Test the recommendation engine."""
    import json

    logging.basicConfig(level=logging.INFO)

    try:
        # Initialize engine
        engine = RecommendationEngine()

        # Sample student profile and linguistic analysis
        student_profile = {
            'student_id': 'S001',
            'grade_level': 7,
            'report_date': '2025-11-11T10:30:00Z'
        }

        linguistic_analysis = {
            'vocabulary_richness': 0.45,
            'academic_word_ratio': 0.08,
            'avg_sentence_length': 9.5,
            'unique_words': 75,
            'vocabulary_richness': 0.45,
            'academic_word_ratio': 0.08
        }

        print("🧪 Testing Recommendation Engine")
        print("=" * 50)

        # Generate recommendations
        recommendations = engine.generate_recommendations(
            student_profile['student_id'],
            student_profile,
            linguistic_analysis
        )

        if 'error' not in recommendations:
            print(f"✅ Generated {len(recommendations['recommendations'])} recommendations")
            print(f"🎯 Student: {recommendations['student_id']}")
            print(f"📚 Grade Level: {recommendations['recommendation_metadata']['grade_level']}")

            # Show top 3 recommendations
            print("\n🏆 Top Recommendations:")
            for i, rec in enumerate(recommendations['recommendations'][:3], 1):
                print(f"{i}. {rec['word']} (Score: {rec['total_score']:.3f})")
                print(f"   {rec['rationale']}")

            # Show algorithm metadata
            metadata = recommendations['recommendation_metadata']
            print(f"\n📊 Algorithm: v{metadata['algorithm_version']}")
            print(f"⏰ Generated: {metadata['processing_timestamp'][:19]}")
            print(f"🎯 Gaps Addressed: {', '.join(metadata['vocabulary_gaps_addressed'])}")

        else:
            print(f"❌ Recommendation generation failed: {recommendations['error']}")

        print("\n✅ Recommendation engine test completed!")

    except Exception as e:
        print(f"💥 Test failed: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
