#!/usr/bin/env bash
# Qwen-only experiment matrix via the Bedrock shim (port 8766). 3 sellers, 3 buyers, 15 rounds, seeds 0-2.
# Q = Qwen3-235B-A22B-2507 (strong), S = Qwen3-32B (weaker). Default opening: asks ~97.5, bids ~82.5.
# Already on disk (reused, same model/shim): Q vs Q, open 97.5, comms on (A_baseline_llmbuyers) / off (N0_nocomms_llm).
export LLM_BASE_URL=http://127.0.0.1:8766/v1 LLM_API_KEY=local
unset LLM_MODEL
Q=qwen.qwen3-235b-a22b-2507-v1:0
S=qwen.qwen3-32b-v1:0
LOG=/tmp/claude-1000/-home-Aakash-discord-projects/8a60ad31-61f4-4bd0-b9ac-7e498e1b86ab/scratchpad/matrix_logs
mkdir -p "$LOG"
cd /home/Aakash/discord-projects/collusion_hackathon/llm-agent-collusion || exit 1

run() {  # run <tag> <args...>: one process per seed so a crash only loses that seed
  local tag=$1; shift
  for s in 0 1 2; do
    echo "$(date +%T) start $tag seed$s"
    uv run python src/continuous_double_auction/simulation.py "$@" --seeds "$s" --tag "M_${tag}-seed$s" -y \
      > "$LOG/${tag}-seed$s.log" 2>&1
    echo "$(date +%T) end   $tag seed$s exit=$?"
  done
}

# bid-anchor test: Q vs Q, seller comms on, sellers open ~97.5 (default), buyers open higher
( run QQ_bids90_comms --seller_models $Q --buyer_models $Q --seller_comms_enabled --initial_buyer_bid_center 90 ) &
( run QQ_bids95_comms --seller_models $Q --buyer_models $Q --seller_comms_enabled --initial_buyer_bid_center 95 ) &
( run QQ_bids95_nocomms --seller_models $Q --buyer_models $Q --initial_buyer_bid_center 95 ) &
wait
echo "$(date +%T) ALL DONE"
