#!/bin/bash

# Verification script for AWS transformation
# This script checks that all required files and configurations are in place

set -e

echo "=========================================="
echo "Card Approval Prediction - AWS Transformation Verification"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Function to check file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $1 missing"
        ((FAILED++))
        return 1
    fi
}

# Function to check directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 directory exists"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} $1 directory missing"
        ((FAILED++))
        return 1
    fi
}

# Function to check file contains string
check_content() {
    if grep -q "$2" "$1" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $1 contains '$2'"
        ((PASSED++))
        return 0
    else
        echo -e "${YELLOW}⚠${NC} $1 does not contain '$2'"
        ((WARNINGS++))
        return 1
    fi
}

echo "1. Checking Pulumi Infrastructure Files..."
echo "-------------------------------------------"
check_dir "pulumi"
check_file "pulumi/__main__.py"
check_file "pulumi/Pulumi.yaml"
check_file "pulumi/requirements.txt"
check_file "pulumi/README.md"
check_content "pulumi/__main__.py" "pulumi_aws"
check_content "pulumi/__main__.py" "aws.s3.Bucket"
echo ""

echo "2. Checking GitHub Actions Workflows..."
echo "-------------------------------------------"
check_dir ".github/workflows"
check_file ".github/workflows/ci.yml"
check_file ".github/workflows/cd.yml"
check_content ".github/workflows/ci.yml" "CodeQL"
check_content ".github/workflows/cd.yml" "apprunner"
echo ""

echo "3. Checking DVC Configuration..."
echo "-------------------------------------------"
check_dir ".dvc"
check_file ".dvc/config"
check_file ".dvcignore"
check_content ".dvc/config" "s3storage"
check_content ".dvc/config" "s3://"
echo ""

echo "4. Checking Application Files..."
echo "-------------------------------------------"
check_file "app/services/drift_detection.py"
check_file "app/routers/drift.py"
check_content "app/services/drift_detection.py" "evidently"
check_content "app/routers/drift.py" "drift"
check_content "app/core/config.py" "AWS"
echo ""

echo "5. Checking Configuration Files..."
echo "-------------------------------------------"
check_file "config-aws.env"
check_file "Dockerfile"
check_file "requirements.txt"
check_file "pyproject.toml"
check_content "requirements.txt" "boto3"
check_content "requirements.txt" "dvc"
check_content "requirements.txt" "evidently"
check_content "Dockerfile" "awscli"
echo ""

echo "6. Checking Documentation..."
echo "-------------------------------------------"
check_file "README-AWS.md"
check_file "TRANSFORMATION_SUMMARY.md"
check_file "MIGRATION_GUIDE.md"
check_file "QUICK_START_AWS.md"
check_file "PROJECT_TRANSFORMATION_COMPLETE.md"
check_file "DOCUMENTATION_INDEX.md"
check_file "docs/00_Setup_Guide_AWS.md"
echo ""

echo "7. Checking Removed GCP Files..."
echo "-------------------------------------------"
if [ ! -d "terraform" ] || [ -z "$(ls -A terraform 2>/dev/null)" ]; then
    echo -e "${YELLOW}⚠${NC} terraform directory removed or empty (expected for AWS-only)"
    ((WARNINGS++))
else
    echo -e "${GREEN}✓${NC} terraform directory still exists (OK if keeping both versions)"
    ((PASSED++))
fi

if [ ! -f "Jenkinsfile" ]; then
    echo -e "${YELLOW}⚠${NC} Jenkinsfile removed (expected for GitHub Actions)"
    ((WARNINGS++))
else
    echo -e "${GREEN}✓${NC} Jenkinsfile still exists (OK if keeping both versions)"
    ((PASSED++))
fi
echo ""

echo "8. Checking Python Dependencies..."
echo "-------------------------------------------"
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓${NC} Python 3 is installed"
    ((PASSED++))
    
    # Check if in virtual environment
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        echo -e "${GREEN}✓${NC} Virtual environment is active"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠${NC} No virtual environment detected"
        ((WARNINGS++))
    fi
else
    echo -e "${RED}✗${NC} Python 3 is not installed"
    ((FAILED++))
fi
echo ""

echo "9. Checking AWS CLI..."
echo "-------------------------------------------"
if command -v aws &> /dev/null; then
    echo -e "${GREEN}✓${NC} AWS CLI is installed"
    ((PASSED++))
    
    # Check if configured
    if aws sts get-caller-identity &> /dev/null; then
        echo -e "${GREEN}✓${NC} AWS CLI is configured"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠${NC} AWS CLI not configured (run 'aws configure')"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}⚠${NC} AWS CLI not installed (install with 'pip install awscli')"
    ((WARNINGS++))
fi
echo ""

echo "10. Checking Pulumi CLI..."
echo "-------------------------------------------"
if command -v pulumi &> /dev/null; then
    echo -e "${GREEN}✓${NC} Pulumi CLI is installed"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠${NC} Pulumi CLI not installed (install from https://www.pulumi.com/docs/get-started/install/)"
    ((WARNINGS++))
fi
echo ""

echo "11. Checking DVC..."
echo "-------------------------------------------"
if command -v dvc &> /dev/null; then
    echo -e "${GREEN}✓${NC} DVC is installed"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠${NC} DVC not installed (install with 'pip install dvc[s3]')"
    ((WARNINGS++))
fi
echo ""

echo "12. Checking Docker..."
echo "-------------------------------------------"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker is installed"
    ((PASSED++))
    
    # Check if Docker daemon is running
    if docker info &> /dev/null; then
        echo -e "${GREEN}✓${NC} Docker daemon is running"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠${NC} Docker daemon is not running"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}⚠${NC} Docker not installed"
    ((WARNINGS++))
fi
echo ""

echo "=========================================="
echo "Verification Summary"
echo "=========================================="
echo -e "${GREEN}Passed:${NC} $PASSED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "${RED}Failed:${NC} $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ Transformation verification PASSED!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Review README-AWS.md for architecture overview"
    echo "2. Follow QUICK_START_AWS.md for deployment"
    echo "3. Configure AWS credentials: aws configure"
    echo "4. Deploy infrastructure: cd pulumi && pulumi up"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Transformation verification FAILED!${NC}"
    echo ""
    echo "Please fix the failed checks above before proceeding."
    echo ""
    exit 1
fi
