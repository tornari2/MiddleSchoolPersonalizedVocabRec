#!/bin/bash

# ============================================================================
# Full Pipeline Runner - Add Data and Execute Complete Processing Workflow
# ============================================================================
# This script:
# 1. Checks for existing data or generates test data
# 2. Uploads data to S3 input bucket (triggers data ingestion Lambda)
# 3. Waits for data ingestion to complete
# 4. Invokes Step Function for each student to generate recommendations
# 5. Monitors execution and verifies results
# ============================================================================

set -e

# Configuration
ENV="${ENV:-prod}"
AWS_REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID="971422717446"
PROJECT_NAME="vocab-rec-engine"

# Resource names
INPUT_BUCKET="${PROJECT_NAME}-input-data-${ENV}"
OUTPUT_BUCKET="${PROJECT_NAME}-output-reports-${ENV}"
PROFILES_TABLE="${PROJECT_NAME}-vocabulary-profiles-${ENV}"
RECOMMENDATIONS_TABLE="${PROJECT_NAME}-vocabulary-recommendations-${ENV}"
STEP_FUNCTION_ARN="arn:aws:states:${AWS_REGION}:${ACCOUNT_ID}:stateMachine:${PROJECT_NAME}-processing-workflow-${ENV}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; echo -e "${CYAN}▶ $1${NC}"; echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"; }

# Test data file
TEST_DATA_FILE="production_data/student_text_samples.jsonl"
TEMP_UPLOAD_FILE="/tmp/vocab_pipeline_upload_$(date +%s).jsonl"

# ============================================================================
# Step 1: Prepare Test Data
# ============================================================================
prepare_test_data() {
    log_step "Step 1: Preparing Test Data"
    
    if [[ -f "$TEST_DATA_FILE" ]]; then
        log_info "Using existing test data: $TEST_DATA_FILE"
        cp "$TEST_DATA_FILE" "$TEMP_UPLOAD_FILE"
        
        # Count students
        STUDENT_COUNT=$(jq -r '.student_id' "$TEMP_UPLOAD_FILE" | sort -u | wc -l | tr -d ' ')
        SAMPLE_COUNT=$(wc -l < "$TEMP_UPLOAD_FILE" | tr -d ' ')
        log_success "Found $SAMPLE_COUNT samples for $STUDENT_COUNT students"
    else
        log_warning "Test data file not found: $TEST_DATA_FILE"
        log_info "Creating minimal test data..."
        
        # Create minimal test data with 3 students
        cat > "$TEMP_UPLOAD_FILE" << 'EOF'
{"student_id": "S001", "grade_level": 7, "timestamp": "2024-11-11T10:00:00Z", "assignment_type": "written_essay", "text": "The ecosystem in our local park demonstrates biodiversity through various species of plants and animals. Climate change affects weather patterns globally, requiring immediate action to reduce carbon emissions. Scientists analyze data to understand these complex environmental systems."}
{"student_id": "S001", "grade_level": 7, "timestamp": "2024-11-12T10:00:00Z", "assignment_type": "written_paragraph", "text": "Character development plays a crucial role in understanding literature. Authors use various techniques to create compelling narratives that engage readers and convey important themes."}
{"student_id": "S002", "grade_level": 6, "timestamp": "2024-11-11T10:00:00Z", "assignment_type": "written_essay", "text": "Mathematics helps us solve problems in everyday life. We use numbers to calculate, measure, and understand patterns. Geometry teaches us about shapes and spatial relationships."}
{"student_id": "S002", "grade_level": 6, "timestamp": "2024-11-12T10:00:00Z", "assignment_type": "written_paragraph", "text": "History shows us how past events shape our present world. Learning about different cultures and civilizations helps us understand diversity and global connections."}
{"student_id": "S003", "grade_level": 8, "timestamp": "2024-11-11T10:00:00Z", "assignment_type": "written_essay", "text": "Scientific research requires careful observation, hypothesis formation, and experimental validation. The scientific method provides a systematic approach to understanding natural phenomena and advancing human knowledge."}
{"student_id": "S003", "grade_level": 8, "timestamp": "2024-11-12T10:00:00Z", "assignment_type": "written_paragraph", "text": "Effective communication involves clear expression of ideas, active listening, and understanding different perspectives. These skills are essential for collaboration and problem-solving in academic and professional settings."}
EOF
        
        STUDENT_COUNT=3
        SAMPLE_COUNT=6
        log_success "Created test data: $SAMPLE_COUNT samples for $STUDENT_COUNT students"
    fi
    
    # Extract unique student IDs
    STUDENT_IDS=($(jq -r '.student_id' "$TEMP_UPLOAD_FILE" | sort -u))
    log_info "Students to process: ${STUDENT_IDS[*]}"
}

