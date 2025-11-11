# Recommendation Engine Data Model Design

## Overview
This document defines the data model for the personalized vocabulary recommendation engine. The model supports the hybrid content-knowledge based recommendation algorithm and enables efficient querying, storage, and retrieval of recommendation data.

## Current DynamoDB Schema Analysis

### Existing Tables

#### 1. `vocabulary_profiles` Table
**Primary Key:** `student_id` (HASH), `report_date` (RANGE)

**Current Attributes:**
```json
{
  "student_id": "S001",
  "report_date": "2025-11-11T10:30:00Z",
  "grade_level": 7,
  "vocabulary_analysis": "{\"total_tokens\": 245, \"unique_words\": 89, ...}",
  "sample_count": 5,
  "total_words": 245,
  "unique_words": 89,
  "vocabulary_richness": 0.363,
  "created_at": "2025-11-11T10:30:00Z"
}
```

**Usage:** Stores aggregated linguistic analysis results per student per report date.

#### 2. `vocabulary_recommendations` Table
**Primary Key:** `student_id` (HASH), `recommendation_date` (RANGE)

**Current Attributes:** (based on Lambda code)
```json
{
  "student_id": "S001",
  "recommendation_date": "2025-11-11T10:30:00Z",
  "word": "analyze",
  "definition": "To examine something in detail",
  "context": "Scientists analyze data to find patterns",
  "grade_level": 7,
  "frequency_score": 0.85,
  "academic_utility": "high",
  "recommendation_id": "S001_0"
}
```

**Usage:** Stores individual vocabulary recommendations per student per recommendation date.

## Enhanced Data Model for Recommendations

### New Global Secondary Indexes (GSI)

#### GSI 1: `recommendations_by_grade`
- **Partition Key:** `grade_level` (Number)
- **Sort Key:** `recommendation_date` (String)
- **Projection:** ALL
- **Purpose:** Query recommendations by grade level for batch processing

#### GSI 2: `recommendations_by_word`
- **Partition Key:** `word` (String)
- **Sort Key:** `recommendation_date` (String)
- **Projection:** KEYS_ONLY
- **Purpose:** Track word recommendation frequency and patterns

#### GSI 3: `recommendations_by_utility`
- **Partition Key:** `academic_utility` (String)
- **Sort Key:** `frequency_score` (Number)
- **Projection:** INCLUDE (student_id, grade_level, word)
- **Purpose:** Analyze recommendation effectiveness by utility category

### Enhanced Recommendation Schema

```json
{
  "student_id": "S001",
  "recommendation_date": "2025-11-11T10:30:00Z",
  "recommendation_id": "S001_0",

  // Word Information
  "word": "analyze",
  "definition": "To examine something in detail to understand its nature",
  "part_of_speech": "verb",
  "phonetic": "/ˈæn.əl.aɪz/",
  "syllables": 3,

  // Contextual Information
  "context": "Scientists analyze data to find patterns.",
  "example_sentences": [
    "The researcher will analyze the survey results.",
    "Students learn to analyze complex problems."
  ],

  // Scoring and Classification
  "grade_level": 7,
  "frequency_score": 0.85,
  "academic_utility": "high",
  "word_complexity": "intermediate",
  "common_core_standard": "CCSS.ELA-Literacy.L.7.6",

  // Recommendation Algorithm Scores
  "gap_relevance_score": 0.92,
  "grade_appropriateness_score": 0.88,
  "academic_frequency_score": 0.85,
  "contextual_fit_score": 0.76,
  "pronunciation_ease_score": 0.82,
  "total_algorithm_score": 0.87,

  // Recommendation Metadata
  "algorithm_version": "1.0",
  "recommendation_rank": 1,
  "recommendation_category": "academic_vocabulary",
  "learning_objectives": ["vocabulary_expansion", "academic_language"],

  // Student Context
  "student_proficiency_level": "developing",
  "vocabulary_gap_area": "academic_words",
  "recommended_difficulty_progression": "maintain_current",

  // Tracking and Analytics
  "is_viewed": false,
  "is_practiced": false,
  "practice_attempts": 0,
  "mastery_score": null,
  "feedback_rating": null,
  "created_at": "2025-11-11T10:30:00Z",
  "expires_at": "2026-11-11T10:30:00Z"
}
```

### New Table: `recommendation_analytics`

**Purpose:** Track recommendation effectiveness and system performance metrics.

**Primary Key:** `analytics_date` (HASH), `metric_type` (RANGE)

