#!/usr/bin/env bash
# Friend's main condition (barhoz10, branch "results", SUMMARY.md section 1), with the seller swapped:
#   gpt-4.1 sellers -> qwen/qwen3-235b-a22b-2507 sellers
#   3 sellers, 3 gpt-4.1-mini buyers, 15 rounds, comms on, no overseer, temperature 0.7 (defaults),
#   seeds 0-4 (same seeds => same random opening asks/bids as his GPT-4.1 runs).
# One process per seed so a crash in one seed (e.g. an OpenRouter 402) does not abort the others.
LOGDIR=/tmp/claude-1000/-home-Aakash-discord-projects/8a60ad31-61f4-4bd0-b9ac-7e498e1b86ab/scratchpad/qwen235b_logs
mkdir -p "$LOGDIR"
cd /home/Aakash/discord-projects/collusion_hackathon/llm-agent-collusion || exit 1
for s in 0 1 2 3 4; do
  echo "=== seed $s start $(date +%T) ==="
  uv run python src/continuous_double_auction/simulation.py \
    --seller_models qwen/qwen3-235b-a22b-2507 \
    --buyer_models gpt-4.1-mini \
    --seller_comms_enabled \
    --rounds 15 \
    --seeds "$s" \
    --tag qwen235b_main \
    -y > "$LOGDIR/seed$s.log" 2>&1
  echo "=== seed $s exit code $? at $(date +%T) ==="
done
echo "=== ALL SEEDS DONE ==="
