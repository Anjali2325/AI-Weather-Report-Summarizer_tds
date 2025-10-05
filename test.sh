#!/bin/bash

# Test script for AI Weather Report Summarizer
# Tests weather summaries for major Indian cities

BASE_URL="http://localhost:8000"
ENDPOINT="/weather-summary"

echo "🌤️  AI Weather Report Summarizer - City Tests"
echo "=============================================="
echo ""

# Function to test a city
test_city() {
    local city_name=$1
    local latitude=$2
    local longitude=$3
    
    echo "🏙️  Testing: $city_name"
    echo "📍 Coordinates: $latitude, $longitude"
    echo "🔄 Making request..."
    
    response=$(curl -s -X POST "$BASE_URL$ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "{\"latitude\": $latitude, \"longitude\": $longitude}")
    
    # Check if curl was successful
    if [ $? -eq 0 ]; then
        echo "✅ Response received:"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    else
        echo "❌ Failed to get response"
    fi
    
    echo ""
    echo "----------------------------------------"
    echo ""
}

# Check if server is running
echo "🔍 Checking if server is running at $BASE_URL..."
health_check=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/")

if [ "$health_check" != "200" ]; then
    echo "❌ Server is not running at $BASE_URL"
    echo "Please start the server first with: python app.py"
    exit 1
fi

echo "✅ Server is running!"
echo ""

# Test each city
echo "Starting city tests..."
echo ""

# Delhi - Capital of India
test_city "Delhi" 28.6139 77.2090

# Mumbai - Financial capital
test_city "Mumbai" 19.0760 72.8777

# Hyderabad - IT hub
test_city "Hyderabad" 17.3850 78.4867

# Chennai - South Indian metro
test_city "Chennai" 13.0827 80.2707

# Amritsar - Golden Temple city
test_city "Amritsar" 31.6340 74.8723

echo "🎉 All city tests completed!"
echo ""

# Test invalid coordinates
echo "🧪 Testing error handling with invalid coordinates..."
echo ""

echo "Testing invalid latitude (>90):"
curl -s -X POST "$BASE_URL$ENDPOINT" \
    -H "Content-Type: application/json" \
    -d '{"latitude": 91.0, "longitude": 77.2090}' | python3 -m json.tool 2>/dev/null

echo ""
echo "Testing invalid longitude (<-180):"
curl -s -X POST "$BASE_URL$ENDPOINT" \
    -H "Content-Type: application/json" \
    -d '{"latitude": 28.6139, "longitude": -181.0}' | python3 -m json.tool 2>/dev/null

echo ""
echo "✅ Error handling tests completed!"