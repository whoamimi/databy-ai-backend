#!/bin/bash
# AWS Stop Script - Stop SageMaker and Bedrock Services
# Stops all cost-incurring AWS resources
set -e  # Exit on any error

echo "==================================="
echo "Stopping AWS Services"
echo "==================================="
echo ""
echo "⚠️  This will stop all active billable resources:"
echo "  - SageMaker Endpoints"
echo "  - SageMaker Training/Transform/Processing Jobs"
echo "  - SageMaker Notebook Instances"
echo ""

# Read configuration from environment or arguments
REGION=${1:-${AWS_REGION:-"us-east-1"}}
DRY_RUN=${2:-"false"}

if [ "$DRY_RUN" = "true" ]; then
    echo "🔍 DRY RUN MODE - No resources will be deleted"
    echo ""
fi

echo "Configuration:"
echo "  Region: $REGION"
echo "  Dry Run: $DRY_RUN"
echo ""

# Confirmation prompt (skip in dry-run mode)
if [ "$DRY_RUN" != "true" ]; then
    read -p "Are you sure you want to proceed? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "Aborted by user"
        exit 0
    fi
    echo ""
fi

TOTAL_DELETED=0
TOTAL_STOPPED=0
ERRORS=0

# Function to handle errors
handle_error() {
    echo "⚠️  Error: $1"
    ERRORS=$((ERRORS + 1))
}

# ====================
# 1. SAGEMAKER ENDPOINTS
# ====================
echo "=== 1. Checking SageMaker Endpoints ==="
ENDPOINTS=$(aws sagemaker list-endpoints \
    --region "$REGION" \
    --query "Endpoints[?EndpointStatus=='InService'].EndpointName" \
    --output text 2>/dev/null || echo "")

if [ -n "$ENDPOINTS" ]; then
    ENDPOINT_COUNT=$(echo "$ENDPOINTS" | wc -w)
    echo "Found $ENDPOINT_COUNT active endpoint(s):"

    for ENDPOINT in $ENDPOINTS; do
        # Get instance details for cost estimation
        INSTANCE_INFO=$(aws sagemaker describe-endpoint \
            --region "$REGION" \
            --endpoint-name "$ENDPOINT" \
            --query 'ProductionVariants[0].{Type:InstanceType,Count:CurrentInstanceCount}' \
            --output text 2>/dev/null || echo "unknown unknown")

        echo "  📍 $ENDPOINT ($INSTANCE_INFO)"

        if [ "$DRY_RUN" != "true" ]; then
            if aws sagemaker delete-endpoint \
                --region "$REGION" \
                --endpoint-name "$ENDPOINT" 2>/dev/null; then
                echo "    ✓ Deleted"
                TOTAL_DELETED=$((TOTAL_DELETED + 1))
            else
                handle_error "Failed to delete endpoint: $ENDPOINT"
            fi
        else
            echo "    [DRY RUN] Would delete"
        fi
    done
else
    echo "  ✓ No active endpoints found"
fi
echo ""

# ====================
# 2. SAGEMAKER TRAINING JOBS
# ====================
echo "=== 2. Checking SageMaker Training Jobs ==="
TRAINING_JOBS=$(aws sagemaker list-training-jobs \
    --region "$REGION" \
    --status-equals "InProgress" \
    --query "TrainingJobSummaries[].TrainingJobName" \
    --output text 2>/dev/null || echo "")

if [ -n "$TRAINING_JOBS" ]; then
    JOB_COUNT=$(echo "$TRAINING_JOBS" | wc -w)
    echo "Found $JOB_COUNT running training job(s):"

    for JOB in $TRAINING_JOBS; do
        echo "  🏃 $JOB"

        if [ "$DRY_RUN" != "true" ]; then
            if aws sagemaker stop-training-job \
                --region "$REGION" \
                --training-job-name "$JOB" 2>/dev/null; then
                echo "    ✓ Stopped"
                TOTAL_STOPPED=$((TOTAL_STOPPED + 1))
            else
                handle_error "Failed to stop training job: $JOB"
            fi
        else
            echo "    [DRY RUN] Would stop"
        fi
    done
else
    echo "  ✓ No running training jobs found"
fi
echo ""

# ====================
# 3. SAGEMAKER TRANSFORM JOBS
# ====================
echo "=== 3. Checking SageMaker Transform Jobs ==="
TRANSFORM_JOBS=$(aws sagemaker list-transform-jobs \
    --region "$REGION" \
    --status-equals "InProgress" \
    --query "TransformJobSummaries[].TransformJobName" \
    --output text 2>/dev/null || echo "")

