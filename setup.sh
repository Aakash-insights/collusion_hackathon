#!/usr/bin/env bash
#
# One-shot setup for every experiment in this repo.
#
# Installs the shared compute layer (poseidon_compute, in ./util) and sets up each experiment's
# environment, so every experiment can `from poseidon_compute import ...` and route inference through
# the one shared `compute.env`.
#
#   ./setup.sh                 # set up ALL experiments
#   ./setup.sh focal-points    # set up only the named experiment(s)
#
# Per experiment:
#   * uv project   (has pyproject.toml)  ->  `uv sync`   (installs poseidon-compute via [tool.uv.sources])
#   * pip project  (requirements.txt)    ->  a local .venv + `pip install -r requirements.txt`
#                                            (its `-e ../util` line installs poseidon-compute)
#
# Nothing here needs a GPU or any key — it only installs. Put your keys in compute.env afterwards.

set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

bold=$(printf '\033[1m'); green=$(printf '\033[32m'); red=$(printf '\033[31m')
yellow=$(printf '\033[33m'); dim=$(printf '\033[2m'); rst=$(printf '\033[0m')
ok()   { printf "  ${green}✅ %s${rst}\n" "$*"; }
bad()  { printf "  ${red}❌ %s${rst}\n" "$*"; }
warn() { printf "  ${yellow}⚠  %s${rst}\n" "$*"; }
info() { printf "  ${dim}%s${rst}\n" "$*"; }

PASS=(); FAIL=()

# --- prerequisites --------------------------------------------------------------------------------
have() { command -v "$1" >/dev/null 2>&1; }

if ! have python3; then
  bad "python3 not found — install Python 3.9+ and re-run."; exit 1
fi

HAVE_UV=1
if ! have uv; then
  HAVE_UV=0
  warn "uv not found. uv-based experiments will be skipped."
  info "Install uv:  curl -LsSf https://astral.sh/uv/install.sh | sh    (then re-run ./setup.sh)"
fi

# --- compute.env ----------------------------------------------------------------------------------
if [ ! -f "$ROOT/compute.env" ]; then
  if [ -f "$ROOT/compute.env.example" ]; then
    cp "$ROOT/compute.env.example" "$ROOT/compute.env"
    warn "Created compute.env from compute.env.example — open it and add your NEBIUS_API_KEY and/or OPENROUTER_API_KEY."
  else
    warn "No compute.env (and no example to copy). Create one with NEBIUS_API_KEY / OPENROUTER_API_KEY before running experiments."
  fi
else
  ok "compute.env present"
fi

# --- shared package into a repo-root venv (gives you the `poseidon-run` entry point) ---------------
printf "\n${bold}Shared compute layer (poseidon_compute)${rst}\n"
if [ "$HAVE_UV" = "1" ]; then
  if uv venv "$ROOT/.venv" >/dev/null 2>&1 && uv pip install --python "$ROOT/.venv" -e "$ROOT/util" >/dev/null 2>&1; then
    ok "installed into ./.venv  —  run the entry point with:  ./.venv/bin/poseidon-run --model <id> -- <cmd>"
  else
    bad "failed to install poseidon-compute into ./.venv"; FAIL+=("poseidon-compute (root .venv)")
  fi
else
  if python3 -m venv "$ROOT/.venv" && "$ROOT/.venv/bin/python" -m pip install -q -U pip >/dev/null 2>&1 \
     && "$ROOT/.venv/bin/python" -m pip install -q -e "$ROOT/util" >/dev/null 2>&1; then
    ok "installed into ./.venv  —  run the entry point with:  ./.venv/bin/poseidon-run --model <id> -- <cmd>"
  else
    bad "failed to install poseidon-compute into ./.venv"; FAIL+=("poseidon-compute (root .venv)")
  fi
fi

# --- discover experiments -------------------------------------------------------------------------
# An experiment is a direct subdir with a pyproject.toml (uv) or a requirements.txt (pip), excluding util.
discover() {
  for d in */; do
    d="${d%/}"
    [ "$d" = "util" ] && continue
    if [ -f "$d/pyproject.toml" ] || [ -f "$d/requirements.txt" ]; then echo "$d"; fi
  done
}

if [ "$#" -gt 0 ]; then
  EXPERIMENTS=("$@")
else
  EXPERIMENTS=()
  while IFS= read -r _line; do EXPERIMENTS+=("$_line"); done < <(discover)
fi

setup_one() {
  local d="$1"
  if [ ! -d "$d" ]; then bad "$d — no such directory"; FAIL+=("$d"); return; fi
  printf "\n${bold}%s${rst}\n" "$d"
  if [ -f "$d/pyproject.toml" ]; then
    if [ "$HAVE_UV" = "0" ]; then warn "$d — uv project, but uv is not installed; skipping"; FAIL+=("$d (needs uv)"); return; fi
    if ( cd "$d" && uv sync ); then ok "$d — uv sync"; PASS+=("$d"); else bad "$d — uv sync failed"; FAIL+=("$d"); fi
  elif [ -f "$d/requirements.txt" ]; then
    if ( cd "$d" \
         && python3 -m venv .venv \
         && ./.venv/bin/python -m pip install -q -U pip \
         && ./.venv/bin/python -m pip install -r requirements.txt ); then
      ok "$d — .venv + requirements.txt (incl. poseidon-compute)"; PASS+=("$d")
    else
      bad "$d — pip install failed"; FAIL+=("$d")
    fi
  else
    warn "$d — no pyproject.toml or requirements.txt; nothing to do"
  fi
}

for d in "${EXPERIMENTS[@]}"; do setup_one "$d"; done

# --- summary --------------------------------------------------------------------------------------
printf "\n${bold}Summary${rst}\n"
printf "  ${green}%d ok${rst}" "${#PASS[@]}"; [ "${#FAIL[@]}" -gt 0 ] && printf "   ${red}%d failed${rst}" "${#FAIL[@]}"; printf "\n"
if [ "${#FAIL[@]}" -gt 0 ]; then
  for f in "${FAIL[@]}"; do info "failed: $f"; done
  printf "\n${yellow}Some setups failed — see the logs above.${rst}\n"
  exit 1
fi
printf "\n${green}All set.${rst} Put your keys in ${bold}compute.env${rst}, then run any experiment (see its README).\n"
