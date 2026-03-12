#!/usr/bin/env bash
#----------------------------------------------------------------------------------------------------------------------
MODEL="${1:-$(docker exec llm-proxy /bin/sh -lc 'printf "%s" "${SMALL_MODEL:-${BIG_MODEL:-}}"' )}"
PROVIDER="$(docker exec llm-proxy /bin/sh -lc 'printf "%s" "${PREFERRED_PROVIDER:-unknown}"')"
#----------------------------------------------------------------------------------------------------------------------
if [ -z "$MODEL" ]; then
  echo "Could not detect model from llm-proxy container"
  exit 1
fi
#----------------------------------------------------------------------------------------------------------------------
echo "Testing $MODEL from $PROVIDER"
#----------------------------------------------------------------------------------------------------------------------
curl -s http://localhost:8082/v1/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy" \
  -d '{
    "model": "'"$MODEL"'",
    "max_tokens": 64,
    "messages": [
      {
        "role": "user",
        "content": "What is the capital of Ukraine? Answer in one short sentence."
      }
    ],
    "temperature": 0
  }'

echo ""