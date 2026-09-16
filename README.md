# Hackathon NY starter repo

Six research codebases on LLM agents, collusion and multi-agent coordination, bundled
so a team can clone once and start hacking. Each project has been adapted to run on a
laptop with **no GPU**, through OpenRouter with a single API key.

## The projects

### 1. [`algorithmic-pricing-llms/`](algorithmic-pricing-llms/)

**Question:** when LLM agents set prices against each other in a repeated market, do they
tacitly collude, and does collusion break down as the number of firms grows?

Two to five LLM "firms" play 300 rounds of a Calvano (2020) pricing game. Each round every
firm sees its history and picks a price; the market returns quantities and profits. The
thesis found prices well above the competitive (Nash) level that fall by about 3.7% per
extra competitor. Sprint project 1.2: verify the positive control, then ablate one
variable at a time (visible history, persistent notes, shuffled names, temperature) via
CLI flags, through OpenRouter (default `mistralai/mistral-large-2512`; the thesis's
`mistral-large-2411` is no longer served).

```bash
cd algorithmic-pricing-llms && uv sync && cp .env.example .env   # add OPENROUTER_API_KEY
uv run python experiments_synthetic/duopoly.py --rounds 30          # ~60 calls
```

### 2. [`llm-cartel/`](llm-cartel/)

**Question:** do *reasoning* models collude in a Bertrand price game, and can you steer
that behaviour on or off inside the model's activations?

Companion code to an ICML 2026 position paper arguing that collusion risk justifies
certification of AI agents making market decisions. Two or three agents play Bertrand
competition under different system prompts (neutral, implicit and explicit nudges to
collude, anti-collusion warnings), with LLM judges scoring the transcripts. The
"steering" part trains contrastive activation vectors and injects them into open models
served with vLLM (GPU, untouched here). Sprint projects 1.2 and 1.4: a CPU-only harness
runs the same game through OpenRouter with prompt / monitoring / window / temperature
flags, adds checkpoint branching to swap a participant mid-run, and an API-based judge. The
paper's R1 distills are no longer on OpenRouter, so you pick the agent model: full R1 for
fidelity (~2-3 min per call), `qwen/qwen3-14b` (thinks, ~1 min per call) or `openai/gpt-4.1-mini` for fast iteration.

```bash
cd llm-cartel && uv sync && cp .env.example .env     # add OPENROUTER_API_KEY
uv run python run_game.py --models openai/gpt-4.1-mini --rounds 30   # ~60 calls, ~1 min
```

### 3. [`focal-points/`](focal-points/)

**Question:** do LLMs pick the same "obvious" answers humans do in coordination games,
and can they use those focal points to bargain?

Schelling-style coordination problems ("name a number", "pick a place to meet") and the
Bardsley Amsterdam / Nottingham pick-guess-coordinate tasks are posed to a model, tens of
answers are sampled per prompt, and a coordination index (how often two answers agree)
is compared with the human data. In the sprint this is the cheap **benign** control:
agreement without any communication, for calibrating detectors (2.1), for testing
whether a replacement agent recovers a convention (1.4), or as the convention task for
swap detection (3.2). The original ran 70B models locally on GPUs plus OpenAI / Gemini
batch jobs; it now calls OpenRouter (default: the paper's Llama-3.3-70B), with samples,
temperature, seed and prompt count as flags. The 1.8 GB of raw transcripts were removed
from this copy; prompt datasets, human baselines and the paper's aggregated results stay.

```bash
cd focal-points && uv sync && cp .env.example .env     # add OPENROUTER_API_KEY
uv run python main.py --max-prompts 3 -s 5             # 15 calls
```

### 4. [`llm-agent-collusion/`](llm-agent-collusion/)

**Question:** in a continuous double auction with several LLM sellers and buyers, do the
sellers coordinate to keep prices high, and what makes it more or less likely?

Paper: *Evaluating LLM Agent Collusion in Double Auctions* (2025). LLM sellers and buyers,
each with a private valuation, post asks and bids for one lot per hour in a continuous
double auction; the code varies seller communication, an overseer that can gag sellers,
message caps, CEO pressure, temperature and the model mix, and measures how far prices sit
above the competitive level. Sprint projects 2.1, 2.2, 3.3 and 3.4: all calls go through
OpenRouter (paper default `gpt-4.1` → `openai/gpt-4.1`), defaults are the brief's 3 sellers,
3 buyers, 15 rounds, and a new `--overseer_sample_fraction` exposes 25/50/100 % of messages
to the monitor. Each run ends with a collusion-index summary against the competitive and
cartel prices. The paper's 75 runs ship as metrics + round logs (43 MB); the 250 MB of
per-agent transcripts are linked upstream.

```bash
cd llm-agent-collusion && uv sync && cp .env.example .env     # add OPENROUTER_API_KEY
uv run python src/continuous_double_auction/simulation.py --rounds 5 --tag smoke   # ~30 calls
```

### 5. [`colosseum/`](colosseum/)

**Question:** how do you audit a *team* of tool-calling LLM agents for collusion,
misalignment and misinformation spread, and how does the communication network shape it?

A framework (built on the Terrarium agent runtime) for running many tool-calling LLM agents
in shared environments such as a Jira ticket board or a hospital scheduling system, with
different network topologies between agents. Experiments cover persuasion effects on
collusion, topology sweeps, misinformation propagation and objective misalignment. Sprint
projects 1.1, 2.4 and 1.3: a preflight script for the Terrarium/CoLLAB setup, a ~20-call
positive-control config, and the four matched conditions of project 1.1 (assigned pair ±
private channel, open channel, neither) as ready-made configs, all through OpenRouter with
the paper's `openai/gpt-4o-mini` as default.

```bash
cd colosseum && uv sync && cp .env.example .env    # add OPENROUTER_API_KEY
uv run python -m experiments.preflight
uv run python -m experiments.collusion.run --config experiments/collusion/configs/hackathon_positive_control.yaml
```

### 6. [`llm-trust-breaking/`](llm-trust-breaking/)

**Question:** do LLMs break promises strategically, and how does trust between them evolve
when they deceive each other repeatedly?

Original: [Jerick-1380/LLM-Trust-Breaking](https://github.com/Jerick-1380/LLM-Trust-Breaking).
Several agents play 10 rounds of strategic games (e.g. the diners' dilemma) with a private
planning stage, public commitments and final actions, and every commitment break is
classified. Used in sprint projects 2.3 (does combining what agents say with what they do
improve detection?) and 3.2 (can agents tell when a peer has been replaced?). Runs through
OpenRouter; see its README for the quick start.

## Ground rules baked into every adapted project

Following the *Collusion Research Sprint: How to get started* brief:

- Runs on a normal 16 GB laptop, no GPU. Heavy dependencies (torch and friends) live in
  optional extras.
- **One provider, one key.** Every project calls models through OpenRouter with the
  hackathon's `OPENROUTER_API_KEY`. Where a paper's original model exists on OpenRouter it
  is the default; any other OpenRouter model id can be substituted with a flag. Each repo was
  smoke-tested live once with a small run.
- **No local GPU inference.** Code that loaded model weights (vLLM, transformers) is
  routed through the API instead. Original datasets are included when small.
- Defaults are the brief's cheap starting point: one prompt, one parameter value, one
  seed. Scripts print how many model calls a command will make before spending.
- The brief's weekend project for each repo is reproducible from command-line flags.
- Original results data is kept where it exists, so analysis notebooks still work.

Each folder has its own README with a quick start. The projects are independent; start
with the question that interests you.
