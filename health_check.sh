#!/bin/bash

# Health Check Script for Expert LLM System
# This script performs comprehensive health checks for the application

set -euo pipefail

# Configuration
HEALTH_ENDPOINT="http://localhost:8501/_stcore/health"
OLLAMA_ENDPOINT="http://localhost:11434/api/tags"
LOG_FILE="/app/logs/health_check.log"
MAX_RETRIES=3
RETRY_DELAY=5

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log_health() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to check HTTP endpoint
check_endpoint() {
    local url="$1"
    local name="$2"
    local retries=0
    
    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -f -s --max-time 10 "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} $name is healthy"
            log_health "SUCCESS: $name health check passed"
            return 0
        else
            retries=$((retries + 1))
            if [ $retries -lt $MAX_RETRIES ]; then
                echo -e "${YELLOW}⚠${NC} $name check failed, retrying in ${RETRY_DELAY}s... ($retries/$MAX_RETRIES)"
                sleep $RETRY_DELAY
            fi
        fi
    done
    
    echo -e "${RED}✗${NC} $name is unhealthy after $MAX_RETRIES attempts"
    log_health "ERROR: $name health check failed after $MAX_RETRIES attempts"
    return 1
}

# Function to check process
check_process() {
    local process_name="$1"
    
    if pgrep -f "$process_name" > /dev/null; then
        echo -e "${GREEN}✓${NC} $process_name process is running"
        log_health "SUCCESS: $process_name process is running"
        return 0
    else
        echo -e "${RED}✗${NC} $process_name process is not running"
        log_health "ERROR: $process_name process is not running"
        return 1
    fi
}

# Function to check disk space
check_disk_space() {
    local threshold=80
    local usage=$(df /app | awk 'NR==2 {print int($5)}')
    
    if [ "$usage" -lt "$threshold" ]; then
        echo -e "${GREEN}✓${NC} Disk usage is ${usage}% (< ${threshold}%)"
        log_health "SUCCESS: Disk usage is ${usage}%"
        return 0
    else
        echo -e "${RED}✗${NC} Disk usage is ${usage}% (>= ${threshold}%)"
        log_health "WARNING: High disk usage ${usage}%"
        return 1
    fi
}

# Function to check memory usage
check_memory() {
    local threshold=80
    local usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    if [ "$usage" -lt "$threshold" ]; then
        echo -e "${GREEN}✓${NC} Memory usage is ${usage}% (< ${threshold}%)"
        log_health "SUCCESS: Memory usage is ${usage}%"
        return 0
    else
        echo -e "${YELLOW}⚠${NC} Memory usage is ${usage}% (>= ${threshold}%)"
        log_health "WARNING: High memory usage ${usage}%"
        return 0  # Don't fail on memory warning
    fi
}

# Function to check log files
check_logs() {
    local log_dir="/app/logs"
    local error_count
    
    if [ -d "$log_dir" ]; then
        # Count recent errors (last 100 lines)
        error_count=$(find "$log_dir" -name "*.log" -exec tail -100 {} \; 2>/dev/null | grep -c -i "error\|critical\|fatal" || echo "0")
        
        if [ "$error_count" -lt 5 ]; then
            echo -e "${GREEN}✓${NC} Log files healthy (${error_count} recent errors)"
            log_health "SUCCESS: Log files healthy with ${error_count} recent errors"
            return 0
        else
            echo -e "${YELLOW}⚠${NC} Found ${error_count} recent errors in logs"
            log_health "WARNING: Found ${error_count} recent errors in logs"
            return 0  # Don't fail on log warnings
        fi
    else
        echo -e "${YELLOW}⚠${NC} Log directory not found"
        log_health "WARNING: Log directory not found"
        return 0
    fi
}

# Function to check data directory
check_data_directory() {
    local data_dir="/app/data"
    
    if [ -d "$data_dir" ] && [ -w "$data_dir" ]; then
        echo -e "${GREEN}✓${NC} Data directory is accessible and writable"
        log_health "SUCCESS: Data directory is accessible"
        return 0
    else
        echo -e "${RED}✗${NC} Data directory is not accessible or writable"
        log_health "ERROR: Data directory is not accessible"
        return 1
    fi
}

# Main health check function
main() {
    local exit_code=0
    
    echo "=== Expert LLM System Health Check ==="
    echo "Timestamp: $(date)"
    echo ""
    
    # Create log directory if it doesn't exist
    mkdir -p "$(dirname "$LOG_FILE")"
    
    log_health "Starting health check"
    
    # Core application checks
    echo "🔍 Checking core application..."
    check_endpoint "$HEALTH_ENDPOINT" "Streamlit Application" || exit_code=1
    
    # Process checks
    echo ""
    echo "🔍 Checking processes..."
    check_process "streamlit" || exit_code=1
    
    # System resource checks
    echo ""
    echo "🔍 Checking system resources..."
    check_disk_space || exit_code=1
    check_memory
    
    # File system checks
    echo ""
    echo "🔍 Checking file systems..."
    check_data_directory || exit_code=1
    check_logs
    
    # Optional Ollama check (might not be running in same container)
    echo ""
    echo "🔍 Checking external services..."
    if curl -f -s --max-time 5 "$OLLAMA_ENDPOINT" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Ollama service is reachable"
        log_health "SUCCESS: Ollama service is reachable"
    else
        echo -e "${YELLOW}⚠${NC} Ollama service not reachable (this is OK if running separately)"
        log_health "INFO: Ollama service not reachable"
    fi
    
    echo ""
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ Overall health check: PASSED${NC}"
        log_health "SUCCESS: Overall health check passed"
    else
        echo -e "${RED}❌ Overall health check: FAILED${NC}"
        log_health "ERROR: Overall health check failed"
    fi
    
    log_health "Health check completed with exit code $exit_code"
    exit $exit_code
}

# Handle different command line arguments
case "${1:-health}" in
    "health"|"check")
        main
        ;;
    "quick")
        # Quick health check - just the essential endpoint
        check_endpoint "$HEALTH_ENDPOINT" "Streamlit Application"
        ;;
    "verbose")
        # Verbose mode with additional debugging
        set -x
        main
        ;;
    *)
        echo "Usage: $0 [health|check|quick|verbose]"
        echo "  health/check: Full health check (default)"
        echo "  quick: Quick endpoint check only"
        echo "  verbose: Full check with debug output"
        exit 1
        ;;
esac
