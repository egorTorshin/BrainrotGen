#!/bin/bash

# Target host (default to localhost)
TARGET_HOST=${1:-"http://localhost:8000"}
USERS=${2:-10}
SPAWN_RATE=${3:-1}
RUN_TIME=${4:-"30s"}

echo "Running load tests against $TARGET_HOST..."
echo "Config: $USERS users, $SPAWN_RATE spawn rate, $RUN_TIME duration"

# Create reports directory if it doesn't exist
REPORTS_DIR="reports/load"
mkdir -p "$REPORTS_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$REPORTS_DIR/report_$TIMESTAMP.html"

# Run locust in headless mode
locust -f backend/tests/load_test.py \
    --headless \
    --host "$TARGET_HOST" \
    --users "$USERS" \
    --spawn-rate "$SPAWN_RATE" \
    --run-time "$RUN_TIME" \
    --html "$REPORT_FILE" \
    --p95-threshold 200.0

echo ""
echo ">>> Detailed HTML report saved to: $REPORT_FILE"