if [ -n "$TRANSFORM_JOBS" ]; then
    JOB_COUNT=$(echo "$TRANSFORM_JOBS" | wc -w)
    echo "Found $JOB_COUNT running transform job(s):"

    for JOB in $TRANSFORM_JOBS; do
        echo "  🔄 $JOB"

        if [ "$DRY_RUN" != "true" ]; then
            if aws sagemaker stop-transform-job \
                --region "$REGION" \
                --transform-job-name "$JOB" 2>/dev/null; then
                echo "    ✓ Stopped"
                TOTAL_STOPPED=$((TOTAL_STOPPED + 1))
            else
                handle_error "Failed to stop transform job: $JOB"
            fi
        else
            echo "    [DRY RUN] Would stop"
        fi
    done
else
    echo "  ✓ No running transform jobs found"
fi
echo ""

# ====================
# 4. SAGEMAKER NOTEBOOK INSTANCES
# ====================
echo "=== 4. Checking SageMaker Notebook Instances ==="
NOTEBOOKS=$(aws sagemaker list-notebook-instances \
    --region "$REGION" \
    --status-equals "InService" \
    --query "NotebookInstances[].NotebookInstanceName" \
    --output text 2>/dev/null || echo "")

if [ -n "$NOTEBOOKS" ]; then
    NOTEBOOK_COUNT=$(echo "$NOTEBOOKS" | wc -w)
    echo "Found $NOTEBOOK_COUNT running notebook instance(s):"

    for NOTEBOOK in $NOTEBOOKS; do
        echo "  📓 $NOTEBOOK"

        if [ "$DRY_RUN" != "true" ]; then
            if aws sagemaker stop-notebook-instance \
                --region "$REGION" \
                --notebook-instance-name "$NOTEBOOK" 2>/dev/null; then
                echo "    ✓ Stopped"
                TOTAL_STOPPED=$((TOTAL_STOPPED + 1))
            else
                handle_error "Failed to stop notebook: $NOTEBOOK"
            fi
        else
            echo "    [DRY RUN] Would stop"
        fi
    done
else
    echo "  ✓ No running notebook instances found"
fi
echo ""

# ====================
# 5. SAGEMAKER PROCESSING JOBS
# ====================
echo "=== 5. Checking SageMaker Processing Jobs ==="
PROCESSING_JOBS=$(aws sagemaker list-processing-jobs \
    --region "$REGION" \
    --status-equals "InProgress" \
    --query "ProcessingJobSummaries[].ProcessingJobName" \
    --output text 2>/dev/null || echo "")

if [ -n "$PROCESSING_JOBS" ]; then
    JOB_COUNT=$(echo "$PROCESSING_JOBS" | wc -w)
    echo "Found $JOB_COUNT running processing job(s):"

    for JOB in $PROCESSING_JOBS; do
        echo "  ⚙️  $JOB"

        if [ "$DRY_RUN" != "true" ]; then
            if aws sagemaker stop-processing-job \
                --region "$REGION" \
                --processing-job-name "$JOB" 2>/dev/null; then
                echo "    ✓ Stopped"
                TOTAL_STOPPED=$((TOTAL_STOPPED + 1))
            else
                handle_error "Failed to stop processing job: $JOB"
            fi
        else
            echo "    [DRY RUN] Would stop"
        fi
    done
else
    echo "  ✓ No running processing jobs found"
fi
echo ""

# ====================
# 6. SUMMARY
# ====================
echo "=== 6. Summary ==="
if [ "$DRY_RUN" = "true" ]; then
    echo "ℹ️  Dry run mode - no resources were modified"
else
    echo "Resources stopped/deleted:"
    echo "  • Deleted: $TOTAL_DELETED"
    echo "  • Stopped: $TOTAL_STOPPED"
    echo "  • Errors: $ERRORS"

    if [ $((TOTAL_DELETED + TOTAL_STOPPED)) -gt 0 ]; then
        echo ""
        echo "✅ Success! The following charges will stop:"
        echo "  • SageMaker endpoint charges (immediate)"
        echo "  • Training job charges (immediate)"
        echo "  • Notebook instance charges (immediate)"
        echo "  • EC2 instance charges (immediate)"
        echo ""
        echo "💰 Estimated savings: Check AWS Cost Explorer in 24 hours"
    else
        echo ""
        echo "✓ No billable resources were found running"
    fi
fi
echo ""

echo "==================================="
echo "Stop Complete"
echo "==================================="

if [ $ERRORS -gt 0 ]; then
    echo "⚠️  Completed with $ERRORS error(s). Check output above."
    exit 1
fi

exit 0
