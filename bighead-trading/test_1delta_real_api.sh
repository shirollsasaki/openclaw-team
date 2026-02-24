#!/bin/bash

API_KEY="ag_I0gGHlzynlrwYqFIZgy_yhOLzHbC8iAtNOGbsNkF"
BASE_URL="https://portal.1delta.io"

echo "Testing 1Delta API endpoints..."
echo "================================"
echo ""

# Try different paths
endpoints=(
    "/data"
    "/api/data"
    "/lending"
    "/api/lending"
    "/markets"
    "/api/markets"
    "/rates"
    "/api/rates"
    "/v1/data"
    "/v1/lending"
    "/v1/markets"
    "/health"
    "/"
)

for endpoint in "${endpoints[@]}"; do
    echo "Testing: $BASE_URL$endpoint"
    response=$(curl -s "$BASE_URL$endpoint" -H "x-api-key: $API_KEY")
    echo "Response: ${response:0:200}"
    echo ""
    sleep 0.5
done
