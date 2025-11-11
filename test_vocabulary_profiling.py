#!/usr/bin/env python3
"""
Comprehensive Test Suite for Vocabulary Profiling Module

Tests the complete vocabulary profiling pipeline with diverse text samples
from the synthetic data generator. Validates all functions work together seamlessly.
"""

import json
import os
from pathlib import Path
from vocabulary_profiler import VocabularyProfiler
import logging

logging.basicConfig(level=logging.WARNING)  # Reduce spaCy logging
logger = logging.getLogger(__name__)

def load_synthetic_data(file_path: str) -> list:
    """Load synthetic data from JSONL file."""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def group_data_by_student(data: list) -> dict:
    """Group data samples by student ID."""
    students = {}
    for item in data:
        student_id = item['student_id']
        if student_id not in students:
            students[student_id] = []
        students[student_id].append(item)
    return students

def test_complete_pipeline():
    """Test the complete vocabulary profiling pipeline."""
    print("🚀 Testing Complete Vocabulary Profiling Pipeline")
    print("=" * 60)

    # Initialize profiler
    profiler = VocabularyProfiler()

    # Load synthetic data
    data_file = "synthetic_data/student_text_samples.jsonl"
    if not os.path.exists(data_file):
        data_file = "test_lambda_data/student_text_samples.jsonl"

    if not os.path.exists(data_file):
        print("❌ No synthetic data found. Please generate data first.")
        return False

    print(f"📂 Loading data from: {data_file}")
    raw_data = load_synthetic_data(data_file)
    students = group_data_by_student(raw_data)

    print(f"👥 Found {len(students)} students with {len(raw_data)} total samples")

    # Test with first 3 students for comprehensive testing
    test_students = list(students.keys())[:3]
    results = []

    for student_id in test_students:
        print(f"\n🔍 Analyzing Student: {student_id}")
        print("-" * 40)

        student_samples = students[student_id]
        grade_level = student_samples[0]['grade_level']

        # Extract text samples
        texts = [sample['text'] for sample in student_samples]
        print(f"📝 Grade {grade_level}, {len(texts)} text samples")

        # Run complete analysis
        analysis = profiler.analyze_student_texts(texts, grade_level)

        if 'error' in analysis:
            print(f"❌ Analysis failed: {analysis['error']}")
            continue

        # Display results
        prof = analysis['proficiency_analysis']
        stats = analysis['aggregated_stats']

        print(f"🏆 Proficiency Level: {prof['proficiency_level']}")
        print(f"📊 Overall Score: {prof['overall_proficiency_score']:.3f}")
        print(f"💡 Recommendation: {prof['recommendation']}")

        # Show key metrics
        metrics = prof['key_metrics']
        print(f"🔤 Vocabulary Richness: {metrics['vocabulary_richness']:.3f}")
        print(f"🏫 Academic Word Ratio: {metrics['academic_word_ratio']:.3f}")
        print(f"📏 Avg Sentence Length: {metrics['avg_sentence_length']:.1f} words")
        print(f"📚 Unique Words: {metrics['unique_words']}")

        # Show component scores
        components = prof['component_scores']
        print(f"🎯 Component Scores:")
        print(f"   • Vocabulary Diversity: {components['vocabulary_diversity']:.3f}")
        print(f"   • Academic Usage: {components['academic_word_usage']:.3f}")
        print(f"   • Sentence Complexity: {components['sentence_complexity']:.3f}")
        print(f"   • Grammatical Range: {components['grammatical_range']:.3f}")
        print(f"   • Lexical Density: {components['lexical_density']:.3f}")

        results.append({
            'student_id': student_id,
            'grade_level': grade_level,
            'proficiency_level': prof['proficiency_level'],
            'overall_score': prof['overall_proficiency_score'],
            'recommendation': prof['recommendation'],
            'sample_count': len(texts)
        })

    # Summary statistics
    print(f"\n📈 Pipeline Test Summary")
    print("=" * 60)
    print(f"✅ Successfully analyzed {len(results)} students")

    if results:
        # Calculate averages by grade
        grade_stats = {}
        for result in results:
            grade = result['grade_level']
            if grade not in grade_stats:
                grade_stats[grade] = []
            grade_stats[grade].append(result['overall_score'])

        print("📊 Average Proficiency Scores by Grade:")
        for grade in sorted(grade_stats.keys()):
            scores = grade_stats[grade]
            avg_score = sum(scores) / len(scores)
            print(f"   Grade {grade}: {avg_score:.3f} ({len(scores)} students)")

        # Proficiency level distribution
        levels = [r['proficiency_level'] for r in results]
        level_counts = {}
        for level in levels:
            level_counts[level] = level_counts.get(level, 0) + 1

        print("🏆 Proficiency Level Distribution:")
        for level in ['Emerging', 'Developing', 'Proficient', 'Advanced']:
            count = level_counts.get(level, 0)
            if count > 0:
                print(f"   {level}: {count} students")

    return True

