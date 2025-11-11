#!/usr/bin/env python3
"""
Integrated Data Generation System for Vocabulary Recommendation Engine

This script provides a complete end-to-end data generation and validation system that:
1. Loads reference data (vocabulary, definitions, frequencies)
2. Generates synthetic student data using templates
3. Validates generated data quality and format
4. Performs comprehensive testing of the data generation pipeline

Usage:
    python data_generation_system.py --full-test    # Complete end-to-end test
    python data_generation_system.py --generate     # Generate production data
    python data_generation_system.py --validate     # Validate existing data
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple
import logging
from datetime import datetime

from reference_data_loader import ReferenceDataLoader
from data_generator import SyntheticDataGenerator

logger = logging.getLogger(__name__)

class DataGenerationSystem:
    """Integrated system for data generation and validation."""

    def __init__(self, seed: int = 42):
        """
        Initialize the integrated data generation system.

        Args:
            seed: Random seed for reproducible generation
        """
        self.seed = seed
        self.data_loader = None
        self.generator = None

    def initialize_system(self) -> bool:
        """
        Initialize all system components.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info("🔧 Initializing Data Generation System...")

            # Initialize reference data loader
            self.data_loader = ReferenceDataLoader()
            logger.info("✅ Reference data loader initialized")

            # Initialize synthetic data generator
            self.generator = SyntheticDataGenerator(seed=self.seed)
            logger.info("✅ Synthetic data generator initialized")

            # Validate system components
            if self._validate_system_components():
                logger.info("🎉 System initialization complete!")
                return True
            else:
                logger.error("❌ System validation failed")
                return False

        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            return False

    def _validate_system_components(self) -> bool:
        """Validate that all system components are working correctly."""
        logger.info("🔍 Validating system components...")

        try:
            # Test reference data loader
            stats = self.data_loader.get_data_stats()
            if not all([stats['grade_words_loaded'], stats['frequencies_loaded'], stats['definitions_loaded']]):
                logger.error("❌ Reference data loading failed")
                return False

            # Test basic data access
            grade_7_words = self.data_loader.get_grade_words(7, 'basic')
            if len(grade_7_words) < 50:
                logger.warning(f"⚠️  Only {len(grade_7_words)} grade 7 basic words loaded")

            analysis_def = self.data_loader.get_word_definition('analysis')
            if not analysis_def:
                logger.error("❌ Word definition lookup failed")
                return False

            analysis_freq = self.data_loader.get_word_frequency('analysis')
            if not analysis_freq:
                logger.warning("⚠️  Word frequency lookup failed")

            logger.info("✅ System components validated")
            return True

        except Exception as e:
            logger.error(f"❌ Component validation failed: {e}")
            return False

    def run_full_test(self, num_students: int = 5) -> Dict[str, Any]:
        """
        Run comprehensive end-to-end testing.

        Args:
            num_students: Number of students to generate for testing

        Returns:
            Dictionary with test results
        """
        logger.info(f"🧪 Running full system test with {num_students} students")

        results = {
            "timestamp": datetime.now().isoformat(),
            "tests_run": [],
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "details": {}
        }

        # Test 1: System initialization
        logger.info("Test 1: System initialization")
        init_success = self.initialize_system()
        results["tests_run"].append("system_initialization")
        results["details"]["system_initialization"] = init_success
        if init_success:
            results["passed"] += 1
        else:
            results["failed"] += 1

        if not init_success:
            logger.error("❌ Cannot continue testing - system initialization failed")
            return results

        # Test 2: Reference data integrity
        logger.info("Test 2: Reference data integrity")
        data_integrity = self._test_reference_data_integrity()
        results["tests_run"].append("reference_data_integrity")
        results["details"]["reference_data_integrity"] = data_integrity
        if data_integrity["passed"]:
            results["passed"] += 1
        else:
            results["failed"] += 1

        # Test 3: Data generation pipeline
        logger.info("Test 3: Data generation pipeline")
        generation_test = self._test_data_generation(num_students)
        results["tests_run"].append("data_generation")
        results["details"]["data_generation"] = generation_test
        if generation_test["passed"]:
            results["passed"] += 1
        else:
            results["failed"] += 1

        # Test 4: Data quality validation
        logger.info("Test 4: Data quality validation")
        quality_test = self._test_data_quality(generation_test.get("output_file"))
        results["tests_run"].append("data_quality")
        results["details"]["data_quality"] = quality_test
        if quality_test["passed"]:
            results["passed"] += 1
        else:
            results["failed"] += 1

        # Test 5: Vocabulary consistency
        logger.info("Test 5: Vocabulary consistency")
        vocab_test = self._test_vocabulary_consistency(generation_test.get("output_file"))
        results["tests_run"].append("vocabulary_consistency")
        results["details"]["vocabulary_consistency"] = vocab_test
        if vocab_test["passed"]:
            results["passed"] += 1
        else:
            results["failed"] += 1

        # Summary
        total_tests = len(results["tests_run"])
        pass_rate = results["passed"] / total_tests if total_tests > 0 else 0

        results["summary"] = {
            "total_tests": total_tests,
            "pass_rate": pass_rate,
            "overall_status": "PASSED" if results["failed"] == 0 else "FAILED"
        }

        logger.info("\n📊 Test Results Summary:")
        logger.info(f"   • Tests run: {total_tests}")
        logger.info(f"   • Passed: {results['passed']}")
        logger.info(f"   • Failed: {results['failed']}")
        logger.info(f"   • Pass rate: {pass_rate:.1%}")
        logger.info(f"   • Overall: {results['summary']['overall_status']}")

        return results

    def _test_reference_data_integrity(self) -> Dict[str, Any]:
        """Test reference data integrity and accessibility."""
        result = {"passed": True, "checks": [], "issues": []}

        try:
            # Check grade words availability
            for grade in [6, 7, 8]:
                for level in ['basic', 'advanced']:
                    words = self.data_loader.get_grade_words(grade, level)
                    if len(words) < 20:
                        result["issues"].append(f"Grade {grade} {level}: only {len(words)} words")
                        result["passed"] = False

            result["checks"].append("grade_words_availability")

            # Check word definitions
            test_words = ['analysis', 'approach', 'benefit', 'challenge']
            for word in test_words:
                definition = self.data_loader.get_word_definition(word)
                if not definition:
                    result["issues"].append(f"Missing definition for '{word}'")
                    result["passed"] = False

            result["checks"].append("word_definitions")

            # Check word frequencies (using words that should be in frequency data)
            freq_test_words = ['analysis', 'approach', 'benefit', 'factor']
            for word in freq_test_words:
                freq_data = self.data_loader.get_word_frequency(word)
                if not freq_data:
                    result["issues"].append(f"Missing frequency data for '{word}'")
                    result["passed"] = False

            result["checks"].append("word_frequencies")

        except Exception as e:
            result["passed"] = False
            result["issues"].append(f"Exception: {e}")

        return result

    def _test_data_generation(self, num_students: int) -> Dict[str, Any]:
        """Test data generation pipeline."""
        result = {"passed": True, "output_file": None, "stats": {}}

        try:
            # Generate test data
            test_output_dir = f"test_output_{int(datetime.now().timestamp())}"
            output_file = self.generator.generate_all_data(
                num_students=num_students,
                output_dir=test_output_dir
            )

            result["output_file"] = output_file

            # Load and validate generated data
            with open(output_file, 'r', encoding='utf-8') as f:
                samples = [json.loads(line) for line in f]

            # Basic validation
            expected_samples = num_students * 30  # 30 samples per student
            if len(samples) != expected_samples:
                result["passed"] = False
                result["issues"] = [f"Expected {expected_samples} samples, got {len(samples)}"]
                return result

            # Check sample structure
            required_fields = ['student_id', 'grade_level', 'timestamp', 'assignment_type', 'text']
            for i, sample in enumerate(samples[:5]):  # Check first 5 samples
                for field in required_fields:
                    if field not in sample:
                        result["passed"] = False
                        result["issues"] = [f"Sample {i}: missing field '{field}'"]
                        return result

            # Check grade distribution
            grades = {}
            for sample in samples:
                grade = sample['grade_level']
                grades[grade] = grades.get(grade, 0) + 1

            result["stats"] = {
                "total_samples": len(samples),
                "grade_distribution": grades,
                "sample_types": {}
            }

            # Check sample types
            for sample in samples:
                sample_type = sample['assignment_type']
                result["stats"]["sample_types"][sample_type] = result["stats"]["sample_types"].get(sample_type, 0) + 1

        except Exception as e:
            result["passed"] = False
            result["issues"] = [f"Exception: {e}"]

        return result

    def _test_data_quality(self, data_file: str) -> Dict[str, Any]:
        """Test quality of generated data."""
        result = {"passed": True, "quality_metrics": {}}

        if not data_file or not Path(data_file).exists():
            result["passed"] = False
            result["issues"] = ["Data file not found"]
            return result

        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                samples = [json.loads(line) for line in f]

            # Quality checks
            text_lengths = []
            vocab_usage = {}
            grade_appropriate_checks = []

            for sample in samples[:50]:  # Check first 50 samples for performance
                text = sample.get('text', '')
                text_lengths.append(len(text))

                # Check vocabulary usage
                vocab_focus = sample.get('vocabulary_focus', [])
                for word in vocab_focus:
                    vocab_usage[word] = vocab_usage.get(word, 0) + 1

                # Check if vocabulary is grade-appropriate
                grade = sample.get('grade_level', 7)
                grade_words = set(self.data_loader.get_all_grade_words(grade)['basic'] +
                                self.data_loader.get_all_grade_words(grade)['advanced'])

                vocab_appropriate = all(word in grade_words for word in vocab_focus)
                grade_appropriate_checks.append(vocab_appropriate)

            # Quality metrics
            result["quality_metrics"] = {
                "avg_text_length": sum(text_lengths) / len(text_lengths) if text_lengths else 0,
                "min_text_length": min(text_lengths) if text_lengths else 0,
                "max_text_length": max(text_lengths) if text_lengths else 0,
                "unique_vocab_words": len(vocab_usage),
                "grade_appropriate_rate": sum(grade_appropriate_checks) / len(grade_appropriate_checks) if grade_appropriate_checks else 0
            }

            # Quality thresholds
            if result["quality_metrics"]["avg_text_length"] < 50:
                result["passed"] = False
                result["issues"] = ["Average text length too short"]
            elif result["quality_metrics"]["grade_appropriate_rate"] < 0.8:
                result["passed"] = False
                result["issues"] = ["Low grade-appropriate vocabulary rate"]

        except Exception as e:
            result["passed"] = False
            result["issues"] = [f"Exception: {e}"]

        return result

    def _test_vocabulary_consistency(self, data_file: str) -> Dict[str, Any]:
        """Test vocabulary consistency across generated data."""
        result = {"passed": True, "consistency_metrics": {}}

        if not data_file or not Path(data_file).exists():
            result["passed"] = False
            result["issues"] = ["Data file not found"]
            return result

        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                samples = [json.loads(line) for line in f]

            # Analyze vocabulary patterns
            grade_vocab = {}
            word_frequencies = {}

            for sample in samples:
                grade = sample.get('grade_level', 7)
                vocab_focus = sample.get('vocabulary_focus', [])

                if grade not in grade_vocab:
                    grade_vocab[grade] = []

                grade_vocab[grade].extend(vocab_focus)

                for word in vocab_focus:
                    word_frequencies[word] = word_frequencies.get(word, 0) + 1

            # Check grade-level vocabulary separation
            result["consistency_metrics"] = {
                "grade_vocab_diversity": {grade: len(set(words)) for grade, words in grade_vocab.items()},
                "top_vocab_words": sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)[:10],
                "vocab_distribution": len(word_frequencies)
            }

            # Consistency checks
            for grade, words in grade_vocab.items():
                unique_words = len(set(words))
                if unique_words < 10:  # Should have reasonable vocabulary diversity
                    result["passed"] = False
                    result["issues"] = [f"Grade {grade}: insufficient vocabulary diversity ({unique_words} unique words)"]

        except Exception as e:
            result["passed"] = False
            result["issues"] = [f"Exception: {e}"]

        return result

    def generate_production_data(self, num_students: int = 20, output_dir: str = "production_data") -> str:
        """
        Generate production-ready data for the vocabulary recommendation system.

        Args:
            num_students: Number of students to generate data for
            output_dir: Output directory for production data

        Returns:
            Path to generated data file
        """
        logger.info(f"🏭 Generating production data for {num_students} students")

        if not self.generator:
            if not self.initialize_system():
                raise RuntimeError("Failed to initialize system")

        return self.generator.generate_all_data(
            num_students=num_students,
            output_dir=output_dir
        )

