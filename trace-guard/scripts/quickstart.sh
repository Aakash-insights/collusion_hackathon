#!/bin/bash
# TraceGuard Quick Start.
#
# This project runs inside ControlArena's BashArena, which executes every task in a
# Docker container. That makes it the one project in this repository with an
# infrastructure prerequisite, so this script checks each one and STOPS at the first
# that is missing -- the smoke test itself takes about ten minutes and the full
# experiment 6-8 hours; nothing here should start until the cheap checks pass.
set -euo pipefail
cd "$(dirname "$0")/.."

fail() {
    echo ""
    echo "ERROR: $1"
    echo "       $2"
    exit 1
}

echo "=== TraceGuard Quick Start ==="
echo ""
echo "1. Prerequisites"
python -c "import control_arena" 2>/dev/null \
    || fail "control-arena is not installed." "Run: pip install -e .   (installs inspect-ai + control-arena, ~1 GB)"
python -c "import inspect_ai" 2>/dev/null \
    || fail "inspect-ai is not installed." "Run: pip install -e ."
docker info >/dev/null 2>&1 \
    || fail "Docker is not running." "Start Docker (Desktop or daemon) -- BashArena runs every task in a container -- then re-run."
[ -f .env ] \
    || fail ".env not found." "Run: cp .env.example .env   and put your OPENROUTER_API_KEY in it."
echo "   control-arena, inspect-ai, Docker, .env: OK"

echo ""
echo "2. Model access (seconds -- always before the ten-minute eval)"
python scripts/test_model_access.py \
    || fail "A configured model did not answer." "Check OPENROUTER_API_KEY in .env and the model ids printed above."

echo ""
echo "3. BashArena images"
docker image inspect bash-arena-logging-server:latest >/dev/null 2>&1 \
    || fail "BashArena images are not built yet." "Run once: control-arena env setup --env bash_arena   (builds several Docker images; needs a few GB and some minutes)"
echo "   BashArena images: OK"

echo ""
echo "4. Smoke test: 5 samples, TraceGuard monitor (~10 min, a few hundred model calls)"
python scripts/run_eval.py --limit 5 --monitor traceguard

echo ""
echo "=== Quick start complete ==="
echo "Next steps:"
echo "  - Full experiment (6-8 h):  python scripts/run_eval.py --all-monitors --limit 50"
echo "  - Analyze results:          python scripts/analyze_results.py --log-dir logs/"
echo "  - Post-hoc testing:         python scripts/run_posthoc.py --log-dir logs/ --all-monitors"