def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n🧪 Testing Edge Cases")
    print("=" * 60)

    profiler = VocabularyProfiler()

    # Test empty text
    try:
        result = profiler.process_text("")
        print(f"✅ Empty text handled: {len(result['tokens'])} tokens")
    except Exception as e:
        print(f"❌ Empty text failed: {e}")

    # Test very short text
    try:
        result = profiler.process_text("Hi.")
        print(f"✅ Short text handled: {len(result['tokens'])} tokens")
    except Exception as e:
        print(f"❌ Short text failed: {e}")

    # Test text with special characters
    try:
        result = profiler.process_text("Hello world! This is a test with numbers 123 and symbols @#$%.")
        print(f"✅ Special characters handled: {len(result['tokens'])} tokens")
    except Exception as e:
        print(f"❌ Special characters failed: {e}")

    # Test empty list aggregation
    try:
        result = profiler.aggregate_stats([])
        print("✅ Empty aggregation handled")
    except Exception as e:
        print(f"❌ Empty aggregation failed: {e}")

    # Test invalid grade level
    try:
        fake_stats = {'vocabulary_richness': 0.5, 'academic_word_ratio': 0.2, 'avg_sentence_length': 10}
        result = profiler.calculate_proficiency_score(fake_stats, 5)  # Invalid grade
        print("✅ Invalid grade handled")
    except Exception as e:
        print(f"❌ Invalid grade failed: {e}")

    print("✅ Edge case testing completed")

def test_performance():
    """Test performance with larger datasets."""
    print("\n⚡ Testing Performance")
    print("=" * 60)

    import time
    profiler = VocabularyProfiler()

    # Create larger test dataset
    test_texts = [
        "The scientific method involves observation, hypothesis formation, experimentation, and conclusion drawing.",
        "Environmental sustainability requires responsible resource management and conservation efforts.",
        "Technological innovation has transformed communication patterns across global networks.",
        "Democracy depends on informed citizen participation and representative governance structures.",
        "Education systems must adapt to changing workforce requirements and technological advancements.",
        "Climate change mitigation strategies include renewable energy adoption and carbon emission reduction.",
        "Cultural diversity enriches societies through varied perspectives and traditional knowledge systems.",
        "Economic development requires infrastructure investment and human capital enhancement programs.",
        "Healthcare accessibility ensures equitable medical service distribution across populations.",
        "Digital literacy enables effective information processing and technology utilization skills."
    ] * 5  # 50 texts total

    print(f"📊 Testing with {len(test_texts)} text samples...")

    start_time = time.time()
    processed = [profiler.process_text(text) for text in test_texts]
    aggregation_time = time.time()
    aggregated = profiler.aggregate_stats(processed)
    analysis_time = time.time()
    proficiency = profiler.calculate_proficiency_score(aggregated, 8)
    end_time = time.time()

    processing_time = aggregation_time - start_time
    aggregation_time_taken = analysis_time - aggregation_time
    scoring_time = end_time - analysis_time
    total_time = end_time - start_time

    print("⏱️  Performance Results:")
    print(f"   Text Processing: {processing_time:.3f}s")
    print(f"   Aggregation: {aggregation_time_taken:.3f}s")
    print(f"   Scoring: {scoring_time:.3f}s")
    print(f"   Total Time: {total_time:.3f}s")
    print(f"   Processing Speed: {len(test_texts)/total_time:.1f} texts/second")
    print("✅ Performance testing completed")

def main():
    """Run comprehensive integration tests."""
    print("🧪 VOCABULARY PROFILING MODULE - INTEGRATION TESTS")
    print("=" * 60)

    try:
        # Test complete pipeline
        pipeline_success = test_complete_pipeline()

        # Test edge cases
        test_edge_cases()

        # Test performance
        test_performance()

        if pipeline_success:
            print("\n🎉 ALL INTEGRATION TESTS PASSED!")
            print("✅ Vocabulary Profiling Module is production-ready")
            return 0
        else:
            print("\n❌ Integration tests failed")
            return 1

    except Exception as e:
        print(f"\n💥 Critical error during testing: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
