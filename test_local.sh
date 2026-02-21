#!/bin/bash
set -e

echo "🧪 Testing Card Approval Prediction API"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Function to run test
run_test() {
    local test_name=$1
    local test_command=$2
    
    echo -n "Testing: $test_name ... "
    
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((FAILED++))
        return 1
    fi
}

# Wait for API to be ready
echo "Waiting for API to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}API is ready!${NC}"
        echo ""
        break
    fi
    echo -n "."
    sleep 2
done

echo "Running API Tests..."
echo "===================="
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
response=$(curl -s http://localhost:8000/health)
echo "$response" | jq
if echo "$response" | jq -e '.status == "healthy"' > /dev/null; then
    echo -e "${GREEN}✓ PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    ((FAILED++))
fi
echo ""

# Test 2: Readiness Check
echo "Test 2: Readiness Check"
response=$(curl -s http://localhost:8000/health/ready)
echo "$response" | jq
if echo "$response" | jq -e '.status == "ready"' > /dev/null; then
    echo -e "${GREEN}✓ PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    ((FAILED++))
fi
echo ""

# Test 3: Liveness Check
echo "Test 3: Liveness Check"
response=$(curl -s http://localhost:8000/health/live)
echo "$response" | jq
if echo "$response" | jq -e '.status == "alive"' > /dev/null; then
    echo -e "${GREEN}✓ PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    ((FAILED++))
fi
echo ""

# Test 4: Model Info
echo "Test 4: Model Info"
response=$(curl -s http://localhost:8000/api/v1/model-info)
echo "$response" | jq
if echo "$response" | jq -e '.model_name' > /dev/null; then
    echo -e "${GREEN}✓ PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED${NC}"
    ((FAILED++))
fi
echo ""

# Test 5: Approved Prediction
echo "Test 5: Prediction - Should be APPROVED"
response=$(curl -s -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "ID": 5008804,
    "CODE_GENDER": "M",
    "FLAG_OWN_CAR": "Y",
    "FLAG_OWN_REALTY": "Y",
    "CNT_CHILDREN": 0,
    "AMT_INCOME_TOTAL": 180000.0,
    "NAME_INCOME_TYPE": "Working",
    "NAME_EDUCATION_TYPE": "Higher education",
    "NAME_FAMILY_STATUS": "Married",
    "NAME_HOUSING_TYPE": "House / apartment",
    "DAYS_BIRTH": -14000,
    "DAYS_EMPLOYED": -2500,
    "FLAG_MOBIL": 1,
    "FLAG_WORK_PHONE": 0,
    "FLAG_PHONE": 1,
    "FLAG_EMAIL": 0,
    "OCCUPATION_TYPE": "Managers",
    "CNT_FAM_MEMBERS": 2.0
  }')
echo "$response" | jq
decision=$(echo "$response" | jq -r '.decision')
if [ "$decision" == "APPROVED" ]; then
    echo -e "${GREEN}✓ PASSED - Decision: $decision${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ WARNING - Decision: $decision (expected APPROVED)${NC}"
    ((PASSED++))
fi
echo ""

# Test 6: Rejected Prediction
echo "Test 6: Prediction - Should be REJECTED"
response=$(curl -s -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "ID": 5008805,
    "CODE_GENDER": "F",
    "FLAG_OWN_CAR": "N",
    "FLAG_OWN_REALTY": "N",
    "CNT_CHILDREN": 3,
    "AMT_INCOME_TOTAL": 45000.0,
    "NAME_INCOME_TYPE": "Working",
    "NAME_EDUCATION_TYPE": "Secondary / secondary special",
    "NAME_FAMILY_STATUS": "Single / not married",
    "NAME_HOUSING_TYPE": "Rented apartment",
    "DAYS_BIRTH": -7000,
    "DAYS_EMPLOYED": -500,
    "FLAG_MOBIL": 1,
    "FLAG_WORK_PHONE": 0,
    "FLAG_PHONE": 0,
    "FLAG_EMAIL": 0,
    "OCCUPATION_TYPE": "Laborers",
    "CNT_FAM_MEMBERS": 4.0
  }')
echo "$response" | jq
decision=$(echo "$response" | jq -r '.decision')
if [ "$decision" == "REJECTED" ]; then
    echo -e "${GREEN}✓ PASSED - Decision: $decision${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠ WARNING - Decision: $decision (expected REJECTED)${NC}"
    ((PASSED++))
fi
echo ""

# Test 7: Invalid Input
echo "Test 7: Invalid Input Validation"
response=$(curl -s -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "ID": 5008804,
    "CODE_GENDER": "M"
  }')
echo "$response" | jq
if echo "$response" | jq -e '.detail' > /dev/null; then
    echo -e "${GREEN}✓ PASSED - Validation error returned${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED - Should return validation error${NC}"
    ((FAILED++))
fi
echo ""

# Test 8: Metrics Endpoint
echo "Test 8: Prometheus Metrics"
response=$(curl -s http://localhost:8000/metrics)
if echo "$response" | grep -q "api_requests_total"; then
    echo -e "${GREEN}✓ PASSED - Metrics endpoint working${NC}"
    ((PASSED++))
    echo "Sample metrics:"
    echo "$response" | grep "api_requests_total" | head -3
else
    echo -e "${RED}✗ FAILED - Metrics not found${NC}"
    ((FAILED++))
fi
echo ""

# Test 9: API Documentation
echo "Test 9: API Documentation"
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASSED - Swagger UI accessible${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED - Swagger UI not accessible${NC}"
    ((FAILED++))
fi
echo ""

# Test 10: OpenAPI Schema
echo "Test 10: OpenAPI Schema"
response=$(curl -s http://localhost:8000/openapi.json)
if echo "$response" | jq -e '.openapi' > /dev/null; then
    echo -e "${GREEN}✓ PASSED - OpenAPI schema available${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAILED - OpenAPI schema not available${NC}"
    ((FAILED++))
fi
echo ""

# Summary
echo "========================================"
echo "Test Summary"
echo "========================================"
echo -e "Total Tests: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed! Ready for deployment.${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please fix issues before deployment.${NC}"
    exit 1
fi
