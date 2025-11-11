# Data Generation Strategy for Vocabulary Recommendation Engine

## Overview
This document outlines the strategy for generating synthetic student data and managing reference data for the Personalized Vocabulary Recommendation Engine MVP.

## Data Requirements

### Synthetic Student Data (Input)
- **Format**: JSONL files with student text samples
- **Volume**: 20 students × 30 samples = 600 total samples
- **Content Types**:
  - 20 writing assignments (essays, paragraphs)
  - 10 conversational samples (dialogues, responses)
- **Grade Levels**: 6-8 (middle school)
- **Vocabulary Control**: Age-appropriate words with controlled sophistication levels

### Reference Data (Static)
- **Grade Level Words**: Word lists by grade level
- **Word Frequencies**: Academic word frequency data
- **Word Definitions**: Dictionary entries for recommendations

## Generation Strategy Decision

### Option 1: LLM-Based Generation (Claude/GPT)
**Pros:**
- Highly realistic and natural language
- Contextual appropriateness
- Dynamic vocabulary control
- Educational quality content

**Cons:**
- Non-deterministic (results vary between runs)
- API costs and rate limits
- Slower generation speed
- Less reproducible for testing
- Harder to control exact vocabulary distribution

### Option 2: Template-Based Generation (RECOMMENDED)
**Pros:**
- Fully reproducible and deterministic
- Fast generation speed
- Precise vocabulary control
- No API costs or external dependencies
- Easier testing and debugging
- Consistent results across environments

**Cons:**
- May feel less "natural" than LLM-generated content
- Requires more upfront template design
- Limited creativity in content variety

## Recommended Approach: Template-Based Generation

For the MVP, we recommend **template-based generation** with an optional LLM mode for enhanced realism.

### Implementation Strategy

1. **Base Templates**: Structured sentence/paragraph templates with placeholders
2. **Vocabulary Pools**: Curated word lists by grade level and complexity
3. **Content Types**: Separate templates for writing vs conversational content
4. **Quality Assurance**: Built-in validation and quality checks

### Architecture

```
data_generator/
├── templates/
│   ├── writing_templates.json      # Essay/paragraph templates
│   └── conversation_templates.json # Dialogue templates
├── vocabulary/
│   ├── grade_6_words.json         # Grade 6 vocabulary pool
│   ├── grade_7_words.json         # Grade 7 vocabulary pool
│   ├── grade_8_words.json         # Grade 8 vocabulary pool
│   └── academic_words.json        # High-frequency academic words
├── generators/
│   ├── template_generator.py      # Main template-based generator
│   └── llm_generator.py          # Optional LLM generator
├── reference_data/
│   ├── grade_level_words.json     # Static reference data
│   ├── word_frequencies.json      # Word frequency data
│   └── word_definitions.json      # Dictionary definitions
├── config.py                      # Configuration and settings
└── main.py                        # CLI interface
```

## Configuration Options

```python
# config.py
class DataGeneratorConfig:
    USE_LLM = False  # Default to template-based for reproducibility
    NUM_STUDENTS = 20
    SAMPLES_PER_STUDENT = 30
    WRITING_RATIO = 2/3  # 20 writing, 10 conversation per student
    GRADE_DISTRIBUTION = {6: 6, 7: 8, 8: 6}  # Students per grade
    VOCABULARY_COMPLEXITY_RANGE = (0.3, 0.9)  # Sophistication control
    OUTPUT_FORMAT = "jsonl"
    RANDOM_SEED = 42  # For reproducibility
```

## Quality Assurance

### Template Design Principles
1. **Educational Relevance**: Content should reflect actual student writing topics
2. **Vocabulary Progression**: Words should align with grade-level expectations
3. **Structural Variety**: Mix of simple, compound, and complex sentences
4. **Error Simulation**: Optional introduction of common student writing errors

### Validation Checks
- Vocabulary distribution analysis
- Readability metrics (Flesch-Kincaid, etc.)
- Content appropriateness filtering
- Format compliance verification

## Testing Strategy

1. **Unit Tests**: Individual template and vocabulary validation
2. **Integration Tests**: Full data generation pipeline
3. **Quality Metrics**: Automated content quality assessment
4. **Performance Tests**: Generation speed and memory usage

## Future Enhancements

- **Hybrid Approach**: Template base + LLM refinement
- **Adaptive Generation**: Learning from quality feedback
- **Multi-language Support**: Additional language templates
- **Domain-Specific Content**: Subject-area specialized templates

## Decision Rationale

**Template-based generation** is chosen as the primary approach because:

1. **Reproducibility**: Critical for testing and debugging
2. **Cost Efficiency**: No API costs during development
3. **Performance**: Fast generation for large datasets
4. **Control**: Precise vocabulary and quality management
5. **Reliability**: No external API dependencies

The system will include an LLM option (`USE_LLM=True`) for users who want more realistic content, but template-based will be the default and recommended approach for development and testing.
