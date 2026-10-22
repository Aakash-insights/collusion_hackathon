# Code review ledger — PR #1 (Nebius + Modal integration)

Consolidated findings from three independent reviews of this PR (`main` `a0b85d2` → branch
`add-nebius-modal-integration`):

1. an internal multi-agent review of the PR diff,
2. **Francisco's** hands-on test of the *original `main`* branch, and
3. **marcobaumann's** prioritized review of the PR.

**Status legend:** ✅ FIXED (this review pass) · ☑️ FIXED earlier in the PR · ⚠️ OPEN · ◻️ DESIGN /
not-a-bug.

---

## 1. Data-correctness (can silently produce wrong results) — all FIXED

| # | Finding | Status | Fix |
|---|---|---|---|
| 1 | **`LLM_MODEL` in `compute.env` silently collapses multi-model experiments** (trace-guard trusted==untrusted, a-c-2/a-c rosters/judges) — `resolve_model` let it override every role with no notice | ✅ | `resolve_model` now announces the override once per requested id; `compute.env.example` rewritten with a WARNING; explicit warnings added to trace-guard, llm-agent-collusion, llm-agent-collusion-2 READMEs |
| 2 | **llm-trust-breaking runs JSON-incapable models and records empty data** ("…may parse as EMPTY. Proceeding.") | ✅ | fail loud: a stage whose decisions parse 100% empty now raises (wired into every decision-parse site); JSON-capable models still pass |
| 3 | **llm-cartel: a failed API call falls back to the monopoly price** → a failed run scores as perfect collusion | ✅ | exhausted retries now raise (`AgentCallError`); no monopoly-price substitution; run aborts loud |
| 4 | **trace-guard baseline monitors never see the agent's actions** (`BASELINE_PROMPT` had no `{task_description}`/`{tool_calls}`) — the likely cause of the README's "0% safety for single-score monitors" | ✅ | placeholders added; formatter supplies them |
| 5 | **trace-guard: a parse failure scored 5.0 and counted as "caught"** at thresholds ≤0.5 | ✅ | parse failure → abstain (NaN, `parse_failed=True`), excluded from the composite; all-abstain → non-triggering |
| 6 | **trace-guard `run_eval.py` printed "Completed!" / exit 0 even if every task crashed** | ✅ | inspects sample status; exits non-zero when no samples complete |

## 2. Wrong-provider / breaks-loudly / robustness — all FIXED

| Finding | Status | Fix |
|---|---|---|
| Custom/opt-in endpoints ignored (`ollama:`/`custom:` compute a `base_url` then call `make_client()` which ignores it) — focal-points, algorithmic-pricing, llm-cartel | ✅ | non-default presets now build a client with their own `base_url`/key (or `"EMPTY"`); default `openrouter` preset still routes via the shared config |
| `resolve_model` applied only to the default model, not to an explicit `--model` (algorithmic-pricing, llm-cartel) | ✅ | explicit model now routed through `resolve_model` too |
| `settings.py` crashes at **import** when no key is set (`api_key()` raises; dead `or` fallback) | ✅ | non-raising `config()["has_key"]` guard; project's own placeholder error owns the fail-loud |
| Modal/custom endpoint gets the Nebius/OpenRouter key as its bearer | ✅ | custom endpoint uses only `LLM_API_KEY` (or `"EMPTY"`) |
| a-c-2 `decide_challenge` still hard-raised (fix had only covered `choose_cards_to_play`) | ✅ | bounded graceful fallback (shape-verified against all callers) |
| a-c-2: bullet position deterministic; offer sometimes skipped; `allow_refusal` not enforced; collude prompt hardcoded models; invalid-move retry uninformative | ✅ | bullet randomized at game start; offer trigger `==`→`>=`; `allow_refusal` enforced; partner list from live roster; retry states what was invalid |
| collusive `manual_assist` referenced an undefined `error` (NameError on validation-failure path) | ✅ | `error` passed in; manual-assist now defaults **off** (it blocks on `input()`; failures already reprompt) |
| stego: `openai`/`gemini`/`groq` backends silently rerouted to the shared endpoint | ✅ | fail loud (both main + `release/code/` copies); verified no shipped config breaks |
| stego: run-IDs collide across configs → appended transcripts | ✅ | run-IDs/paths disambiguated per config |
| llm-cartel default judge (Qwen3-14B, thinking-off) doesn't work on OpenRouter | ✅ | default judge → `Qwen/Qwen2.5-7B-Instruct` (non-reasoning) |
| `queued_openrouter.py` caught every exception and fell back to OpenRouter | ✅ | except narrowed to `ImportError` |
| Bare `load_dotenv()` could let a stray local `.env` shadow `compute.env` (colosseum, llm-cartel, focal-points, algorithmic-pricing, llm-trust-breaking) | ✅ | `override=False` everywhere |
| focal-points client had no `timeout`/`max_retries` | ✅ | added |
| Hardcoded `openrouter.ai` rate links when the endpoint is Nebius (focal, cartel, colosseum) | ✅ | endpoint-aware via `endpoint_kind()` |
| OpenRouter-cased model ids in project code (llm-cartel) | ✅ | rewritten in Nebius/HF casing |
| colosseum param name `llm_config` shadowed the imported module | ✅ | renamed to `llm_cfg` |
| stale `.env.example` references in trace-guard script output | ✅ | point at the repo-root `compute.env` |
| stego: torch a direct (~5 GB) dependency | ✅ | moved to `requirements-local.txt` |

## 3. Still open

| Finding | Status | Note |
|---|---|---|
| llm-trust-breaking `trial_runner.py:150` `_execute_parallel` appears to call itself recursively | ⚠️ | **newly surfaced**, pre-existing, out of this review's scope; the `--use-queue` smoke passes, so it may be an unused/shadowed path — needs a separate look |
| a-c-2 Liar's Bar: a player who *accepts* but names no valid partner isn't force-enrolled when `allow_refusal=False` | ⚠️ | minor residual edge case |
| stego: shipped results don't byte-reproduce; benchmark is near-trivial (dishonest-word leakage) | ⚠️ | research-data / benchmark-design concerns, out of integration scope |

## 4. Design decisions (not bugs)

- **Closed default models** (colosseum `gpt-4o-mini`, llm-trust-breaking `gpt-4o-mini`, trace-guard GPT-4o)
  fail on a Nebius-only setup — kept paper-faithful and documented; they need `OPENROUTER_API_KEY`. (An
  onboarding error, not wrong data.)
- **Weak default models** (Francisco's Haiku-5.5 suggestion): not adopted; paper defaults kept.
- **Retired-pin / OpenRouter-alias upgrades** (`llm_config.py`): announced same-lineage version upgrades,
  intentional and printed — not silent substitutions.
- **Research observations** (thesis super-Nash claim doesn't replicate; neutral framing reduces lying):
  starter-project material, not defects.

## 5. Scope note

This PR grew beyond "Nebius + Modal integration" into a broad hardening pass (bug fixes across the
experiment logic). That was a deliberate call to make the experiments correct for participants; the
reviewer rightly flagged it as scope creep. Cosmetic items intentionally left for later: the pervasive
"openrouter"-means-Nebius naming, some duplicated `_FATAL`/auth wrappers, and `trace-guard`'s
`ruff target-version = py310` vs `requires-python = py312`.
