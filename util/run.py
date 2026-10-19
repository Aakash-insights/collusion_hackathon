"""Run an experiment with a chosen model, routing inference to where that model actually exists —
and NEVER substituting a different model:

  * Nebius serves the model                         -> run on Nebius
  * Nebius doesn't, but it's self-hostable (open)   -> boot it on Modal for this run, then tear down
  * closed model with no provider (e.g. openai/*)   -> FAIL LOUDLY (pick an available model)

Identification is a catalog lookup: `llm_config.nebius_serves(model)` checks Nebius's `GET /v1/models`.

    python -m util.run --model <id> -- <experiment command>

e.g.
    python -m util.run --model Qwen/Qwen2.5-7B-Instruct -- \
        bash -c "cd colosseum && uv run python -m experiments.collusion.run --config ..."
"""
import os
import sys
import argparse
import subprocess
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))  # util/ on path
import llm_config

# Closed / provider-only families we can't self-host on Modal (vLLM serves open weights only).
_CLOSED_PREFIXES = ("openai/", "gpt-", "o1", "o3", "o4", "gemini", "google/", "anthropic/", "claude")


def _self_hostable(model_id):
    m = model_id.lower()
    return not any(m.startswith(p) for p in _CLOSED_PREFIXES)


def main():
    ap = argparse.ArgumentParser(description="Run an experiment, routing its model to Nebius or Modal (never substituted).")
    ap.add_argument("--model", required=True, help="exact model id you want to run")
    ap.add_argument("--gpu", default=None, help="Modal GPU if it has to self-host, e.g. A10G / A100-40GB / H100")
    ap.add_argument("cmd", nargs=argparse.REMAINDER, help="the experiment command, after `--`")
    args = ap.parse_args()
    cmd = args.cmd[1:] if args.cmd and args.cmd[0] == "--" else args.cmd
    if not cmd:
        ap.error("provide a command after `--`, e.g.  -- bash -c 'cd proj && python ...'")

    model = llm_config.resolve_model(args.model)   # same-model id normalization only; never a swap
    served = llm_config.nebius_serves(model)

    if served is True:
        print(f"[run] Nebius serves '{model}' — running on Nebius.", flush=True)
        env = {**os.environ, "LLM_MODEL": model}
        sys.exit(subprocess.run(cmd, env=env).returncode)

    if served is False:
        if not _self_hostable(model):
            sys.exit(f"[run] ERROR: '{model}' is not served by Nebius and is a closed model that cannot be "
                     f"self-hosted on Modal. Choose an open model (or a provider that serves it). "
                     f"Not substituting another model.")
        print(f"[run] '{model}' is not on Nebius — hosting it on Modal for this run.", flush=True)
        import hosted_model
        with hosted_model.hosted_model(model=model, gpu=args.gpu):
            sys.exit(subprocess.run(cmd, env=os.environ).returncode)

    # served is None: couldn't reach the Nebius catalog. Don't guess — try Nebius and let the actual
    # inference call fail loudly if the model really isn't there (still no substitution).
    print("[run] WARNING: couldn't verify the Nebius catalog (check NEBIUS_API_KEY / network). "
          "Trying Nebius; it will fail loudly if the model isn't served.", flush=True)
    env = {**os.environ, "LLM_MODEL": model}
    sys.exit(subprocess.run(cmd, env=env).returncode)


if __name__ == "__main__":
    main()