def main():
    """Main entry point for the data generation system."""
    parser = argparse.ArgumentParser(description="Integrated Data Generation System")
    parser.add_argument("--full-test", action="store_true",
                       help="Run complete end-to-end system test")
    parser.add_argument("--generate", action="store_true",
                       help="Generate production data")
    parser.add_argument("--validate", action="store_true",
                       help="Validate existing data")
    parser.add_argument("--num-students", type=int, default=20,
                       help="Number of students for testing/generation")
    parser.add_argument("--output-dir", default="production_data",
                       help="Output directory for generated data")
    parser.add_argument("--seed", type=int, default=42,
                       help="Random seed for reproducible generation")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")

    args = parser.parse_args()

    # Set up logging
    level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')

    try:
        system = DataGenerationSystem(seed=args.seed)

        if args.full_test:
            # Run comprehensive testing
            results = system.run_full_test(num_students=args.num_students)

            # Save test results
            results_file = Path("test_results.json")
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            print(f"📊 Test results saved to {results_file}")

            if results["failed"] == 0:
                print("🎉 All tests passed! System is ready for production.")
                return 0
            else:
                print(f"❌ {results['failed']} tests failed. Check test_results.json for details.")
                return 1

        elif args.generate:
            # Generate production data
            output_file = system.generate_production_data(
                num_students=args.num_students,
                output_dir=args.output_dir
            )
            print(f"✅ Production data generated: {output_file}")
            return 0

        elif args.validate:
            # Validate existing data
            if not system.initialize_system():
                print("❌ System initialization failed")
                return 1

            # Look for existing data
            data_files = list(Path(".").glob("**/student_text_samples.jsonl"))
            if not data_files:
                print("❌ No data files found to validate")
                return 1

            data_file = data_files[0]
            print(f"🔍 Validating data file: {data_file}")

            quality_test = system._test_data_quality(str(data_file))
            vocab_test = system._test_vocabulary_consistency(str(data_file))

            if quality_test["passed"] and vocab_test["passed"]:
                print("✅ Data validation passed!")
                return 0
            else:
                print("❌ Data validation failed!")
                if not quality_test["passed"]:
                    print(f"Quality issues: {quality_test.get('issues', [])}")
                if not vocab_test["passed"]:
                    print(f"Vocabulary issues: {vocab_test.get('issues', [])}")
                return 1

        else:
            # Default: show help
            parser.print_help()
            return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
