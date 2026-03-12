OPENAI_API_KEY=$(cat secret_key_openai.txt)
container_name='llm-proxy'
docker stop $container_name 2>/dev/null || true
docker rm $container_name 2>/dev/null || true

docker run -d \
  --name $container_name \
  --restart unless-stopped \
  -p 8082:8082 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e PREFERRED_PROVIDER=openai \
  -e BIG_MODEL=gpt-4o \
  -e SMALL_MODEL=gpt-4o-mini \
  ghcr.io/1rgs/claude-code-proxy:main

echo "Waiting for venv to initialize..."
sleep 20


echo "Started $container_name"