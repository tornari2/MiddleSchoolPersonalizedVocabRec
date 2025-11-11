# Personalized Vocabulary Recommendation Engine - MVP Implementation PRD (Refined for TaskMaster)

**Organization:** Flourish Schools  
**Project ID:** JnGyV0Xlx2AEiL31nu7J_1761523676397  
**Document Version:** 3.1 (TaskMaster-Ready)  
**Target Delivery:** ASAP  
**Primary Language:** Python  
**Deployment:** AWS (Serverless)

---

## 1. Executive Summary

This MVP implements the core P0 functionality of the **Personalized Vocabulary Recommendation Engine** — a backend system that processes student text samples, builds vocabulary profiles, and generates personalized, grade-aligned vocabulary recommendations for middle school students (grades 6–8).

**MVP Scope:** Backend engine + JSON output (dashboard-ready) for a single educator testing environment.

**Functional Summary:**
- Input: JSONL text data per student
- Output: JSON vocabulary profiles + recommendations
- Core components: Data ingestion → Vocabulary profiling → Gap analysis → Recommendations → Reports

---

## 2. System Overview

### 2.1 Architecture Summary

**Core Components:**
1. **Data Ingestion Service** — Processes daily batches of student text data from S3.
2. **Vocabulary Analysis Engine** — Extracts linguistic features and builds student profiles.
3. **Recommendation Engine** — Identifies vocabulary gaps and suggests new words.
4. **Data Storage Layer** — DynamoDB tables for profiles and recommendations.
5. **Authentication Layer** — AWS Cognito for a single educator login.

**Taskmaster Hint:**  
Break these as five atomic modules (DataIngestion, VocabAnalysis, Recommendation, DataStorage, Auth). Each module has its own Lambda or callable function.

### 2.2 Simplified AWS Logical Architecture
```
S3 (raw text JSONL)
  ↓ trigger
Lambda (ingestion)
  ↓ async fan-out
Step Function → Lambda (per student processor)
  ↓
DynamoDB (profiles & recommendations)
  ↓
Lambda (report generator)
  ↓
S3 (output reports)
```

### 2.3 Performance Targets
- Process 20 students × 30 samples (<5 minutes)
- Fully serverless (no EC2)
- Parallelized via Lambda fan-out pattern
- Reference data preloaded and cached

---

## 3. Data Specification

**Input Format (JSONL):**
```json
{
  "student_id": "S001",
  "grade_level": 7,
  "timestamp": "2025-11-10T09:15:00Z",
  "assignment_type": "written_assignment",
  "text": "The ecosystem in our local park demonstrates biodiversity..."
}
```

**Output Format:** Student and batch JSON reports (dashboard-ready).  
See section 7 for schemas.

**Taskmaster Hint:**  
Ensure schema validation (pydantic) at both input and output stages.

---

## 4. Synthetic Data Generation (Simplified)

**Purpose:** Generate reproducible synthetic datasets for local and AWS testing.

**Approach:**
- Use LLM (Claude or GPT) *or* local template-based generator (`USE_LLM=True/False` flag).
- Generate 20 students × 30 samples (20 writing, 10 conversations).
- Vocabulary control via grade-level lists.

**Dependencies:** `reference_data/grade_level_words.json`, `reference_data/word_frequencies.json`

---

## 5. Vocabulary Profiling System

### Section Summary
- **Input:** Student text samples
- **Output:** Student vocabulary profile JSON
- **Dependencies:** spaCy model, reference data (grade words + frequency lists)

**Modules:**
1. `Preprocessor` — Cleans text
2. `LinguisticAnalyzer` — POS tagging, lemmatization
3. `Profiler` — Aggregates vocabulary metrics + proficiency scoring

**Simplification:** Use only spaCy (`en_core_web_lg`); remove NLTK dependency.

**Proficiency Formula:**
```
Score = (Grade_Level_Score * 0.6) + (Sophistication_Score * 0.4)
```

**Taskmaster Hint:**  
Implement as a single module `vocab_analysis.py` with functions: `process_text`, `aggregate_stats`, `calculate_proficiency_score`, and `save_profile`.

---

## 6. Recommendation Engine

### Section Summary
- **Input:** Student vocabulary profile
- **Output:** 10 personalized vocabulary recommendations
- **Dependencies:** Reference data (definitions, grade lists)

**Algorithm (Simplified):**
1. Identify gap words (unused grade+1 words)
2. Score words by frequency, context, and academic utility
3. Select top 10, enrich with definition, example, context

**Simplification:**  
Run profiling + recommendation sequentially in same Lambda to reduce orchestration.

**Taskmaster Hint:**  
Single function `generate_recommendations(student_id)` → saves results to `VocabularyRecommendations` table.

---

