# Middle School Personalized Vocabulary Recommendation Engine

## Overview

This system provides personalized vocabulary recommendations for middle school students (grades 6-8) based on their writing samples. The system analyzes student text using natural language processing techniques and generates targeted vocabulary recommendations to improve academic writing skills.

The engine processes student writing samples, builds detailed vocabulary profiles, identifies gaps in academic vocabulary usage, and recommends grade-appropriate words that will most benefit each student's linguistic development.

## Table of Contents
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Sample Data Generation](#sample-data-generation)
- [Vocabulary Gap Identification](#vocabulary-gap-identification)
- [Vocabulary Recommendation](#vocabulary-recommendation)
- [Core Features](#core-features)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)

## Architecture

### System Architecture

The vocabulary recommendation engine follows a modular, serverless architecture designed for scalability and maintainability.

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Student Text  │ -> │  Data Ingestion  │ -> │ Vocabulary       │
│     Samples     │    │    Service       │    │ Profiling Engine │
│   (JSONL/S3)    │    │   (AWS Lambda)   │    │  (spaCy + NLP)   │
└─────────────────┘    └──────────────────┘    └──────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ Vocabulary Gap  │ -> │ Recommendation   │ -> │  Report          │
│  Identification │    │    Engine        │    │  Generation      │
│  (Gap Analysis) │    │ (Hybrid Algorithm)│    │  (JSON Output)   │
└─────────────────┘    └──────────────────┘    └──────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   DynamoDB      │    │   CloudWatch     │    │   Web Dashboard  │
│   Storage       │    │   Monitoring     │    │   (Optional)     │
│ (Profiles & Recs)│    │   & Alarms      │    │                  │
└─────────────────┘    └──────────────────┘    └──────────────────┘
```

### Core Components

#### 1. Data Ingestion Service
- **Purpose**: Processes student text data uploaded to S3
- **Trigger**: S3 object creation events (JSONL files)
- **Function**: Reads JSONL files, groups data by student, and initiates vocabulary analysis
- **Technology**: AWS Lambda (Python 3.9, 512MB, 5min timeout)

#### 2. Vocabulary Profiling Engine
- **Purpose**: Analyzes student text using spaCy NLP library
- **Functions**:
  - `process_text()`: Tokenization and preprocessing
  - `aggregate_stats()`: Linguistic feature extraction
  - `calculate_proficiency_score()`: Vocabulary proficiency assessment
- **Output**: Detailed linguistic analysis and proficiency metrics

#### 3. Recommendation Engine
- **Purpose**: Generates personalized vocabulary recommendations
- **Algorithm**: Hybrid content-knowledge based approach
- **Components**: Gap analysis, candidate selection, scoring, ranking
- **Output**: Top 10 vocabulary words per student with definitions and contexts
- **Technology**: AWS Lambda (Python 3.9, 1024MB, 10min timeout)

#### 4. Report Generation Service
- **Purpose**: Compiles student data and generates structured reports
- **Output**: JSON reports stored in S3 with schema validation
- **Technology**: AWS Lambda (Python 3.9, 1024MB, 10min timeout)

### Data Flow Architecture

```
Input Data (S3)
    ↓
Data Ingestion Lambda
    ↓
Step Functions Orchestrator
    ↓
Vocabulary Analysis (per student)
    ↓
Recommendation Generation
    ↓
Report Compilation
    ↓
Output Reports (S3) + Profiles (DynamoDB)
```

### Storage Architecture

#### S3 Buckets:
- `vocab-rec-engine-input-data-prod`: Student text data (JSONL files)
- `vocab-rec-engine-output-reports-prod`: Generated reports and analytics

#### DynamoDB Tables:
- `vocabulary-profiles-prod`: Student vocabulary analysis results
- `vocabulary-recommendations-prod`: Generated recommendations with metadata
- `recommendation-analytics-prod`: System performance analytics

### Security Architecture

#### Authentication:
- AWS Cognito User Pools for educator authentication
- JWT tokens for API access
- IAM roles with least-privilege access

#### Data Protection:
- Encryption at rest (S3 SSE-KMS, DynamoDB encryption)
- Encryption in transit (HTTPS/TLS)
- VPC isolation for Lambda functions

## Technology Stack

### Backend & Infrastructure
- **Runtime**: Python 3.9
- **Cloud Platform**: AWS (Serverless Architecture)
- **Compute**: AWS Lambda Functions
- **Storage**: Amazon S3, Amazon DynamoDB
- **Orchestration**: AWS Step Functions
- **Authentication**: AWS Cognito
- **Monitoring**: Amazon CloudWatch

### NLP & Data Processing
- **NLP Engine**: spaCy with `en_core_web_sm` model
- **Data Validation**: Pydantic schemas
- **Configuration Management**: Python dictionaries/JSON
- **Logging**: Python logging module

### Development Tools
- **Package Management**: pip, requirements.txt
- **Infrastructure as Code**: Terraform
- **Local Development**: Python HTTP server for dashboard testing
- **Testing**: pytest framework (previously used)

### Key Dependencies
```
spacy==3.7.2
pydantic==2.5.0
boto3==1.34.0
requests==2.31.0
openai==1.0.0 (optional enhancement)
```

## Sample Data Generation

### Overview
The system generates synthetic student writing samples to simulate real classroom data for testing and demonstration. Sample data includes various writing types and difficulty levels appropriate for middle school students.

### Data Structure
Each sample follows this JSON schema:
```json
{
  "student_id": "S001",
  "grade_level": 7,
  "timestamp": "2024-09-05T00:00:00",
  "assignment_type": "conversation|written_essay|written_paragraph",
  "text": "Student writing sample text...",
  "vocabulary_focus": ["word1", "word2"],
  "generated_at": "2025-11-10T23:16:00.346841"
}
```

### Generation Statistics
- **Total Samples**: 600 writing samples
- **Students**: 20 unique students (S001-S020)
- **Grade Distribution**: 210 samples each for grades 6-7, 180 for grade 8
- **Assignment Types**:
  - Conversations: 200 samples
  - Written Essays: 140 samples
  - Written Paragraphs: 260 samples

### Vocabulary Integration
Samples incorporate academic vocabulary words from the AWL (Academic Word List) and grade-appropriate word lists. The system tracks vocabulary usage patterns to ensure realistic distributions across different writing contexts.

### Quality Assurance
- **Lexical Diversity**: Varies by grade level and assignment type
- **Academic Word Integration**: 8-15% academic vocabulary usage
- **Sentence Complexity**: Grade-appropriate sentence structures
- **Contextual Appropriateness**: Writing samples reflect authentic student work

## Vocabulary Gap Identification

### Overview
The vocabulary gap identification process analyzes student writing samples to determine areas where academic vocabulary usage could be improved. This involves comparing student language patterns against grade-appropriate expectations and academic standards.

### Analysis Components

#### 1. Linguistic Feature Extraction
The system analyzes multiple linguistic dimensions:
- **Vocabulary Diversity**: Ratio of unique words to total words
- **Academic Word Usage**: Percentage of AWL (Academic Word List) words
- **Sentence Complexity**: Average sentence length and structure
- **Grammatical Range**: Balance of nouns, verbs, adjectives, adverbs
- **Lexical Density**: Content words vs. function words

#### 2. Proficiency Assessment
Each student receives a comprehensive proficiency score based on:
```
Overall Score = (
  Vocabulary_Diversity × 0.30 +
  Academic_Word_Usage × 0.25 +
  Sentence_Complexity × 0.20 +
  Grammatical_Range × 0.15 +
  Lexical_Density × 0.10
)
```

#### 3. Grade-Level Expectations
The system uses grade-appropriate benchmarks:
- **Grade 6**: Target score 0.5, Advanced threshold 0.7
- **Grade 7**: Target score 0.6, Advanced threshold 0.8
- **Grade 8**: Target score 0.7, Advanced threshold 0.9

### Gap Identification Process

#### Step 1: Current Proficiency Analysis
- Analyze student's writing samples
- Calculate linguistic metrics
- Determine current proficiency level

#### Step 2: Gap Area Identification
The system identifies specific areas needing improvement:
- **Academic Vocabulary**: Low AWL word usage
- **Vocabulary Diversity**: Limited word variety
- **Sentence Complexity**: Simple sentence structures
- **Content Focus**: Too many function words, not enough content words

#### Step 3: Gap Quantification
Each gap area receives a priority score:
- **High Priority**: Academic vocabulary gaps
- **Medium Priority**: Vocabulary diversity issues
- **Low Priority**: Minor grammatical range imbalances

### Output Structure
Gap analysis produces:
```json
{
  "vocabulary_gaps": {
    "academic_words": "low",
    "vocabulary_diversity": "medium",
    "sentence_complexity": "high"
  },
  "gap_priority": ["sentence_complexity", "academic_words", "vocabulary_diversity"],
  "recommendation_focus": ["academic", "complexity", "diversity"]
}
```

## Vocabulary Recommendation

### Overview
The recommendation engine uses a hybrid algorithm combining content-based analysis (student gaps) with knowledge-based educational standards to generate personalized vocabulary recommendations.

### Recommendation Algorithm

#### 1. Hybrid Approach
- **Content-Based**: Analyzes student's specific writing patterns and gaps
- **Knowledge-Based**: Leverages educational standards and academic word lists
- **Grade-Appropriate**: Considers developmental stage and curriculum requirements

#### 2. Candidate Word Selection
The system selects words from a comprehensive vocabulary database:
- **Source**: 1,200+ grade-appropriate words (grades 6-8)
- **Categories**: Basic vocabulary, academic words, domain-specific terms
- **Grade Range**: ±1 grade level from student's current grade
- **Filtering**: Removes words already used by the student

#### 3. Multi-Factor Scoring System
Each candidate word receives scores across multiple dimensions:

```
Overall Score = (
  Gap_Relevance × 0.40 +
  Grade_Appropriateness × 0.25 +
  Academic_Utility × 0.20 +
  Contextual_Fit × 0.10 +
  Pronunciation_Ease × 0.05
)
```

##### Gap Relevance (40% weight)
- How well the word addresses identified student gaps
- Higher scores for words that fill academic vocabulary deficiencies

##### Grade Appropriateness (25% weight)
- Alignment with student's grade level expectations
- Considers curriculum standards and developmental readiness

##### Academic Utility (20% weight)
- Educational value and frequency in academic contexts
- Based on AWL (Academic Word List) classifications

##### Contextual Fit (10% weight)
- Semantic and contextual appropriateness
- Word relationships and usage patterns

##### Pronunciation Ease (5% weight)
- Phonetic complexity and learnability
- Considers syllable count and phonetic patterns

#### 4. Recommendation Generation Process

##### Step 1: Gap Analysis Integration
- Import identified vocabulary gaps
- Prioritize gap areas (academic → diversity → complexity)

##### Step 2: Candidate Pool Creation
- Query grade-appropriate vocabulary database
- Filter out already-used words
- Apply gap-specific selection criteria

##### Step 3: Scoring and Ranking
- Calculate multi-factor scores for each candidate
- Rank by overall recommendation score
- Select top 10 words per student

##### Step 4: Output Formatting
Generate structured recommendations:
```json
{
  "student_id": "S001",
  "recommendation_date": "2025-11-13T02:34:00",
  "word": "interpret",
  "definition": "To explain the meaning of something",
  "context": "Historians interpret events from the past.",
  "grade_level": 7,
  "frequency_score": 0.72,
  "academic_utility": "medium",
  "gap_addressed": "academic_vocabulary"
}
```

### Recommendation Categories

#### By Gap Type:
- **Academic Vocabulary**: Words from AWL for academic writing
- **Vocabulary Diversity**: Synonyms and varied expressions
- **Sentence Complexity**: Words enabling complex sentence structures
- **Content Focus**: Domain-specific vocabulary for subject areas

#### By Learning Priority:
- **High Impact**: Frequently used academic words
- **Foundation Building**: Basic vocabulary for grade level
- **Extension**: Advanced words for gifted students

### Quality Assurance

#### Validation Criteria:
- **Grade Appropriateness**: All recommendations within ±1 grade level
- **Gap Relevance**: Minimum 70% gap-relevance score
- **Diversity**: No more than 2 words from same semantic field
- **Utility**: Minimum medium academic utility rating

#### Performance Metrics:
- **Coverage**: Addresses 80%+ of identified gaps
- **Appropriateness**: 95%+ grade-appropriate recommendations
- **Utility**: 85%+ medium/high academic utility words

## Core Features

### 1. Automated Vocabulary Analysis
- **Real-time Processing**: Automatic analysis when student data is uploaded
- **Comprehensive Metrics**: 5-dimensional linguistic assessment
- **Grade Calibration**: Age-appropriate evaluation standards
- **Progress Tracking**: Longitudinal vocabulary development monitoring

### 2. Personalized Recommendations
- **Gap-Based Targeting**: Addresses specific student deficiencies
- **Grade-Appropriate Selection**: ±1 grade level vocabulary selection
- **Multi-Factor Scoring**: Holistic recommendation quality assessment
- **Contextual Examples**: Real-world usage demonstrations

### 3. Academic Word Integration
- **AWL Foundation**: Based on Academic Word List research
- **Cross-Disciplinary**: Applicable across subject areas
- **Curriculum Alignment**: Matches educational standards
- **Research-Backed**: Grounded in vocabulary acquisition studies

### 4. Scalable Architecture
- **Serverless Design**: Auto-scaling AWS Lambda functions
- **Event-Driven**: S3 triggers for immediate processing
- **Batch Processing**: Efficient handling of multiple students
- **Cost-Optimized**: Pay-per-use pricing model

### 5. Data Quality Assurance
- **Schema Validation**: Pydantic-based data integrity checks
- **Error Handling**: Robust exception management and logging
- **Quality Metrics**: Automated validation of recommendation quality
- **Audit Trail**: Complete processing history and metadata

### 6. Security & Compliance
- **Data Encryption**: End-to-end encryption at rest and in transit
- **Access Control**: Least-privilege IAM roles and policies
- **Authentication**: AWS Cognito integration for user management
- **Privacy Protection**: Student data anonymization and secure storage

### 7. Monitoring & Observability
- **CloudWatch Integration**: Real-time system monitoring
- **Performance Metrics**: Detailed execution time and resource usage
- **Error Alerting**: Automated notifications for system issues
- **Usage Analytics**: System utilization and performance reporting

### 8. Extensible Design
- **Modular Architecture**: Clean separation of concerns
- **API-Ready**: RESTful interface capabilities
- **Plugin Architecture**: Extensible recommendation algorithms
- **Configuration Management**: Environment-based settings

## Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- Python 3.9+ (for local development)
- Terraform 1.0+ (for infrastructure management)

### Local Development Setup
```bash
# Clone repository
git clone <repository-url>
cd WK5_MiddleSchoolPersonalizedVocabRec

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Start local dashboard (optional)
python3 -m http.server 8000
# Visit: http://localhost:8000/dashboard/
```

### Production Deployment
```bash
# Deploy infrastructure
cd infrastructure/terraform
terraform init
terraform plan -var-file=prod.tfvars
terraform apply -var-file=prod.tfvars

# Build Lambda layer
cd ../../lambda_layer
./build_layer.sh

# Deploy dashboard (optional)
cd ..
./scripts/deploy_dashboard.sh
```

### Usage
```bash
# Upload student data to trigger processing
aws s3 cp production_data/student_text_samples.jsonl s3://vocab-rec-engine-input-data-prod/

# Monitor processing
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --start-time 2025-11-13T00:00:00Z \
  --end-time 2025-11-14T00:00:00Z \
  --period 3600 \
  --statistics Average

# View dashboard
open "https://dzo1vamgxcpsx.cloudfront.net"
```

## API Reference

### Data Ingestion Lambda
**Trigger**: S3 ObjectCreated event
**Input**: JSONL file with student writing samples
**Processing**: Groups samples by student, initiates analysis workflow

### Recommendation Engine Lambda
**Input**: Student ID and linguistic analysis
**Processing**: Gap identification, candidate selection, scoring
**Output**: Top 10 personalized vocabulary recommendations

### Report Generation Lambda
**Input**: Student profiles and recommendations
**Processing**: Data compilation and validation
**Output**: Structured JSON reports in S3

### Data Schemas

#### Student Input Format
```json
{
  "student_id": "string",
  "grade_level": "integer (6-8)",
  "timestamp": "ISO 8601 datetime",
  "assignment_type": "conversation|written_essay|written_paragraph",
  "text": "string (student writing sample)",
  "vocabulary_focus": ["string"] // optional
}
```

#### Recommendation Output Format
```json
{
  "student_id": "string",
  "recommendation_date": "ISO 8601 datetime",
  "word": "string",
  "definition": "string",
  "context": "string",
  "grade_level": "integer",
  "frequency_score": "float (0-1)",
  "academic_utility": "high|medium|low",
  "gap_addressed": "string"
}
```

### Error Handling
- **Invalid Data**: Schema validation errors logged and reported
- **Processing Failures**: Automatic retry with exponential backoff
- **System Errors**: CloudWatch alarms trigger notifications
- **Data Quality Issues**: Validation failures prevent corrupted data storage

## Performance & Scaling

### System Performance
- **Processing Speed**: < 1 second per student analysis
- **Memory Usage**: < 512MB per Lambda execution
- **Concurrent Processing**: Up to 1000 simultaneous students
- **Batch Efficiency**: 20 students processed in < 60 seconds

### Cost Optimization
- **Lambda Cost**: ~$0.20/month for 1000 students
- **Storage Cost**: ~$0.05/GB/month for S3
- **Database Cost**: ~$2-5/month for DynamoDB (on-demand)
- **Total MVP Cost**: < $10/month for production use

### Scalability Features
- **Auto-scaling**: Lambda functions scale automatically
- **Event-driven**: No polling, instant processing
- **Stateless Design**: Horizontal scaling without conflicts
- **Global CDN**: CloudFront for worldwide access

---

**System Status**: ✅ Production Ready
**Last Updated**: November 13, 2025
**Version**: 1.0.0
