GEMINI_API_KEY=$(cat secret_key_gemini.txt)
container_name='claude-gemini-proxy'

PATCH_PY='
import os, time

path = "/claude-code-proxy/.venv/lib/python3.10/site-packages/litellm/llms/vertex_ai/common_utils.py"
for _ in range(30):
    if os.path.exists(path):
        break
    time.sleep(2)

code = open(path).read()

# Patch 1: len(anyof) != 2 raises instead of skipping
old1 = """        if len(anyof) != 2:
            raise ValueError(
                \"Invalid input: Type Unions are not supported, except for `Optional` types. \"
                \"Please provide an `Optional` type or a non-Union type.\"
            )"""
new1 = """        if len(anyof) != 2:
            return  # skip unsupported Union types"""

# Patch 2: non-null union raises instead of best-effort
old2 = """        else:
            raise ValueError(
                \"Invalid input: Type Unions are not supported, except for `Optional` types. \"
                \"Please provide an `Optional` type or a non-Union type.\"
            )"""
new2 = """        else:
            schema.update(a)  # best-effort: use first type for unsupported unions"""

# Patch 3: strip unsupported JSON Schema keywords (propertyNames etc)
old3 = "def convert_to_nullable(schema):\n    anyof = schema.pop(\"anyOf\", None)"
new3 = """def convert_to_nullable(schema):
    for unsupported in [\"propertyNames\", \"unevaluatedProperties\", \"if\", \"then\", \"else\", \"not\", \"contains\"]:
        schema.pop(unsupported, None)
    anyof = schema.pop(\"anyOf\", None)"""

code = code.replace(old1, new1).replace(old2, new2).replace(old3, new3)
open(path, "w").write(code)
print("litellm patched (3 patches applied)")
'

docker stop $container_name 2>/dev/null || true
docker rm $container_name 2>/dev/null || true

docker run -d \
  --name $container_name \
  --restart unless-stopped \
  -p 8082:8082 \
  -e GEMINI_API_KEY=$GEMINI_API_KEY \
  -e OPENAI_API_KEY=dummy \
  -e PREFERRED_PROVIDER=google \
  -e BIG_MODEL=gemini-2.5-flash \
  -e SMALL_MODEL=gemini-2.5-flash \
  ghcr.io/1rgs/claude-code-proxy:main

echo "Waiting for venv to initialize..."
sleep 20

docker exec $container_name python3 -c "$PATCH_PY"
echo "Started $container_name (patched)"