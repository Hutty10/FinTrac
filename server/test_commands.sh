#!/bin/bash
# Quick test commands for FinTrac

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}FinTrac Testing Quick Reference${NC}\n"

# Help function
show_help() {
    echo "Usage: ./test_commands.sh [command]"
    echo ""
    echo "Available commands:"
    echo "  all              - Run all tests"
    echo "  repos            - Run repository tests only"
    echo "  services         - Run service tests only"
    echo "  api              - Run API integration tests only"
    echo "  security         - Run security tests only"
    echo "  coverage         - Run tests with coverage report"
    echo "  parallel         - Run tests in parallel"
    echo "  verbose          - Run tests with verbose output"
    echo "  debug            - Run tests with print statements"
    echo "  single [name]    - Run single test by name"
    echo "  markers          - Show all test markers"
    echo "  clean            - Clean test cache and coverage"
    echo "  help             - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./test_commands.sh all"
    echo "  ./test_commands.sh coverage"
    echo "  ./test_commands.sh single test_register_user_success"
}

# Run all tests
run_all() {
    echo -e "${GREEN}Running all tests...${NC}\n"
    pytest -v
}

# Run repository tests
run_repos() {
    echo -e "${GREEN}Running repository tests...${NC}\n"
    pytest tests/test_repositories.py -v
}

# Run service tests
run_services() {
    echo -e "${GREEN}Running service tests...${NC}\n"
    pytest tests/test_services.py -v
}

# Run API integration tests
run_api() {
    echo -e "${GREEN}Running API integration tests...${NC}\n"
    pytest tests/test_api_integration.py -v
}

# Run security tests
run_security() {
    echo -e "${GREEN}Running security tests...${NC}\n"
    pytest tests/test_security_and_edge_cases.py -v -m security
}

# Run with coverage
run_coverage() {
    echo -e "${GREEN}Running tests with coverage...${NC}\n"
    pytest --cov=src --cov-report=html --cov-report=term-missing
    echo -e "\n${GREEN}Coverage report generated. Open htmlcov/index.html to view${NC}"
}

# Run in parallel
run_parallel() {
    echo -e "${GREEN}Running tests in parallel...${NC}\n"
    pytest -n auto -v
}

# Run with verbose output
run_verbose() {
    echo -e "${GREEN}Running tests with verbose output...${NC}\n"
    pytest -v -l --tb=short
}

# Run with debug output (show print statements)
run_debug() {
    echo -e "${GREEN}Running tests with debug output...${NC}\n"
    pytest -v -s
}

# Run single test
run_single() {
    if [ -z "$1" ]; then
        echo "Usage: ./test_commands.sh single [test_name]"
        return
    fi
    echo -e "${GREEN}Running test: $1${NC}\n"
    pytest -v -k "$1"
}

# Show markers
show_markers() {
    echo -e "${GREEN}Available test markers:${NC}\n"
    pytest --markers
}

# Clean cache
clean_cache() {
    echo -e "${GREEN}Cleaning test cache...${NC}\n"
    rm -rf .pytest_cache
    rm -rf htmlcov
    rm -rf .coverage
    echo -e "${GREEN}Cache cleaned${NC}"
}

# Main script
case "${1:-all}" in
    all)
        run_all
        ;;
    repos)
        run_repos
        ;;
    services)
        run_services
        ;;
    api)
        run_api
        ;;
    security)
        run_security
        ;;
    coverage)
        run_coverage
        ;;
    parallel)
        run_parallel
        ;;
    verbose)
        run_verbose
        ;;
    debug)
        run_debug
        ;;
    single)
        run_single "$2"
        ;;
    markers)
        show_markers
        ;;
    clean)
        clean_cache
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
