#!/usr/bin/env python3
"""
Recommendation Validation Framework

Comprehensive validation of vocabulary recommendations against educational standards,
expert criteria, and quality benchmarks. Simulates user testing with educators
and students to ensure recommendation quality and effectiveness.
"""

import json
import logging
from typing import Dict, List, Any, Tuple
from collections import defaultdict, Counter
from recommendation_engine import RecommendationEngine
from vocabulary_profiler import VocabularyProfiler
from reference_data_loader import ReferenceDataLoader

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class RecommendationValidator:
    """
    Validates vocabulary recommendations against educational standards and expert criteria.
    """

    def __init__(self):
        self.engine = RecommendationEngine()
        self.profiler = VocabularyProfiler()
        self.reference_loader = ReferenceDataLoader()

        # Common Core State Standards for Language Arts (Vocabulary Focus)
        self.ccss_standards = {
            'CCSS.ELA-Literacy.L.6.4': 'Determine or clarify the meaning of unknown words',
            'CCSS.ELA-Literacy.L.7.4': 'Determine or clarify the meaning of unknown words and phrases',
            'CCSS.ELA-Literacy.L.8.4': 'Determine or clarify the meaning of unknown words and phrases',
            'CCSS.ELA-Literacy.L.6.6': 'Acquire and use accurately grade-appropriate general academic words',
            'CCSS.ELA-Literacy.L.7.6': 'Acquire and use accurately grade-appropriate general academic words',
            'CCSS.ELA-Literacy.L.8.6': 'Acquire and use accurately grade-appropriate general academic words'
        }

        # Academic Word List categories
        self.awl_categories = {
            'high_utility': ['analyze', 'approach', 'benefit', 'challenge', 'communicate', 'compare'],
            'medium_utility': ['component', 'concept', 'context', 'create', 'culture', 'design'],
            'low_utility': ['evidence', 'factor', 'feature', 'function', 'identify', 'impact']
        }

    def validate_recommendations_comprehensive(self, recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive validation of a recommendation set.

        Args:
            recommendations: Output from RecommendationEngine.generate_recommendations()

        Returns:
            Detailed validation report
        """
        validation_report = {
            'overall_score': 0.0,
            'validation_categories': {},
            'recommendations': []
        }

        if 'error' in recommendations:
            validation_report['error'] = recommendations['error']
            return validation_report

        recs = recommendations['recommendations']
        metadata = recommendations.get('recommendation_metadata', {})

        # Category 1: Educational Standards Alignment
        standards_score = self._validate_educational_standards(recs, metadata)
        validation_report['validation_categories']['educational_standards'] = standards_score

        # Category 2: Linguistic Appropriateness
        linguistic_score = self._validate_linguistic_appropriateness(recs, metadata)
        validation_report['validation_categories']['linguistic_appropriateness'] = linguistic_score

        # Category 3: Academic Word Balance
        academic_score = self._validate_academic_word_balance(recs)
        validation_report['validation_categories']['academic_word_balance'] = academic_score

        # Category 4: Pedagogical Effectiveness
        pedagogical_score = self._validate_pedagogical_effectiveness(recs)
        validation_report['validation_categories']['pedagogical_effectiveness'] = pedagogical_score

        # Category 5: Diversity and Balance
        diversity_score = self._validate_diversity_and_balance(recs)
        validation_report['validation_categories']['diversity_and_balance'] = diversity_score

        # Category 6: Practical Usability
        usability_score = self._validate_practical_usability(recs)
        validation_report['validation_categories']['practical_usability'] = usability_score

        # Calculate overall score (weighted average)
        weights = {
            'educational_standards': 0.25,
            'linguistic_appropriateness': 0.20,
            'academic_word_balance': 0.20,
            'pedagogical_effectiveness': 0.15,
            'diversity_and_balance': 0.10,
            'practical_usability': 0.10
        }

        overall_score = sum(
            score * weights[category]
            for category, score in validation_report['validation_categories'].items()
        )

        validation_report['overall_score'] = round(overall_score, 3)

        # Individual recommendation validation
        for rec in recs:
            rec_validation = self._validate_individual_recommendation(rec)
            validation_report['recommendations'].append(rec_validation)

        # Determine validation level
        if overall_score >= 0.85:
            validation_report['validation_level'] = 'Excellent'
            validation_report['recommendation'] = 'Ready for production use'
        elif overall_score >= 0.75:
            validation_report['validation_level'] = 'Good'
            validation_report['recommendation'] = 'Minor refinements suggested'
        elif overall_score >= 0.65:
            validation_report['validation_level'] = 'Acceptable'
            validation_report['recommendation'] = 'Significant improvements needed'
        else:
            validation_report['validation_level'] = 'Poor'
            validation_report['recommendation'] = 'Major revisions required'

        return validation_report

    def _validate_educational_standards(self, recommendations: List[Dict], metadata: Dict) -> float:
        """Validate alignment with educational standards."""
        grade_level = metadata.get('grade_level', 7)
        score_components = []

        # Check grade appropriateness
        grade_appropriate = sum(1 for rec in recommendations
                              if rec.get('grade_level') in range(grade_level-1, grade_level+2))
        grade_score = grade_appropriate / len(recommendations)
        score_components.append(('grade_appropriateness', grade_score))

        # Check academic word inclusion (CCSS requirement)
        academic_words = sum(1 for rec in recommendations
                           if rec.get('academic_utility') == 'high')
        academic_requirement = 0.4  # At least 40% academic words for middle school
        academic_score = min(academic_words / len(recommendations), 1.0)
        academic_score = academic_score / academic_requirement if academic_requirement > 0 else 0
        score_components.append(('academic_word_inclusion', min(academic_score, 1.0)))

        # Check standards alignment score
        standards_score = sum(score for _, score in score_components) / len(score_components)

        return round(standards_score, 3)

    def _validate_linguistic_appropriateness(self, recommendations: List[Dict], metadata: Dict) -> float:
        """Validate linguistic appropriateness of recommendations."""
        score_components = []

        # Check frequency appropriateness
        frequencies = [rec.get('frequency_score', 0.5) for rec in recommendations]
        avg_frequency = sum(frequencies) / len(frequencies)

        # For middle school, words should have moderate frequency (not too easy or hard)
        target_range = (0.2, 0.8)
        if target_range[0] <= avg_frequency <= target_range[1]:
            frequency_score = 1.0
        elif avg_frequency < target_range[0]:
            frequency_score = avg_frequency / target_range[0]  # Too easy
        else:
            frequency_score = (1.0 - avg_frequency) / (1.0 - target_range[1])  # Too hard

        score_components.append(('frequency_appropriateness', frequency_score))

        # Check definition quality
        definitions_present = sum(1 for rec in recommendations
                                if rec.get('definition') and len(rec.get('definition', '')) > 20)
        definition_score = definitions_present / len(recommendations)
        score_components.append(('definition_quality', definition_score))

        return round(sum(score for _, score in score_components) / len(score_components), 3)

    def _validate_academic_word_balance(self, recommendations: List[Dict]) -> float:
        """Validate balance of academic vs content words."""
        academic_count = sum(1 for rec in recommendations
                           if rec.get('academic_utility') == 'high')
        total_count = len(recommendations)

        if total_count == 0:
            return 0.0

        academic_ratio = academic_count / total_count

        # Ideal range: 50-70% academic words for middle school vocabulary building
        if 0.5 <= academic_ratio <= 0.7:
            balance_score = 1.0
        elif academic_ratio < 0.5:
            balance_score = academic_ratio / 0.5  # Too few academic words
        else:
            balance_score = (1.0 - academic_ratio) / 0.3  # Too many academic words

        return round(balance_score, 3)

    def _validate_pedagogical_effectiveness(self, recommendations: List[Dict]) -> float:
        """Validate pedagogical effectiveness of recommendations."""
        score_components = []

        # Check learning progression (easier to harder words)
        scores = [rec.get('total_score', 0.5) for rec in recommendations]
        scores_sorted = sorted(scores)

        # Check if recommendations are ordered by difficulty (progression)
        progression_score = 1.0 if scores == scores_sorted else 0.7
        score_components.append(('learning_progression', progression_score))

        # Check word variety (different parts of speech)
        pos_tags = [rec.get('part_of_speech', 'noun') for rec in recommendations]
        pos_diversity = len(set(pos_tags)) / len(pos_tags)
        pos_score = pos_diversity  # Higher diversity is better
        score_components.append(('part_of_speech_diversity', pos_score))

        # Check contextual richness
        contexts_present = sum(1 for rec in recommendations
                             if rec.get('context') and len(rec.get('context', '')) > 10)
        context_score = contexts_present / len(recommendations)
        score_components.append(('contextual_richness', context_score))

        return round(sum(score for _, score in score_components) / len(score_components), 3)

    def _validate_diversity_and_balance(self, recommendations: List[Dict]) -> float:
        """Validate diversity and balance of recommendations."""
        score_components = []

        # Check word length diversity
        word_lengths = [len(rec.get('word', '')) for rec in recommendations]
        length_diversity = len(set(word_lengths)) / len(word_lengths)
        length_score = length_diversity  # More diverse lengths are better
        score_components.append(('word_length_diversity', length_score))

        # Check thematic diversity (avoid too many similar words)
        words = [rec.get('word', '').lower() for rec in recommendations]
        # Simple diversity check: ratio of unique words
        unique_ratio = len(set(words)) / len(words)
        thematic_score = unique_ratio
        score_components.append(('thematic_diversity', thematic_score))

        return round(sum(score for _, score in score_components) / len(score_components), 3)

    def _validate_practical_usability(self, recommendations: List[Dict]) -> float:
        """Validate practical usability for educators and students."""
        score_components = []

        # Check definition clarity (not too complex)
        definitions = [rec.get('definition', '') for rec in recommendations]
        avg_definition_length = sum(len(d) for d in definitions) / len(definitions)

        # Ideal definition length: 50-150 characters
        if 50 <= avg_definition_length <= 150:
            clarity_score = 1.0
        elif avg_definition_length < 50:
            clarity_score = avg_definition_length / 50
        else:
            clarity_score = max(0.5, 150 / avg_definition_length)

        score_components.append(('definition_clarity', clarity_score))

        # Check word practicality (common, learnable words)
        practical_words = sum(1 for rec in recommendations
                            if len(rec.get('word', '')) <= 12)  # Reasonably short words
        practicality_score = practical_words / len(recommendations)
        score_components.append(('word_practicality', practicality_score))

        return round(sum(score for _, score in score_components) / len(score_components), 3)

    def _validate_individual_recommendation(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        """Validate an individual recommendation."""
        validation = dict(recommendation)  # Copy original

        # Individual quality checks
        checks = {
            'has_definition': bool(recommendation.get('definition')),
            'has_context': bool(recommendation.get('context')),
            'reasonable_length': 3 <= len(recommendation.get('word', '')) <= 15,
            'has_pos_tag': bool(recommendation.get('part_of_speech')),
            'score_in_range': 0 <= recommendation.get('total_score', 0) <= 1,
            'academic_classified': recommendation.get('academic_utility') in ['high', 'medium', 'low']
        }

        validation['quality_checks'] = checks
        validation['quality_score'] = sum(checks.values()) / len(checks)

        return validation

    def simulate_user_testing(self) -> Dict[str, Any]:
        """
        Simulate comprehensive user testing with multiple student profiles.

        Returns:
            Comprehensive testing report
        """
        print("🧪 Simulating Comprehensive User Testing")
        print("=" * 60)

        # Test cases representing different student profiles
        test_cases = [
            {
                'name': 'Struggling Reader - Grade 6',
                'profile': {'grade_level': 6, 'student_id': 'S_STRUGGLING'},
                'analysis': {
                    'vocabulary_richness': 0.35,
                    'academic_word_ratio': 0.06,
                    'avg_sentence_length': 8.5,
                    'unique_words': 45
                }
            },
            {
                'name': 'Average Student - Grade 7',
                'profile': {'grade_level': 7, 'student_id': 'S_AVERAGE'},
                'analysis': {
                    'vocabulary_richness': 0.52,
                    'academic_word_ratio': 0.11,
                    'avg_sentence_length': 11.2,
                    'unique_words': 72
                }
            },
            {
                'name': 'Advanced Learner - Grade 8',
                'profile': {'grade_level': 8, 'student_id': 'S_ADVANCED'},
                'analysis': {
                    'vocabulary_richness': 0.71,
                    'academic_word_ratio': 0.22,
                    'avg_sentence_length': 15.8,
                    'unique_words': 125
                }
            }
        ]

        testing_results = []

        for test_case in test_cases:
            print(f"\n👤 Testing: {test_case['name']}")

            # Generate recommendations
            recommendations = self.engine.generate_recommendations(
                test_case['profile']['student_id'],
                test_case['profile'],
                test_case['analysis']
            )

            if 'error' in recommendations:
                print(f"❌ Failed: {recommendations['error']}")
                continue

            # Validate recommendations
            validation = self.validate_recommendations_comprehensive(recommendations)

            print("✅ Generated and validated recommendations")
            print(f"📊 Validation Score: {validation['overall_score']:.3f}")
            print(f"🏆 Level: {validation['validation_level']}")
            print(f"💡 Recommendation: {validation['recommendation']}")

            # Show category scores
            categories = validation['validation_categories']
            print("📊 Category Scores:")
            for category, score in categories.items():
                print(f"   • {category.replace('_', ' ').title()}: {score:.3f}")

            testing_results.append({
                'test_case': test_case['name'],
                'recommendations_count': len(recommendations['recommendations']),
                'validation_score': validation['overall_score'],
                'validation_level': validation['validation_level'],
                'categories': categories
            })

        # Overall testing summary
        if testing_results:
            avg_score = sum(r['validation_score'] for r in testing_results) / len(testing_results)
            level_distribution = Counter(r['validation_level'] for r in testing_results)

            summary = {
                'total_test_cases': len(testing_results),
                'average_validation_score': round(avg_score, 3),
                'validation_level_distribution': dict(level_distribution),
                'passed_tests': sum(1 for r in testing_results if r['validation_score'] >= 0.75),
                'test_results': testing_results
            }

            print("\n📈 USER TESTING SUMMARY")
            print("=" * 60)
            print(f"📊 Average Validation Score: {summary['average_validation_score']:.3f}")
            print(f"✅ Test Cases Passed: {summary['passed_tests']}/{summary['total_test_cases']}")

            print("🏆 Validation Levels:")
            for level, count in summary['validation_level_distribution'].items():
                print(f"   • {level}: {count} cases")

            return summary

        return {'error': 'No test results generated'}

def main():
    """Run comprehensive recommendation validation."""
    print("🎯 RECOMMENDATION VALIDATION FRAMEWORK")
    print("=" * 60)

    validator = RecommendationValidator()
    results = validator.simulate_user_testing()

    if 'error' not in results:
        print("\n🎉 VALIDATION COMPLETE!")
        if results['average_validation_score'] >= 0.75:
            print("✅ Recommendations meet educational standards and quality benchmarks")
            print("🚀 Ready for deployment and educator use")
        else:
            print("⚠️ Recommendations need improvement before deployment")
            print("🔧 Focus on: educational standards alignment and pedagogical effectiveness")

        return 0
    else:
        print(f"❌ Validation failed: {results['error']}")
        return 1

if __name__ == "__main__":
    exit(main())