## 7. Output Specification

### 7.1 Student Report
```json
{
  "student_id": "S001",
  "report_date": "2025-11-10",
  "proficiency_score": 58.3,
  "recommendations": [{"word": "analyze", "definition": "To examine..."}]
}
```

**Validation:** Enforce schema with pydantic model `StudentReportSchema`.

### 7.2 Batch Summary
Aggregated class-level report with averages and file references.

**Taskmaster Hint:**  
Create `generate_reports.py` → merges student data → validates with schema → writes to S3.

---

## 8. Reference Data Requirements

**Preloaded Files:**
1. `grade_level_words.json`  
2. `word_frequencies.json`  
3. `word_definitions.json`

**Optimization:** Load and cache at Lambda cold start. Avoid reloading per invocation.

---

## 9. Authentication & Access

- **Cognito** single educator login (username/password)
- No MFA or granular permissions for MVP
- Token-based access to report files (S3 signed URLs)

**Taskmaster Hint:**  
Implement `setup_auth.py` with Cognito SDK integration for login + JWT verification.

---

## 10. Implementation Phases (Revised)

| Phase | Description | Dependencies | Duration |
|--------|--------------|---------------|-----------|
| 1 | Infrastructure setup (S3, DynamoDB, Lambda, Cognito) | AWS account | Week 1 |
| 2 | Synthetic data + reference data generation | Phase 1 | Week 1 |
| 3 | Vocabulary profiling module | Phase 2 | Week 2 |
| 4 | Recommendation engine | Phase 3 | Week 3 |
| 5 | Reporting + Authentication | Phase 4 | Week 4 |
| 6 | End-to-end testing + validation | All prior | Week 5 |

**Success Metric:** Full daily pipeline (20 students × 30 texts) completes in <5 minutes.

---

## 11. Taskmaster Integration Hints

**Atomic Tasks to Generate:**
1. Setup AWS infra (Terraform optional)
2. Create reference data and synthetic data generator
3. Implement vocab analysis engine
4. Implement recommendation engine
5. Implement reporting
6. Add Cognito authentication
7. Test E2E with 600 samples

**Completion Signals:**
- Profiles written to DynamoDB
- Recommendations generated per student
- Reports stored in S3
- Logs show “Batch completed successfully”

---

## 12. Simplified Deployment Plan

**Infrastructure:** AWS Lambda + DynamoDB + S3 + Cognito + Step Functions.

**Config Variables:**
```
AWS_REGION = "us-east-1"
DAILY_PROCESSING_HOUR = 6  # 6 AM UTC
STUDENT_COUNT = 20
USE_LLM = False
```

**Deployment Flow:**
1. Package Lambda functions (Zip + deploy)
2. Create DynamoDB tables using AWS CLI
3. Configure Step Function orchestration
4. Run `trigger_daily_processing()` manually for validation

---

## 13. Success & Quality Criteria

- ✅ Vocabulary profiles generated per student
- ✅ 10 high-quality recommendations daily
- ✅ Processing time <5 min
- ✅ Reports valid against schema
- ✅ Serverless architecture, scalable to 100 students

---

## 14. Non-Functional Requirements Compliance

### ⚡ Performance
- AWS Lambda supports high concurrency (thousands of parallel executions).
- Step Functions manage fan-out/fan-in orchestration.
- spaCy model preloaded in Lambda layer for low latency.
- DynamoDB and S3 provide sub-second I/O.
- **Meets**: Handles full-day classroom data (600+ documents) in <5 minutes.

### 📈 Scalability
- Fully serverless stack (Lambda, DynamoDB, S3) scales horizontally.
- No server management required.
- Partitioning by `student_id` ensures distributed load.
- **Meets**: Scales to 100+ students seamlessly.

### 🔒 Security
- AWS Cognito manages authentication and JWT-based access.
- S3 and DynamoDB encrypt data at rest (AES-256) and in transit (TLS).
- IAM policies enforce least-privilege access per service.
- CloudTrail + CloudWatch provide audit logging.
- FERPA-ready architecture (no PII in synthetic data).
- **Meets**: Educational data protection and compliance.

---

## 15. Future Enhancements (Post-MVP)

| Tier | Feature | Summary |
|------|----------|----------|
| 🚀 P1 | Web dashboard | Visualize profiles and recommendations |
| 🚀 P1 | REST API | External platform integration |
| 💡 P2 | Gamified vocab practice | Flashcards, quizzes |
| 💡 P2 | LTI integration | Connect to LMS platforms |

---

## 16. Final Notes

This PRD is optimized for **TaskMaster automation**. Each core function is modular, self-contained, and verifiable by automated tests. TaskMaster can parallelize these as distinct subtasks with defined dependencies and completion conditions.

