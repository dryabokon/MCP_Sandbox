GEMINI_API_KEY=$(cat secret_key_gemini.txt)
MODEL="gemini-2.5-flash"
#----------------------------------------------------------------------------------------------------------------------
curl "https://generativelanguage.googleapis.com/v1beta/models/$MODEL:generateContent" \
  -H "Content-Type: application/json" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -d '{
    "contents": [
      {
        "parts": [
          {
            "text": "What is the capital of Ukraine? Answer in one short sentence."
          }
        ]
      }
    ]
  }'
