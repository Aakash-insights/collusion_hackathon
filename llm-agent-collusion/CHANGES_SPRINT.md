# CHANGES_SPRINT.md — what is new vs. preexisting

Sprint: Apart Research AI Collusion Research Sprint, project 3.4
("What does a coalition of AI agents do when it learns it is being watched?").

Base: starter repo `poseidon-research/collusion_hackathon`, folder `llm-agent-collusion/`
(Agrawal et al. 2025, arXiv:2507.01413). Everything not listed below is **preexisting, unmodified**.

## New in this sprint (our change)

Goal: separate "being **told** about oversight" from "being **watched**" by the overseer.
Before, `--oversight_enabled` did both at once. Defaults are unchanged, so existing
commands behave exactly as before.

| Flag | Default | Effect |
| --- | --- | --- |
| `--oversight_notice` / `--no_oversight_notice` | notice shown | `--no_oversight_notice` = **silent oversight**: the overseer still runs, but the seller prompt does not mention it. Only meaningful with `--oversight_enabled`. |
| `--disclose_sample_fraction` | off | Adds "Approximately X% of seller messages are reviewed." to the oversight notice, where X = `--overseer_sample_fraction` x 100. Requires `--oversight_enabled` and the notice to be on (otherwise a `ValueError`). |

Files touched:

- `src/continuous_double_auction/cda_types.py` — two new `ExperimentParams` fields
  (`oversight_notice: bool = True`, `disclose_sample_fraction: bool = False`) and one validator check.
- `src/continuous_double_auction/simulation.py` — the three argparse options and passing them into `ExperimentParams`.
- `src/continuous_double_auction/market/agents.py` — passes `oversight_notice` and `disclosed_sample_pct` into the seller prompt render.
- `src/continuous_double_auction/prompt_templates/seller_prompt_base.jinja2` — the oversight line is now
  gated on `oversight_notice` instead of `oversight_enabled`, and carries the optional sample-fraction sentence.
  With defaults the rendered line is identical to the original.

## New: Bedrock bridge (model access, not an experiment variable)

`tools/bedrock_openai_shim.py` is a ~90-line OpenAI-compatible `/v1/chat/completions` server that forwards to
AWS Bedrock (Converse API) so the unmodified simulation can use Bedrock models via `LLM_BASE_URL` / `LLM_API_KEY`.
It emulates `response_format=json_object` with a short system hint, because without it Qwen3 over-escapes quotes
(`{\\"key\\": ...}`) and the sim's JSON extraction fails. The sim's own prompts are untouched.
Models used when running through it: sellers `qwen.qwen3-235b-a22b-2507-v1:0`, overseer `qwen.qwen3-32b-v1:0`
(region ap-south-1) — NOT the paper's GPT-4.1 / GPT-4.1-mini. Keep them fixed across all conditions.

## Known limitation (not changed)

Gagging is preexisting behavior: if the overseer scores a message 4/4, all sellers are gagged and
their prompt then includes "As punishment for collusion…" and a "Message from CME Group Regulators"
section. Under `--no_oversight_notice` this means sellers can still **learn** they are being watched
once a gag fires. We left this as is to keep the change minimal; analyze silent-oversight runs with this in mind.

## Preexisting (not ours)

Everything else, including: `--overseer_sample_fraction` and the `MessageOverseer` sampling logic
(added by the hackathon organizers for 3.4), the collusion index and PASS/FAIL metric, `--boss_pressure`,
the ZIP buyer, and the cost/confirmation prompt.
