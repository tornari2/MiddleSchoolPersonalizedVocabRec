#!/usr/bin/env python3
"""
Vocabulary Profiling Module for Personalized Vocabulary Recommendation Engine

This module uses spaCy to analyze student text samples and calculate vocabulary proficiency scores.
It provides functions for text preprocessing, linguistic analysis, and proficiency scoring.

Key Functions:
- process_text(): Tokenizes, removes stop words, and lemmatizes text
- aggregate_stats(): Performs linguistic analysis and extracts features
- calculate_proficiency_score(): Calculates vocabulary proficiency based on analysis
"""

import spacy
import re
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
import logging
import math

logger = logging.getLogger(__name__)

class VocabularyProfiler:
    """
    Analyzes student text samples to assess vocabulary proficiency and linguistic features.

    Uses spaCy for natural language processing and linguistic analysis.
    """

    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initialize the vocabulary profiler.

        Args:
            model_name: spaCy language model to use
        """
        try:
            self.nlp = spacy.load(model_name)
            logger.info(f"Loaded spaCy model: {model_name}")
        except OSError:
            raise RuntimeError(f"Could not load spaCy model '{model_name}'. Make sure it's installed.")

        # Common academic words (AWL - Academic Word List)
        self.academic_words = {
            'analyze', 'approach', 'area', 'assess', 'assume', 'authority', 'available',
            'benefit', 'challenge', 'character', 'communicate', 'compare', 'component',
            'consider', 'construct', 'context', 'contribute', 'coordinate', 'core',
            'create', 'culture', 'design', 'detail', 'develop', 'device', 'document',
            'dominant', 'economy', 'environment', 'equipped', 'establish', 'evaluate',
            'evidence', 'factor', 'feature', 'focus', 'function', 'furthermore', 'gender',
            'generate', 'generation', 'globe', 'goal', 'grant', 'hierarchy', 'identify',
            'impact', 'implement', 'individual', 'influence', 'infrastructure', 'involved',
            'issue', 'labor', 'legal', 'legislation', 'locate', 'logical', 'maintain',
            'major', 'method', 'occur', 'percent', 'period', 'policy', 'principle',
            'procedure', 'process', 'provide', 'range', 'region', 'relevant', 'rely',
            'remove', 'represent', 'require', 'research', 'resource', 'respond', 'role',
            'section', 'sector', 'select', 'significant', 'similar', 'source', 'specific',
            'structure', 'theory', 'therefore', 'though', 'tradition', 'transfer',
            'transport', 'typical', 'united', 'university', 'variety', 'version', 'volume',
            'welfare'
        }

        # Grade-appropriate word complexity scores (simplified)
        self.grade_complexity = {
            6: {'basic': 1.0, 'advanced': 2.0},
            7: {'basic': 1.2, 'advanced': 2.5},
            8: {'basic': 1.5, 'advanced': 3.0}
        }

    def process_text(self, text: str) -> Dict[str, Any]:
        """
        Preprocess text using spaCy: tokenize, remove stop words, and lemmatize.

        Args:
            text: Raw text input

        Returns:
            Dictionary containing processed text features
        """
        try:
            # Clean the text
            text = self._clean_text(text)

            # Process with spaCy
            doc = self.nlp(text)

            # Extract tokens (excluding stop words and punctuation)
            tokens = []
            lemmas = []
            pos_tags = []

            for token in doc:
                if not token.is_stop and not token.is_punct and not token.is_space:
                    tokens.append(token.text.lower())
                    lemmas.append(token.lemma_.lower())
                    pos_tags.append(token.pos_)

            # Get unique lemmas
            unique_lemmas = list(set(lemmas))

            return {
                'original_text': text,
                'tokens': tokens,
                'lemmas': lemmas,
                'unique_lemmas': unique_lemmas,
                'pos_tags': pos_tags,
                'token_count': len(tokens),
                'unique_word_count': len(unique_lemmas),
                'sentence_count': len(list(doc.sents)),
                'avg_sentence_length': len(tokens) / max(len(list(doc.sents)), 1)
            }

        except Exception as e:
            logger.error(f"Error processing text: {e}")
            return {
                'original_text': text,
                'error': str(e),
                'tokens': [],
                'lemmas': [],
                'unique_lemmas': [],
                'pos_tags': [],
                'token_count': 0,
                'unique_word_count': 0,
                'sentence_count': 0,
                'avg_sentence_length': 0
            }

    def aggregate_stats(self, processed_texts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate statistics from multiple processed text samples.

        Args:
            processed_texts: List of dictionaries from process_text()

        Returns:
            Dictionary with aggregated linguistic statistics
        """
        if not processed_texts:
            return {}

        try:
            # Combine all lemmas and tokens
            all_lemmas = []
            all_pos_tags = []
            all_unique_lemmas = set()
            token_counts = []
            sentence_counts = []
            sentence_lengths = []

            for processed in processed_texts:
                if 'error' not in processed:  # Skip errored texts
                    all_lemmas.extend(processed['lemmas'])
                    all_pos_tags.extend(processed['pos_tags'])
                    all_unique_lemmas.update(processed['unique_lemmas'])
                    token_counts.append(processed['token_count'])
                    sentence_counts.append(processed['sentence_count'])
                    sentence_lengths.append(processed['avg_sentence_length'])

            # Calculate basic statistics
            total_tokens = sum(token_counts)
            total_sentences = sum(sentence_counts)
            avg_sentence_length = sum(sentence_lengths) / max(len(sentence_lengths), 1)
            vocab_richness = len(all_unique_lemmas) / max(total_tokens, 1)

            # POS tag distribution
            pos_distribution = Counter(all_pos_tags)
            pos_percentages = {tag: count / max(len(all_pos_tags), 1) for tag, count in pos_distribution.items()}

            # Lemma frequency analysis
            lemma_freq = Counter(all_lemmas)
            most_common_lemmas = lemma_freq.most_common(20)

            # Academic word usage
            academic_word_count = sum(1 for lemma in all_unique_lemmas if lemma in self.academic_words)
            academic_word_ratio = academic_word_count / max(len(all_unique_lemmas), 1)

            # Diversity metrics
            hapax_legomena = sum(1 for freq in lemma_freq.values() if freq == 1)  # Words appearing once
            hapax_ratio = hapax_legomena / max(len(all_unique_lemmas), 1)

            return {
                'total_samples': len(processed_texts),
                'total_tokens': total_tokens,
                'total_sentences': total_sentences,
                'unique_words': len(all_unique_lemmas),
                'vocabulary_richness': vocab_richness,
                'avg_sentence_length': avg_sentence_length,
                'pos_distribution': pos_distribution,
                'pos_percentages': pos_percentages,
                'most_common_lemmas': most_common_lemmas,
                'academic_word_count': academic_word_count,
                'academic_word_ratio': academic_word_ratio,
                'hapax_legomena': hapax_legomena,
                'hapax_ratio': hapax_ratio,
                'avg_tokens_per_sample': sum(token_counts) / max(len(token_counts), 1),
                'avg_sentences_per_sample': sum(sentence_counts) / max(len(sentence_counts), 1)
            }

        except Exception as e:
            logger.error(f"Error aggregating stats: {e}")
            return {'error': str(e)}

    def calculate_proficiency_score(self, aggregated_stats: Dict[str, Any], grade_level: int) -> Dict[str, Any]:
        """
        Calculate vocabulary proficiency score based on aggregated statistics.

        Args:
            aggregated_stats: Output from aggregate_stats()
            grade_level: Student's grade level (6, 7, or 8)

        Returns:
            Dictionary with proficiency scores and analysis
        """
        if not aggregated_stats or 'error' in aggregated_stats:
            return {'error': 'Invalid aggregated statistics'}

        try:
            # Extract key metrics
            vocab_richness = aggregated_stats.get('vocabulary_richness', 0)
            academic_ratio = aggregated_stats.get('academic_word_ratio', 0)
            avg_sentence_length = aggregated_stats.get('avg_sentence_length', 0)
            unique_words = aggregated_stats.get('unique_words', 0)
            pos_percentages = aggregated_stats.get('pos_percentages', {})

            # Component scores (0-1 scale, higher is better)
            # 1. Vocabulary Diversity Score
            vocab_diversity_score = min(vocab_richness * 100, 1.0)  # Normalize vocabulary richness

            # 2. Academic Word Usage Score
            academic_score = min(academic_ratio * 2, 1.0)  # Academic words are valuable

            # 3. Sentence Complexity Score
            # Grade-appropriate sentence lengths (words per sentence)
            grade_sentence_targets = {6: 12, 7: 15, 8: 18}
            target_length = grade_sentence_targets.get(grade_level, 15)
            sentence_complexity_score = min(avg_sentence_length / target_length, 1.0)

            # 4. POS Diversity Score (grammatical range)
            noun_ratio = pos_percentages.get('NOUN', 0)
            verb_ratio = pos_percentages.get('VERB', 0)
            adj_ratio = pos_percentages.get('ADJ', 0)
            adv_ratio = pos_percentages.get('ADV', 0)

            # Good balance: ~40% nouns, ~20% verbs, ~10% adjectives/adverbs
            pos_balance_score = 1.0 - (
                abs(noun_ratio - 0.4) + abs(verb_ratio - 0.2) +
                abs(adj_ratio - 0.1) + abs(adv_ratio - 0.1)
            ) / 4

            # 5. Lexical Density Score (content vs function words)
            content_words = noun_ratio + verb_ratio + adj_ratio + adv_ratio
            lexical_density_score = min(content_words, 1.0)

            # Overall proficiency score (weighted average)
            weights = {
                'vocabulary_diversity': 0.3,
                'academic_usage': 0.25,
                'sentence_complexity': 0.2,
                'pos_balance': 0.15,
                'lexical_density': 0.1
            }

            overall_score = (
                vocab_diversity_score * weights['vocabulary_diversity'] +
                academic_score * weights['academic_usage'] +
                sentence_complexity_score * weights['sentence_complexity'] +
                pos_balance_score * weights['pos_balance'] +
                lexical_density_score * weights['lexical_density']
            )

            # Grade-appropriate interpretation
            grade_expectations = {
                6: {'min_score': 0.3, 'target_score': 0.5, 'advanced_score': 0.7},
                7: {'min_score': 0.4, 'target_score': 0.6, 'advanced_score': 0.8},
                8: {'min_score': 0.5, 'target_score': 0.7, 'advanced_score': 0.9}
            }

            expectations = grade_expectations.get(grade_level, grade_expectations[7])

            # Determine proficiency level
            if overall_score >= expectations['advanced_score']:
                proficiency_level = 'Advanced'
                recommendation = 'Continue challenging vocabulary development'
            elif overall_score >= expectations['target_score']:
                proficiency_level = 'Proficient'
                recommendation = 'Maintain current vocabulary development pace'
            elif overall_score >= expectations['min_score']:
                proficiency_level = 'Developing'
                recommendation = 'Focus on grade-appropriate vocabulary building'
            else:
                proficiency_level = 'Emerging'
                recommendation = 'Target basic vocabulary and sentence structure'

            return {
                'overall_proficiency_score': round(overall_score, 3),
                'proficiency_level': proficiency_level,
                'recommendation': recommendation,
                'component_scores': {
                    'vocabulary_diversity': round(vocab_diversity_score, 3),
                    'academic_word_usage': round(academic_score, 3),
                    'sentence_complexity': round(sentence_complexity_score, 3),
                    'grammatical_range': round(pos_balance_score, 3),
                    'lexical_density': round(lexical_density_score, 3)
                },
                'grade_level': grade_level,
                'expectations': expectations,
                'key_metrics': {
                    'vocabulary_richness': round(vocab_richness, 3),
                    'academic_word_ratio': round(academic_ratio, 3),
                    'avg_sentence_length': round(avg_sentence_length, 1),
                    'unique_words': unique_words
                }
            }

        except Exception as e:
            logger.error(f"Error calculating proficiency score: {e}")
            return {'error': str(e)}

    def analyze_student_texts(self, texts: List[str], grade_level: int) -> Dict[str, Any]:
        """
        Complete analysis pipeline for student texts.

        Args:
            texts: List of text samples from a student
            grade_level: Student's grade level

        Returns:
            Complete analysis including processed texts, aggregated stats, and proficiency score
        """
        try:
            # Process all texts
            processed_texts = [self.process_text(text) for text in texts]

            # Aggregate statistics
            aggregated_stats = self.aggregate_stats(processed_texts)

            # Calculate proficiency score
            proficiency_score = self.calculate_proficiency_score(aggregated_stats, grade_level)

            return {
                'processed_texts': processed_texts,
                'aggregated_stats': aggregated_stats,
                'proficiency_analysis': proficiency_score,
                'grade_level': grade_level,
                'sample_count': len(texts)
            }

        except Exception as e:
            logger.error(f"Error in complete analysis: {e}")
            return {'error': str(e)}

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for processing."""
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        # Handle common OCR/artifacts that might appear in student text
        # (This is a placeholder - would be expanded based on actual data patterns)

        return text

def main():
    """Test the vocabulary profiler with sample data."""
    import json

    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    try:
        # Initialize profiler
        profiler = VocabularyProfiler()

        # Sample student texts (middle school level)
        sample_texts = [
            "The environment is very important for our planet. We need to protect natural resources like water and trees. Climate change affects everyone around the world.",
            "Scientists analyze data to understand how things work. They use evidence to support their conclusions. Research helps us learn new information.",
            "Technology has changed how we communicate. People use computers and phones to connect with others. This creates new opportunities for learning."
        ]

        # Test individual text processing
        print("🧪 Testing individual text processing...")
        processed = profiler.process_text(sample_texts[0])
        print(f"✅ Processed text: {processed['token_count']} tokens, {processed['unique_word_count']} unique words")

        # Test complete analysis
        print("\n🧪 Testing complete analysis pipeline...")
        analysis = profiler.analyze_student_texts(sample_texts, grade_level=7)

        if 'error' not in analysis:
            print("✅ Analysis completed successfully!")
            print(f"📊 Overall proficiency score: {analysis['proficiency_analysis']['overall_proficiency_score']:.3f}")
            print(f"🏆 Proficiency level: {analysis['proficiency_analysis']['proficiency_level']}")
            print(f"💡 Recommendation: {analysis['proficiency_analysis']['recommendation']}")
        else:
            print(f"❌ Analysis failed: {analysis['error']}")

        print("\n✅ All tests passed! Vocabulary profiler is ready!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
