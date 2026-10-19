"""Bring a Modal-hosted model UP for the duration of an experiment, then tear it DOWN.

This wraps the manual "deploy a model, paste its URL into compute.env, remember to stop it" flow into
one lifecycle. It runs `util/modal_serve.py` as an **ephemeral** Modal app (`app.run()`), points
`llm_config` at the temporary endpoint, waits until the model is ready, runs your experiment, and
stops the app on exit — so you never leave a GPU (and credits) running.

Use when an experiment can't use Nebius inference and you want a model on Modal just for this run.

----------------------------------------------------------------------------------------------------
CLI — wrap any command:
    python -m util.hosted_model --model Qwen/Qwen2.5-7B-Instruct --gpu A10G -- \
        bash -c "cd llm-trust-breaking && python experiments/run_endogenous.py --game diners ..."

In your own Python:
    from hosted_model import hosted_model            # (util/ on sys.path via the usual bootstrap)
    with hosted_model(model="Qwen/Qwen2.5-7B-Instruct"):
        ...  # llm_config now points at the Modal endpoint; run your code
    # endpoint is torn down here

Prereqs: `pip install modal` + `modal setup` (browser auth). Gated models need a HF token secret.
Scaffolding ahead of live credits — validate once your Modal account is funded.
"""
import os
import sys
import time
import json
import argparse
import contextlib
import subprocess
import urllib.request
import urllib.error
import pathlib

# make util/ importable whether run as `python -m util.hosted_model` or `python util/hosted_model.py`
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))


def _wait_ready(url, api_key, timeout):
    """Poll the endpoint until vLLM has loaded the model (first hit triggers the cold start)."""
    deadline = time.time() + timeout
    req = urllib.request.Request(url.rstrip("/") + "/v1/models")
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")
    last = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                if r.status == 200:
                    return True
        except Exception as e:  # noqa: BLE001 - cold start returns connection errors / 503s
            last = e
        time.sleep(5)
    raise TimeoutError(f"Modal model endpoint not ready after {timeout}s (last: {last})")


@contextlib.contextmanager
def hosted_model(model=None, gpu=None, api_key=None, ready_timeout=900):
    """Context manager: ephemeral Modal model up -> llm_config pointed at it -> torn down on exit."""
    # modal_serve reads these at import, so set them before importing it.
    if model:
        os.environ["MODAL_SERVE_MODEL"] = model
    if gpu:
        os.environ["MODAL_SERVE_GPU"] = gpu
    if api_key:
        os.environ["MODAL_SERVE_API_KEY"] = api_key

    import modal
    import modal_serve  # util/modal_serve.py (util/ is on sys.path above)

    served_model = os.environ.get("MODAL_SERVE_MODEL", modal_serve.MODEL)
    saved = {k: os.environ.get(k) for k in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL")}
    with modal.enable_output(), modal_serve.app.run():
        url = modal_serve.serve.get_web_url()
        os.environ["LLM_BASE_URL"] = url.rstrip("/") + "/v1"
        if api_key:
            os.environ["LLM_API_KEY"] = api_key
        os.environ["LLM_MODEL"] = served_model
        print(f"[hosted_model] up: {os.environ['LLM_BASE_URL']}  (model {served_model}) — warming up...", flush=True)
        _wait_ready(url, api_key, ready_timeout)
        print("[hosted_model] ready.", flush=True)
        try:
            yield url
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
            print("[hosted_model] torn down.", flush=True)  # app.run() exit stops the ephemeral app


def main():
    ap = argparse.ArgumentParser(description="Run a command with a Modal-hosted model up for its duration.")
    ap.add_argument("--model", default=None, help="model id to serve (default: modal_serve.py's default)")
    ap.add_argument("--gpu", default=None, help="Modal GPU, e.g. A10G / A100-40GB / H100")
    ap.add_argument("--api-key", default=None, help="bearer key to require on the endpoint (optional)")
    ap.add_argument("--ready-timeout", type=int, default=900)
    ap.add_argument("cmd", nargs=argparse.REMAINDER,
                    help="the experiment command, after `--` (e.g. -- bash -c '...')")
    args = ap.parse_args()
    cmd = args.cmd[1:] if args.cmd and args.cmd[0] == "--" else args.cmd
    if not cmd:
        ap.error("provide a command after `--`, e.g.  -- bash -c 'cd proj && python ...'")
    with hosted_model(model=args.model, gpu=args.gpu, api_key=args.api_key, ready_timeout=args.ready_timeout):
        rc = subprocess.run(cmd, env=os.environ).returncode
    sys.exit(rc)


if __name__ == "__main__":
    main()
