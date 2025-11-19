#!/bin/bash
#
# GitHub Actions Workflow Testing Script
#
# This script triggers and monitors GitHub Actions workflows using gh CLI.
# It provides real-time status updates and comprehensive testing.
#
# Usage:
#   ./test_workflows.sh [workflow-name]
#   ./test_workflows.sh all          # Test all workflows
#   ./test_workflows.sh ci           # Test only CI workflow
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# GitHub CLI path
GH_CLI="${GH_CLI:-gh}"
if command -v /usr/bin/gh &> /dev/null; then
    GH_CLI="/usr/bin/gh"
fi

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check if gh CLI is installed
    if ! command -v ${GH_CLI} &> /dev/null; then
        print_error "gh CLI is not installed"
        echo "Install it from: https://cli.github.com/"
        exit 1
    fi
    print_success "gh CLI is installed ($(${GH_CLI} version | head -n1))"

    # Check if authenticated
    if ! ${GH_CLI} auth status &> /dev/null; then
        print_error "Not authenticated with GitHub"
        echo "Run: gh auth login"
        exit 1
    fi
    print_success "Authenticated with GitHub"

    # Check if in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not in a git repository"
        exit 1
    fi
    print_success "In git repository"

    # Check current branch
    CURRENT_BRANCH=$(git branch --show-current)
    print_info "Current branch: ${CURRENT_BRANCH}"
}

# List all workflows
list_workflows() {
    print_header "Available Workflows"
    ${GH_CLI} workflow list
}

# Trigger a workflow
trigger_workflow() {
    local workflow_name=$1
    print_header "Triggering Workflow: ${workflow_name}"

    # Get current branch
    local branch=$(git branch --show-current)

    # Trigger the workflow
    if ${GH_CLI} workflow run "${workflow_name}" --ref "${branch}"; then
        print_success "Workflow triggered successfully"

        # Wait a moment for the run to start
        sleep 5

        # Get the latest run
        print_info "Fetching latest run..."
        local run_id=$(${GH_CLI} run list --workflow="${workflow_name}" --limit 1 --json databaseId --jq '.[0].databaseId')

        if [ -n "$run_id" ]; then
            print_success "Run ID: ${run_id}"
            echo "View run: ${GH_CLI} run view ${run_id}"
            return 0
        else
            print_warning "Could not fetch run ID"
            return 1
        fi
    else
        print_error "Failed to trigger workflow"
        return 1
    fi
}

# Monitor a workflow run
monitor_workflow() {
    local workflow_name=$1
    print_header "Monitoring Workflow: ${workflow_name}"

    # Get the latest run
    local run_id=$(${GH_CLI} run list --workflow="${workflow_name}" --limit 1 --json databaseId --jq '.[0].databaseId')

    if [ -z "$run_id" ]; then
        print_error "No runs found for ${workflow_name}"
        return 1
    fi

    print_info "Watching run ${run_id}..."
    ${GH_CLI} run watch ${run_id}
}

# View workflow run details
view_workflow_run() {
    local workflow_name=$1
    print_header "Workflow Run Details: ${workflow_name}"

    local run_id=$(${GH_CLI} run list --workflow="${workflow_name}" --limit 1 --json databaseId --jq '.[0].databaseId')

    if [ -z "$run_id" ]; then
        print_error "No runs found for ${workflow_name}"
        return 1
    fi

    ${GH_CLI} run view ${run_id}
}

# Test specific workflows
test_ci_workflow() {
    print_header "Testing CI Pipeline Workflow"
    trigger_workflow "CI Pipeline" || trigger_workflow "ci.yml"
}

test_security_workflow() {
    print_header "Testing Security Scanning Workflow"
    trigger_workflow "Security Scanning" || trigger_workflow "security.yml"
}

test_performance_workflow() {
    print_header "Testing Performance Benchmarks Workflow"
    trigger_workflow "Performance Benchmarks" || trigger_workflow "performance.yml"
}

# Test all workflows
test_all_workflows() {
    print_header "Testing All Workflows"

    local workflows=(
        "CI Pipeline"
        "Security Scanning"
        "Performance Benchmarks"
    )

    for workflow in "${workflows[@]}"; do
        echo ""
        trigger_workflow "${workflow}" || print_warning "Could not trigger ${workflow}"
        sleep 2
    done

    print_header "All Workflows Triggered"
    print_info "Listing all recent runs..."
    ${GH_CLI} run list --limit 10
}

# View workflow status
view_workflow_status() {
    print_header "Current Workflow Status"
    ${GH_CLI} run list --limit 15
}

# Main script
main() {
    local command=${1:-status}

    check_prerequisites

    case "$command" in
        list)
            list_workflows
            ;;
        ci)
            test_ci_workflow
            ;;
        security)
            test_security_workflow
            ;;
        performance)
            test_performance_workflow
            ;;
        all)
            test_all_workflows
            ;;
        monitor)
            if [ -z "$2" ]; then
                print_error "Please specify a workflow name to monitor"
                exit 1
            fi
            monitor_workflow "$2"
            ;;
        view)
            if [ -z "$2" ]; then
                print_error "Please specify a workflow name to view"
                exit 1
            fi
            view_workflow_run "$2"
            ;;
        status)
            view_workflow_status
            ;;
        *)
            echo "Usage: $0 {list|ci|security|performance|all|monitor|view|status}"
            echo ""
            echo "Commands:"
            echo "  list         - List all available workflows"
            echo "  ci           - Test CI workflow"
            echo "  security     - Test security workflow"
            echo "  performance  - Test performance workflow"
            echo "  all          - Test all workflows"
            echo "  monitor      - Monitor a specific workflow"
            echo "  view         - View workflow run details"
            echo "  status       - View current workflow status"
            exit 1
            ;;
    esac
}

# Run main script
main "$@"
