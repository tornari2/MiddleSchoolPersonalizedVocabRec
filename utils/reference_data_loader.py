#!/usr/bin/env python3
"""
Reference Data Loader for Vocabulary Recommendation Engine

This module loads and provides access to reference data including:
- Grade-level appropriate words
- Word frequency data
- Word definitions and examples

Usage:
    from reference_data_loader import ReferenceDataLoader

    loader = ReferenceDataLoader()
    words = loader.get_grade_words(7, 'basic')
    definition = loader.get_word_definition('analysis')
    frequency = loader.get_word_frequency('approach')
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ReferenceDataLoader:
    """Loads and provides access to reference data for the vocabulary system."""

    def __init__(self, data_dir: str = None):
        """
        Initialize the reference data loader.

        Args:
            data_dir: Directory containing reference data files. If None, auto-detect based on environment.
        """
        if data_dir is None:
            # Auto-detect data directory based on environment
            if Path("/opt/reference_data").exists():
                # Lambda environment with layer
                data_dir = "/opt/reference_data"
            else:
                # Local development environment
                data_dir = "reference_data"

        self.data_dir = Path(data_dir)
        self._grade_words: Optional[Dict[str, Any]] = None
        self._word_frequencies: Optional[Dict[str, Any]] = None
        self._word_definitions: Optional[Dict[str, Any]] = None

        # Load data on initialization
        self._load_all_data()

    def _load_all_data(self) -> None:
        """Load all reference data files."""
        try:
            # Load grade-level words
            grade_words_path = self.data_dir / "grade_level_words.json"
            if grade_words_path.exists():
                with open(grade_words_path, 'r', encoding='utf-8') as f:
                    self._grade_words = json.load(f)
                logger.info(f"Loaded grade words data from {grade_words_path}")
            else:
                logger.warning(f"Grade words file not found: {grade_words_path}")

            # Load word frequencies
            freq_path = self.data_dir / "word_frequencies.json"
            if freq_path.exists():
                with open(freq_path, 'r', encoding='utf-8') as f:
                    self._word_frequencies = json.load(f)
                logger.info(f"Loaded word frequencies from {freq_path}")
            else:
                logger.warning(f"Word frequencies file not found: {freq_path}")

            # Load word definitions
            def_path = self.data_dir / "word_definitions.json"
            if def_path.exists():
                with open(def_path, 'r', encoding='utf-8') as f:
                    self._word_definitions = json.load(f)
                logger.info(f"Loaded word definitions from {def_path}")
            else:
                logger.warning(f"Word definitions file not found: {def_path}")

        except Exception as e:
            logger.error(f"Error loading reference data: {e}")
            raise

    def get_grade_words(self, grade: int, level: str = 'basic') -> List[str]:
        """
        Get words for a specific grade level and difficulty.

        Args:
            grade: Grade level (6, 7, or 8)
            level: Difficulty level ('basic' or 'advanced')

        Returns:
            List of words for the specified grade and level

        Raises:
            ValueError: If grade or level is invalid
        """
        if not self._grade_words:
            raise ValueError("Grade words data not loaded")

        grade_key = f"grade_{grade}"
        if grade_key not in self._grade_words:
            raise ValueError(f"Invalid grade: {grade}. Must be 6, 7, or 8")

        if level not in ['basic', 'advanced']:
            raise ValueError(f"Invalid level: {level}. Must be 'basic' or 'advanced'")

        words = self._grade_words[grade_key].get(level, [])
        return words

    def get_all_grade_words(self, grade: int) -> Dict[str, List[str]]:
        """
        Get all words for a specific grade level.

        Args:
            grade: Grade level (6, 7, or 8)

        Returns:
            Dictionary with 'basic' and 'advanced' word lists
        """
        if not self._grade_words:
            raise ValueError("Grade words data not loaded")

        grade_key = f"grade_{grade}"
        if grade_key not in self._grade_words:
            raise ValueError(f"Invalid grade: {grade}. Must be 6, 7, or 8")

        return {
            'basic': self._grade_words[grade_key].get('basic', []),
            'advanced': self._grade_words[grade_key].get('advanced', [])
        }

    def get_word_frequency(self, word: str) -> Optional[Dict[str, Any]]:
        """
        Get frequency data for a specific word.

        Args:
            word: The word to look up

        Returns:
            Dictionary with frequency and academic_score, or None if not found
        """
        if not self._word_frequencies:
            return None

        # Search through all frequency bands
        for band_name, words in self._word_frequencies.get('frequency_bands', {}).items():
            for word_data in words:
                if word_data.get('word', '').lower() == word.lower():
                    return {
                        'word': word_data['word'],
                        'frequency': word_data['frequency'],
                        'academic_score': word_data['academic_score'],
                        'frequency_band': band_name
                    }

        return None

    def get_word_definition(self, word: str) -> Optional[Dict[str, Any]]:
        """
        Get definition data for a specific word.

        Args:
            word: The word to look up

        Returns:
            Dictionary with definition, part_of_speech, and examples, or None if not found
        """
        if not self._word_definitions:
            return None

        definitions = self._word_definitions.get('definitions', {})
        return definitions.get(word.lower())

    def get_words_by_frequency_band(self, band: str) -> List[Dict[str, Any]]:
        """
        Get all words in a specific frequency band.

        Args:
            band: Frequency band ('very_high', 'high', 'medium', 'low')

        Returns:
            List of word data dictionaries
        """
        if not self._word_frequencies:
            return []

        bands = self._word_frequencies.get('frequency_bands', {})
        return bands.get(band, [])

    def get_academic_vocabulary(self, min_score: float = 8.0) -> List[Dict[str, Any]]:
        """
        Get words with high academic scores.

        Args:
            min_score: Minimum academic score threshold

        Returns:
            List of word data for academically challenging words
        """
        academic_words = []

        if self._word_frequencies:
            for band_name, words in self._word_frequencies.get('frequency_bands', {}).items():
                for word_data in words:
                    if word_data.get('academic_score', 0) >= min_score:
                        word_data_copy = word_data.copy()
                        word_data_copy['frequency_band'] = band_name
                        academic_words.append(word_data_copy)

        return academic_words

    def get_grade_appropriate_words(self, grade: int, max_frequency: float = 0.8) -> List[str]:
        """
        Get grade-appropriate words that aren't too frequent.

        Args:
            grade: Target grade level
            max_frequency: Maximum frequency threshold (0-1)

        Returns:
            List of suitable words for vocabulary building
        """
        # Get grade-appropriate words
        grade_words = set()
        grade_data = self.get_all_grade_words(grade)

        for level_words in grade_data.values():
            grade_words.update(level_words)

        # Filter by frequency (prefer less common words for building vocab)
        suitable_words = []
        for word in grade_words:
            freq_data = self.get_word_frequency(word)
            if freq_data and freq_data['frequency'] <= max_frequency:
                suitable_words.append(word)

        return suitable_words

    def search_words(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for words containing the query string.

        Args:
            query: Search query (case-insensitive)
            limit: Maximum number of results

        Returns:
            List of matching word data
        """
        results = []
        query_lower = query.lower()

        # Search in definitions
        if self._word_definitions:
            for word, data in self._word_definitions.get('definitions', {}).items():
                if query_lower in word.lower() or query_lower in data.get('definition', '').lower():
                    results.append({
                        'word': word,
                        'type': 'definition',
                        'data': data
                    })

        # Search in frequency data
        if self._word_frequencies:
            for band_name, words in self._word_frequencies.get('frequency_bands', {}).items():
                for word_data in words:
                    word = word_data.get('word', '')
                    if query_lower in word.lower():
                        results.append({
                            'word': word,
                            'type': 'frequency',
                            'data': word_data,
                            'frequency_band': band_name
                        })

        return results[:limit]

    def get_data_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the loaded reference data.

        Returns:
            Dictionary with data statistics
        """
        stats = {
            'grade_words_loaded': bool(self._grade_words),
            'frequencies_loaded': bool(self._word_frequencies),
            'definitions_loaded': bool(self._word_definitions)
        }

        if self._grade_words:
            total_words = 0
            for grade_key in ['grade_6', 'grade_7', 'grade_8']:
                if grade_key in self._grade_words:
                    grade_data = self._grade_words[grade_key]
                    total_words += len(grade_data.get('basic', []))
                    total_words += len(grade_data.get('advanced', []))
            stats['total_grade_words'] = total_words

        if self._word_frequencies:
            total_freq_words = 0
            for band_words in self._word_frequencies.get('frequency_bands', {}).values():
                total_freq_words += len(band_words)
            stats['total_frequency_words'] = total_freq_words

        if self._word_definitions:
            stats['total_definitions'] = len(self._word_definitions.get('definitions', {}))

        return stats

def main():
    """Test the reference data loader."""
    import sys

    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    try:
        loader = ReferenceDataLoader()

        # Print stats
        stats = loader.get_data_stats()
        print("Reference Data Loader Stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # Test some functionality
        print("\nTesting functionality:")

        # Test grade words
        grade_7_words = loader.get_grade_words(7, 'basic')[:5]
        print(f"Sample grade 7 basic words: {grade_7_words}")

        # Test word frequency
        analysis_freq = loader.get_word_frequency('analysis')
        if analysis_freq:
            print(f"Analysis frequency: {analysis_freq['frequency']:.3f}, academic score: {analysis_freq['academic_score']}")

        # Test word definition
        analysis_def = loader.get_word_definition('analysis')
        if analysis_def:
            print(f"Analysis definition: {analysis_def['definition'][:50]}...")

        # Test academic vocabulary
        academic_words = loader.get_academic_vocabulary(9.0)[:3]
        print(f"Sample high academic score words: {[w['word'] for w in academic_words]}")

        print("\n✅ All tests passed! Reference data loader is working correctly.")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