# ============================================================================
# Step 2: Upload Data to S3 (Triggers Data Ingestion Lambda)
# ============================================================================
upload_to_s3() {
    log_step "Step 2: Uploading Data to S3 Input Bucket"
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    S3_KEY="student_data_${TIMESTAMP}.jsonl"
    
    log_info "Uploading to: s3://${INPUT_BUCKET}/${S3_KEY}"
    
    aws s3 cp "$TEMP_UPLOAD_FILE" "s3://${INPUT_BUCKET}/${S3_KEY}" \
        --region "$AWS_REGION" \
        --content-type "application/x-ndjson"
    
    if [[ $? -eq 0 ]]; then
        log_success "Data uploaded successfully"
        echo "$S3_KEY" > /tmp/vocab_pipeline_s3_key.txt
    else
        log_error "Failed to upload data to S3"
        exit 1
    fi
}

# ============================================================================
# Step 3: Wait for Data Ingestion to Complete
# ============================================================================
wait_for_data_ingestion() {
    log_step "Step 3: Waiting for Data Ingestion to Complete"
    
    log_info "Waiting for student profiles to be created in DynamoDB..."
    log_info "This may take 1-3 minutes..."
    
    MAX_WAIT=180  # 3 minutes
    ELAPSED=0
    CHECK_INTERVAL=10
    
    while [[ $ELAPSED -lt $MAX_WAIT ]]; do
        # Check if profiles exist for our students
        FOUND_COUNT=0
        for student_id in "${STUDENT_IDS[@]}"; do
            COUNT=$(aws dynamodb scan \
                --table-name "$PROFILES_TABLE" \
                --filter-expression "student_id = :sid" \
                --expression-attribute-values "{\":sid\": {\"S\": \"$student_id\"}}" \
                --select COUNT \
                --region "$AWS_REGION" \
                --query 'Count' \
                --output text 2>/dev/null || echo "0")
            
            if [[ "$COUNT" -gt 0 ]]; then
                ((FOUND_COUNT++))
            fi
        done
        
        if [[ $FOUND_COUNT -eq ${#STUDENT_IDS[@]} ]]; then
            log_success "All $FOUND_COUNT student profiles created in DynamoDB"
            return 0
        fi
        
        log_info "Found $FOUND_COUNT/${#STUDENT_IDS[@]} profiles... waiting ${CHECK_INTERVAL}s"
        sleep $CHECK_INTERVAL
        ELAPSED=$((ELAPSED + CHECK_INTERVAL))
    done
    
    if [[ $FOUND_COUNT -lt ${#STUDENT_IDS[@]} ]]; then
        log_warning "Only $FOUND_COUNT/${#STUDENT_IDS[@]} profiles found after $MAX_WAIT seconds"
        log_info "Continuing anyway - some students may not have profiles yet"
    fi
}

# ============================================================================
# Step 4: Invoke Step Function for Each Student
# ============================================================================
invoke_step_functions() {
    log_step "Step 4: Invoking Step Functions for Recommendations"
    
    EXECUTION_ARNS=()
    
    for student_id in "${STUDENT_IDS[@]}"; do
        log_info "Starting Step Function execution for student: $student_id"
        
        EXECUTION_NAME="pipeline-${student_id}-$(date +%s)"
        
        EXECUTION_ARN=$(aws stepfunctions start-execution \
            --state-machine-arn "$STEP_FUNCTION_ARN" \
            --name "$EXECUTION_NAME" \
            --input "{\"student_id\": \"$student_id\", \"students\": [\"$student_id\"], \"batch_mode\": false}" \
            --region "$AWS_REGION" \
            --query 'executionArn' \
            --output text 2>/dev/null)
        
        if [[ -n "$EXECUTION_ARN" ]]; then
            EXECUTION_ARNS+=("$EXECUTION_ARN")
            log_success "Started execution: $EXECUTION_ARN"
        else
            log_error "Failed to start execution for $student_id"
        fi
        
        # Small delay between invocations
        sleep 2
    done
    
    # Save execution ARNs for monitoring
    printf '%s\n' "${EXECUTION_ARNS[@]}" > /tmp/vocab_pipeline_executions.txt
    log_info "Started ${#EXECUTION_ARNS[@]} Step Function executions"
}

# ============================================================================
# Step 5: Monitor Step Function Executions
# ============================================================================
monitor_executions() {
    log_step "Step 5: Monitoring Step Function Executions"
    
    if [[ ! -f /tmp/vocab_pipeline_executions.txt ]]; then
        log_error "No execution ARNs found"
        return 1
    fi
    
    EXECUTION_ARNS=($(cat /tmp/vocab_pipeline_executions.txt))
    TOTAL=${#EXECUTION_ARNS[@]}
    SUCCEEDED=0
    FAILED=0
    RUNNING=0
    
    log_info "Monitoring $TOTAL executions..."
    log_info "This may take 2-5 minutes per student..."
    
    MAX_WAIT=600  # 10 minutes total
    ELAPSED=0
    CHECK_INTERVAL=15
    
    while [[ $ELAPSED -lt $MAX_WAIT ]] && [[ $((SUCCEEDED + FAILED)) -lt $TOTAL ]]; do
        SUCCEEDED=0
        FAILED=0
        RUNNING=0
        
        for execution_arn in "${EXECUTION_ARNS[@]}"; do
            STATUS=$(aws stepfunctions describe-execution \
                --execution-arn "$execution_arn" \
                --region "$AWS_REGION" \
                --query 'status' \
                --output text 2>/dev/null || echo "UNKNOWN")
            
            case "$STATUS" in
                "SUCCEEDED")
                    ((SUCCEEDED++))
                    ;;
                "FAILED"|"TIMED_OUT"|"ABORTED")
                    ((FAILED++))
                    ;;
                "RUNNING")
                    ((RUNNING++))
                    ;;
            esac
        done
        
        log_info "Status: $SUCCEEDED succeeded, $FAILED failed, $RUNNING running"
        
        if [[ $((SUCCEEDED + FAILED)) -eq $TOTAL ]]; then
            break
        fi
        
        sleep $CHECK_INTERVAL
        ELAPSED=$((ELAPSED + CHECK_INTERVAL))
    done
    
    echo ""
    log_success "Execution Summary:"
    log_info "  ✓ Succeeded: $SUCCEEDED/$TOTAL"
    log_info "  ✗ Failed: $FAILED/$TOTAL"
    log_info "  ⏳ Still Running: $RUNNING/$TOTAL"
    
    if [[ $FAILED -gt 0 ]]; then
        log_warning "Some executions failed. Check CloudWatch logs for details."
    fi
}

# ============================================================================
# Step 6: Verify Results
# ============================================================================
verify_results() {
    log_step "Step 6: Verifying Results"
    
    log_info "Checking DynamoDB tables..."
    
    # Check profiles
    PROFILE_COUNT=$(aws dynamodb scan \
        --table-name "$PROFILES_TABLE" \
        --select COUNT \
        --region "$AWS_REGION" \
        --query 'Count' \
        --output text)
    log_info "  Profiles table: $PROFILE_COUNT records"
    
    # Check recommendations
    REC_COUNT=$(aws dynamodb scan \
        --table-name "$RECOMMENDATIONS_TABLE" \
        --select COUNT \
        --region "$AWS_REGION" \
        --query 'Count' \
        --output text)
    log_info "  Recommendations table: $REC_COUNT records"
    
    # Check S3 output bucket
    log_info "Checking S3 output bucket..."
    REPORT_COUNT=$(aws s3 ls "s3://${OUTPUT_BUCKET}/reports/" --recursive --region "$AWS_REGION" 2>/dev/null | wc -l | tr -d ' ')
    log_info "  Output reports: $REPORT_COUNT files"
    
    # Show sample reports
    if [[ $REPORT_COUNT -gt 0 ]]; then
        log_success "Reports generated successfully!"
        log_info "Sample report locations:"
        for student_id in "${STUDENT_IDS[@]}"; do
            LATEST_REPORT=$(aws s3 ls "s3://${OUTPUT_BUCKET}/reports/${student_id}/" \
                --region "$AWS_REGION" 2>/dev/null | tail -1 | awk '{print $4}')
            if [[ -n "$LATEST_REPORT" ]]; then
                log_info "  s3://${OUTPUT_BUCKET}/reports/${student_id}/${LATEST_REPORT}"
            fi
        done
    else
        log_warning "No reports found in output bucket yet"
    fi
}

# ============================================================================
# Cleanup
# ============================================================================
cleanup() {
    log_info "Cleaning up temporary files..."
    rm -f "$TEMP_UPLOAD_FILE" /tmp/vocab_pipeline_s3_key.txt /tmp/vocab_pipeline_executions.txt
}

# ============================================================================
# Main Execution
# ============================================================================
main() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║   Full Pipeline Runner - Vocabulary Recommendation System  ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    log_info "Environment: ${ENV}"
    log_info "Region: ${AWS_REGION}"
    log_info "Input Bucket: ${INPUT_BUCKET}"
    log_info "Output Bucket: ${OUTPUT_BUCKET}"
    echo ""
    
    # Trap to cleanup on exit
    trap cleanup EXIT
    
    # Run pipeline steps
    prepare_test_data
    upload_to_s3
    wait_for_data_ingestion
    invoke_step_functions
    monitor_executions
    verify_results
    
    echo ""
    log_step "Pipeline Complete!"
    log_success "✓ Data uploaded to S3"
    log_success "✓ Student profiles created"
    log_success "✓ Recommendations generated"
    log_success "✓ Reports available in S3"
    echo ""
    log_info "View results:"
    log_info "  S3 Reports: https://s3.console.aws.amazon.com/s3/buckets/${OUTPUT_BUCKET}/reports/"
    log_info "  CloudWatch: https://console.aws.amazon.com/cloudwatch/home?region=${AWS_REGION}#dashboards:name=${PROJECT_NAME}-system-dashboard-${ENV}"
    echo ""
}

# Run main function
main "$@"