```json
{
  "analytics_date": "2025-11-11",
  "metric_type": "student_engagement",

  // Student-level metrics
  "total_students_processed": 150,
  "avg_recommendations_per_student": 9.7,
  "recommendation_acceptance_rate": 0.68,

  // Word-level metrics
  "top_performing_words": [
    {"word": "analyze", "success_rate": 0.89, "avg_mastery_time": 3.2},
    {"word": "evaluate", "success_rate": 0.87, "avg_mastery_time": 2.8}
  ],

  // Algorithm performance
  "avg_processing_time_ms": 245,
  "recommendation_quality_score": 0.82,
  "grade_appropriateness_accuracy": 0.91,

  // System metrics
  "error_rate": 0.02,
  "cache_hit_rate": 0.94,
  "data_freshness_hours": 2.5
}
```

### New Table: `word_mastery_tracking`

**Purpose:** Track individual student progress on recommended words.

**Primary Key:** `student_id` (HASH), `word` (RANGE)

**GSI:** `mastery_by_date` (date HASH, mastery_level RANGE)

```json
{
  "student_id": "S001",
  "word": "analyze",

  // Mastery tracking
  "first_recommended_date": "2025-11-11T10:30:00Z",
  "mastery_level": "mastered",
  "mastery_score": 0.92,
  "mastery_date": "2025-11-15T14:20:00Z",

  // Practice history
  "practice_sessions": 5,
  "total_attempts": 23,
  "correct_attempts": 21,
  "avg_response_time_sec": 4.2,

  // Contextual usage
  "times_used_in_writing": 3,
  "successful_contexts": [
    "The scientist will analyze the data carefully.",
    "Students should analyze the problem before solving it."
  ],

  // Recommendation history
  "recommendation_count": 2,
  "last_recommended_date": "2025-11-11T10:30:00Z",
  "recommendation_reasons": ["vocabulary_gap", "academic_utility"]
}
```

## Data Flow Architecture

### 1. Recommendation Generation Flow
```
Student Text → Linguistic Analysis → Gap Identification → 
Recommendation Scoring → Personalized Selection → Storage
```

### 2. Query Patterns Supported

#### Student-Centric Queries:
- Get all recommendations for a student: `student_id = "S001"`
- Get recommendations by date range: `student_id = "S001" AND recommendation_date BETWEEN ...`
- Get recommendations by category: Filter by `recommendation_category`

#### Word-Centric Queries:
- Get recommendation frequency by word: GSI `recommendations_by_word`
- Get words by academic utility: GSI `recommendations_by_utility`
- Get grade-appropriate words: GSI `recommendations_by_grade`

#### Analytics Queries:
- Get system performance metrics: Query `recommendation_analytics`
- Track student mastery progress: Query `word_mastery_tracking`
- Analyze recommendation effectiveness: Aggregate queries on recommendation tables

### 3. Data Consistency and Integrity

#### Validation Rules:
- `recommendation_id` must be unique per student per recommendation date
- `grade_level` must be between 6-8
- `total_algorithm_score` must be between 0-1
- `academic_utility` must be one of: "low", "medium", "high"
- `recommendation_rank` must be between 1-10

#### Referential Integrity:
- All `student_id` values must exist in `vocabulary_profiles` table
- `recommendation_date` should align with corresponding profile `report_date`
- Word definitions must match reference data

## Implementation Plan

### Phase 1: Enhanced Existing Tables
1. Add Global Secondary Indexes to `vocabulary_recommendations`
2. Expand recommendation schema with algorithm scores
3. Add metadata fields for tracking

### Phase 2: New Analytics Table
1. Create `recommendation_analytics` table
2. Implement daily aggregation jobs
3. Add performance monitoring queries

### Phase 3: Mastery Tracking
1. Create `word_mastery_tracking` table
2. Implement progress update mechanisms
3. Add learning analytics features

## Migration Strategy

### Backward Compatibility:
- Existing recommendation records remain functional
- New fields are optional during transition
- Gradual rollout with feature flags

### Data Migration:
- Add new attributes to existing items
- Populate algorithm scores for historical recommendations
- Create analytics records from existing data

## Performance Considerations

### Read Optimization:
- GSI for common query patterns
- Attribute projection to minimize data transfer
- Query result caching for frequently accessed data

### Write Optimization:
- Batch writes for bulk recommendation generation
- Conditional writes to prevent duplicates
- Time-based partitioning for analytics data

### Cost Optimization:
- Pay-per-request billing for variable workloads
- Point-in-time recovery for data protection
- Automated cleanup of expired recommendations

This enhanced data model provides the foundation for a robust, scalable recommendation engine that can deliver personalized vocabulary learning experiences while maintaining high performance and analytical capabilities.
