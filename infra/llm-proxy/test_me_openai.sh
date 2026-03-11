MODEL="claude-3-haiku-20240307"
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