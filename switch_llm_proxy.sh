#!/usr/bin/env bash
#----------------------------------------------------------------------------------------------------------------------
if [ -z "$1" ]; then
	arg="off"
else
	arg="$1"
fi
#----------------------------------------------------------------------------------------------------------------------
if [ "$arg" == "on" ]; then

  PROVIDER="$(docker exec llm-proxy /bin/sh -lc 'printf "%s" "${PREFERRED_PROVIDER:-unknown}"')"
  MODEL="$(docker exec llm-proxy /bin/sh -lc 'printf "%s" "${SMALL_MODEL:-${BIG_MODEL:-}}"')"

  if [ -z "$MODEL" ]; then
    echo "Could not detect model from llm-proxy container"
    exit 1
  fi
  export ANTHROPIC_API_KEY=dummy
  export ANTHROPIC_BASE_URL=http://localhost:8082
  export ANTHROPIC_MODEL=claude-sonnet-4-5
  echo "Switched to $MODEL from $PROVIDER"
else
  unset ANTHROPIC_API_KEY ANTHROPIC_BASE_URL ANTHROPIC_MODEL
  echo "switched to ANTHROPIC model"
fi

echo "---------------------------------------------------"
echo 'ensure correct execution of this script should be'
echo "source ./switch_llm_proxy.sh $1"
echo "---------------------------------------------------"