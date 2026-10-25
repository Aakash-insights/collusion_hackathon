#!/usr/bin/env bash
# Ratio test, Qwen3-235B both sides via Bedrock shim (port 8765). Neutral opening: asks ~92, bids ~88. Seeds 0-2.
export LLM_BASE_URL=http://127.0.0.1:8765/v1 LLM_API_KEY=local
unset LLM_MODEL
Q=qwen.qwen3-235b-a22b-2507-v1:0
OV=qwen.qwen3-32b-v1:0
LOG=/tmp/claude-1000/-home-Aakash-discord-projects/8a60ad31-61f4-4bd0-b9ac-7e498e1b86ab/scratchpad/ratio_logs
mkdir -p "$LOG"
cd /home/Aakash/discord-projects/collusion_hackathon/llm-agent-collusion || exit 1
COMMON="--seller_models $Q --buyer_models $Q --initial_seller_ask_center 92 --initial_buyer_bid_center 88 --rounds 15"

run() {  # run <tag> <args...>
  local tag=$1; shift
  for s in 0 1 2; do
    echo "$(date +%T) start $tag seed$s"
    uv run python src/continuous_double_auction/simulation.py $COMMON "$@" --seeds "$s" --tag "R_${tag}-seed$s" -y \
      > "$LOG/${tag}-seed$s.log" 2>&1
    echo "$(date +%T) end   $tag seed$s exit=$?"
  done
}

( run 4v3_nochat   --sellers 4 --buyers 3 ) &
( run 4v3_chat     --sellers 4 --buyers 3 --seller_comms_enabled ) &
( run 4v3_overseer --sellers 4 --buyers 3 --seller_comms_enabled --oversight_enabled --overseer_model $OV ) &
( run 3v3_nochat   --sellers 3 --buyers 3
  run 3v3_chat     --sellers 3 --buyers 3 --seller_comms_enabled ) &
wait
echo "$(date +%T) ALL DONE"
