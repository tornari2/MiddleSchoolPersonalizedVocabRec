#!/usr/bin/env python3
"""
Synthetic Data Generator for Vocabulary Recommendation Engine

This script generates realistic synthetic student data including:
- Writing assignments (essays, paragraphs)
- Conversational samples (dialogues)
- Grade-appropriate vocabulary usage
- Controlled vocabulary sophistication levels

Usage:
    python data_generator.py --output-dir synthetic_data --num-students 20
"""

import json
import random
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass

from reference_data_loader import ReferenceDataLoader

logger = logging.getLogger(__name__)

@dataclass
class StudentProfile:
    """Represents a student's profile for data generation."""
    student_id: str
    grade: int
    name: str
    writing_skill: float  # 0.0 to 1.0 (controls vocabulary sophistication)

class SyntheticDataGenerator:
    """Generates synthetic student data for the vocabulary recommendation system."""

    def __init__(self, seed: int = 42):
        """
        Initialize the data generator.

        Args:
            seed: Random seed for reproducible generation
        """
        random.seed(seed)
        self.data_loader = ReferenceDataLoader()

        # Load templates
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Any]:
        """Load writing and conversation templates."""
        return {
            "writing": {
                "essay": [
                    "The Importance of {topic} in Modern Society",
                    "Understanding {topic}: A Comprehensive Analysis",
                    "The Impact of {topic} on Our Daily Lives",
                    "Exploring {topic} and Its Significance",
                    "{topic}: Challenges and Opportunities"
                ],
                "paragraph": [
                    "{topic} plays a crucial role in our understanding of {related_concept}. {explanation} Furthermore, {additional_point} makes {topic} even more significant. In conclusion, {summary_point}.",
                    "When examining {topic}, we can see that {observation}. This {relationship} demonstrates how {topic} {effect} on {affected_area}. Ultimately, {conclusion}.",
                    "{topic} represents {definition}. Through {process}, we can observe {outcome}. This {connection} shows the importance of {topic} in {context}."
                ]
            },
            "conversation": {
                "dialogue": [
                    "Student A: What do you think about {topic}? Student B: I believe {opinion}. What about you? Student A: Well, {counterpoint}. Student B: That's interesting because {explanation}.",
                    "Student A: Have you ever thought about {topic}? Student B: Yes, and I think {viewpoint}. Student A: Really? I feel that {alternative_view}. Student B: Why do you say that? Student A: Because {reasoning}."
                ]
            },
            "topics": {
                "science": ["biodiversity", "climate change", "ecosystems", "renewable energy", "sustainable development"],
                "social_studies": ["democracy", "cultural diversity", "economic systems", "historical events", "community involvement"],
                "literature": ["character development", "narrative structure", "poetic devices", "theme analysis", "author's purpose"],
                "general": ["technology", "environment", "education", "communication", "creativity"]
            }
        }

    def generate_student_profiles(self, num_students: int, grade_distribution: Dict[int, int]) -> List[StudentProfile]:
        """
        Generate student profiles with appropriate grade levels and skill levels.

        Args:
            num_students: Total number of students to generate
            grade_distribution: Dict mapping grade levels to number of students

        Returns:
            List of StudentProfile objects
        """
        students = []
        student_id = 1

        for grade, count in grade_distribution.items():
            for i in range(count):
                # Generate realistic skill levels with some variation
                base_skill = 0.4 + (grade - 6) * 0.15  # Grade 6: 0.4, Grade 7: 0.55, Grade 8: 0.7
                skill_variation = random.uniform(-0.15, 0.15)
                writing_skill = max(0.2, min(0.9, base_skill + skill_variation))

                profile = StudentProfile(
                    student_id=f"S{student_id:03d}",
                    grade=grade,
                    name=f"Student_{student_id}",
                    writing_skill=writing_skill
                )

                students.append(profile)
                student_id += 1

        return students

    def select_vocabulary(self, grade: int, skill_level: float, num_words: int = 20) -> List[str]:
        """
        Select appropriate vocabulary words for a student.

        Args:
            grade: Student's grade level
            skill_level: Writing skill level (0.0 to 1.0)
            num_words: Number of words to select

        Returns:
            List of selected vocabulary words
        """
        # Get grade-appropriate words
        grade_words = self.data_loader.get_all_grade_words(grade)

        # Select basic vs advanced based on skill level
        basic_words = grade_words['basic']
        advanced_words = grade_words['advanced']

        # Determine mix based on skill level
        advanced_ratio = min(0.7, skill_level * 1.2)  # Max 70% advanced words
        basic_ratio = 1 - advanced_ratio

        num_advanced = int(num_words * advanced_ratio)
        num_basic = num_words - num_advanced

        # Select words
        selected_words = []
        selected_words.extend(random.sample(basic_words, min(num_basic, len(basic_words))))
        selected_words.extend(random.sample(advanced_words, min(num_advanced, len(advanced_words))))

        # Fill remaining slots if needed
        all_words = basic_words + advanced_words
        remaining = num_words - len(selected_words)
        if remaining > 0:
            available_words = [w for w in all_words if w not in selected_words]
            selected_words.extend(random.sample(available_words, min(remaining, len(available_words))))

        return selected_words

    def generate_writing_sample(self, student: StudentProfile, sample_type: str) -> Dict[str, Any]:
        """
        Generate a single writing sample for a student.

        Args:
            student: StudentProfile object
            sample_type: Type of writing ("essay" or "paragraph")

        Returns:
            Dictionary containing the generated sample
        """
        # Select topic
        topic_category = random.choice(list(self.templates["topics"].keys()))
        topic = random.choice(self.templates["topics"][topic_category])

        # Select template
        template = random.choice(self.templates["writing"][sample_type])

        # Generate vocabulary for this sample
        vocab_words = self.select_vocabulary(student.grade, student.writing_skill, 8)

        # Fill template with content
        content = self._fill_template(template, {
            "topic": topic,
            "related_concept": random.choice(["science", "society", "technology", "nature"]),
            "explanation": f"it helps us understand complex {random.choice(['systems', 'processes', 'relationships', 'patterns'])}",
            "additional_point": f"research shows that {vocab_words[0]} is becoming increasingly important",
            "summary_point": f"{vocab_words[1]} will continue to shape our future",
            "observation": f"many experts believe {vocab_words[2]} is essential",
            "relationship": random.choice(["connection", "relationship", "interaction"]),
            "effect": random.choice(["influences", "affects", "transforms"]),
            "affected_area": random.choice(["education", "society", "the environment"]),
            "conclusion": f"this highlights the importance of {vocab_words[3]}",
            "definition": f"an essential concept involving {vocab_words[4]}",
            "process": random.choice(["careful analysis", "systematic study", "detailed examination"]),
            "outcome": f"significant {random.choice(['improvements', 'developments', 'advances'])}",
            "connection": random.choice(["relationship", "link", "connection"]),
            "context": random.choice(["modern society", "educational settings", "scientific research"])
        })

        # Generate timestamp (simulate over a few months)
        base_date = datetime(2024, 9, 1)  # Start of school year
        days_offset = random.randint(0, 120)  # Up to 4 months
        timestamp = (base_date + timedelta(days=days_offset)).isoformat()

        return {
            "student_id": student.student_id,
            "grade_level": student.grade,
            "timestamp": timestamp,
            "assignment_type": f"written_{sample_type}",
            "text": content,
            "vocabulary_focus": vocab_words[:3],  # Track which vocab words were used
            "generated_at": datetime.now().isoformat()
        }

    def generate_conversation_sample(self, student: StudentProfile) -> Dict[str, Any]:
        """
        Generate a conversation sample for a student.

        Args:
            student: StudentProfile object

        Returns:
            Dictionary containing the generated conversation
        """
        # Select topic
        topic_category = random.choice(list(self.templates["topics"].keys()))
        topic = random.choice(self.templates["topics"][topic_category])

        # Select template
        template = random.choice(self.templates["conversation"]["dialogue"])

        # Generate vocabulary for this sample (fewer words for conversation)
        vocab_words = self.select_vocabulary(student.grade, student.writing_skill, 5)

        # Fill template
        content = self._fill_template(template, {
            "topic": topic,
            "opinion": f"{vocab_words[0]} is really important for understanding {random.choice(['the world', 'our society', 'modern life'])}",
            "counterpoint": f"I think {vocab_words[1]} might be even more crucial",
            "explanation": f"it helps develop {random.choice(['critical thinking', 'better communication', 'deeper understanding'])}",
            "viewpoint": f"{vocab_words[2]} represents a key aspect of this issue",
            "alternative_view": f"actually, {vocab_words[3]} could have a bigger impact",
            "reasoning": f"research shows that {vocab_words[4]} leads to better outcomes"
        })

        # Generate timestamp
        base_date = datetime(2024, 9, 1)
        days_offset = random.randint(0, 120)
        timestamp = (base_date + timedelta(days=days_offset)).isoformat()

        return {
            "student_id": student.student_id,
            "grade_level": student.grade,
            "timestamp": timestamp,
            "assignment_type": "conversation",
            "text": content,
            "vocabulary_focus": vocab_words[:2],
            "generated_at": datetime.now().isoformat()
        }

    def _fill_template(self, template: str, replacements: Dict[str, str]) -> str:
        """
        Fill a template string with replacements.

        Args:
            template: Template string with {placeholders}
            replacements: Dictionary of placeholder -> replacement mappings

        Returns:
            Filled template string
        """
        result = template
        for key, value in replacements.items():
            result = result.replace(f"{{{key}}}", value)
        return result

    def generate_student_data(self, student: StudentProfile, writing_samples: int = 20,
                            conversation_samples: int = 10) -> List[Dict[str, Any]]:
        """
        Generate all data samples for a single student.

        Args:
            student: StudentProfile object
            writing_samples: Number of writing samples to generate
            conversation_samples: Number of conversation samples to generate

        Returns:
            List of data samples for the student
        """
        samples = []

        # Generate writing samples
        for i in range(writing_samples):
            # Alternate between essay and paragraph
            sample_type = "essay" if i % 3 == 0 else "paragraph"
            sample = self.generate_writing_sample(student, sample_type)
            samples.append(sample)

        # Generate conversation samples
        for i in range(conversation_samples):
            sample = self.generate_conversation_sample(student)
            samples.append(sample)

        # Sort by timestamp
        samples.sort(key=lambda x: x['timestamp'])

        return samples

    def generate_all_data(self, num_students: int = 20,
                         grade_distribution: Optional[Dict[int, int]] = None,
                         output_dir: str = "synthetic_data") -> str:
        """
        Generate synthetic data for all students.

        Args:
            num_students: Total number of students
            grade_distribution: Optional grade distribution override
            output_dir: Directory to save generated data

        Returns:
            Path to the output file
        """
        # Default grade distribution if not provided
        if grade_distribution is None:
            # Create balanced distribution for the requested number of students
            base_per_grade = num_students // 3
            remainder = num_students % 3
            grade_distribution = {
                6: base_per_grade + (1 if remainder > 0 else 0),
                7: base_per_grade + (1 if remainder > 1 else 0),
                8: base_per_grade
            }

        # Verify the distribution matches num_students
        total_in_distribution = sum(grade_distribution.values())
        if total_in_distribution != num_students:
            logger.warning(f"Grade distribution ({total_in_distribution} students) doesn't match num_students ({num_students}). Adjusting...")
            # Adjust the distribution to match
            diff = num_students - total_in_distribution
            if diff > 0:
                # Add to grade 7
                grade_distribution[7] += diff
            elif diff < 0:
                # Remove from grade 8
                grade_distribution[8] = max(0, grade_distribution[8] + diff)

        logger.info(f"Generating synthetic data for {num_students} students")
        logger.info(f"Grade distribution: {grade_distribution}")

        # Generate student profiles
        students = self.generate_student_profiles(num_students, grade_distribution)
        logger.info(f"Created {len(students)} student profiles")

        # Generate data for all students
        all_samples = []
        for student in students:
            logger.info(f"Generating data for {student.student_id} (Grade {student.grade})")
            student_samples = self.generate_student_data(student)
            all_samples.extend(student_samples)

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Save as JSONL file
        output_file = output_path / "student_text_samples.jsonl"
        with open(output_file, 'w', encoding='utf-8') as f:
            for sample in all_samples:
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')

        logger.info(f"Generated {len(all_samples)} total samples")
        logger.info(f"Saved to {output_file}")

        # Generate summary statistics
        self._generate_summary_stats(all_samples, output_path)

        return str(output_file)

    def _generate_summary_stats(self, samples: List[Dict[str, Any]], output_dir: Path):
        """Generate summary statistics of the generated data."""
        stats = {
            "total_samples": len(samples),
            "samples_by_type": {},
            "samples_by_grade": {},
            "vocabulary_usage": {},
            "generation_timestamp": datetime.now().isoformat()
        }

        for sample in samples:
            # Count by type
            sample_type = sample["assignment_type"]
            stats["samples_by_type"][sample_type] = stats["samples_by_type"].get(sample_type, 0) + 1

            # Count by grade
            grade = sample["grade_level"]
            stats["samples_by_grade"][grade] = stats["samples_by_grade"].get(grade, 0) + 1

            # Track vocabulary usage
            for word in sample.get("vocabulary_focus", []):
                stats["vocabulary_usage"][word] = stats["vocabulary_usage"].get(word, 0) + 1

        # Sort vocabulary by usage
        stats["vocabulary_usage"] = dict(sorted(
            stats["vocabulary_usage"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:20])  # Top 20 words

        # Save stats
        stats_file = output_dir / "generation_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        logger.info(f"Summary statistics saved to {stats_file}")

def main():
    """Main entry point for the data generator."""
    parser = argparse.ArgumentParser(description="Generate synthetic student data")
    parser.add_argument("--output-dir", default="synthetic_data",
                       help="Output directory for generated data")
    parser.add_argument("--num-students", type=int, default=20,
                       help="Number of students to generate data for")
    parser.add_argument("--seed", type=int, default=42,
                       help="Random seed for reproducible generation")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")

    args = parser.parse_args()

    # Set up logging
    level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')

    try:
        # Initialize generator
        generator = SyntheticDataGenerator(seed=args.seed)

        # Generate data
        output_file = generator.generate_all_data(
            num_students=args.num_students,
            output_dir=args.output_dir
        )

        print("✅ Synthetic data generation completed!")
        print(f"📁 Output saved to: {args.output_dir}")
        print(f"📄 Main data file: {output_file}")

        # Show quick stats
        stats_file = Path(args.output_dir) / "generation_stats.json"
        if stats_file.exists():
            with open(stats_file, 'r') as f:
                stats = json.load(f)
            print("\n📊 Quick Stats:")
        print(f"   • Total samples: {stats['total_samples']}")
        print(f"   • Samples by grade: {stats['samples_by_grade']}")
        print(f"   • Samples by type: {stats['samples_by_type']}")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
