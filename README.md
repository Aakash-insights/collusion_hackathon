# Hackathon NY starter repo

Ten research codebases on LLM agents, collusion and multi-agent coordination, bundled so a
team can clone once and start hacking. Every project runs on a normal laptop with **no GPU**,
calling models **through OpenRouter with a single API key**. Each folder has its own README
with a quick start; the projects are independent, so start with the question that interests
you. The starter gives you a working harness, not results: the sprint questions are yours to
answer.

## At a glance

| folder | paper / project | one-line summary | sprint projects |
|---|---|---|---|
| [`algorithmic-pricing-llms/`](algorithmic-pricing-llms/) | Romero, Sauer, Peist (2025), extends Fish et al. (2025) | LLM firms in a 300-round Calvano pricing game: tacit collusion, and how it erodes with more firms | 1.2 |
| [`llm-cartel/`](llm-cartel/) | Riemer et al., ICML 2026 position paper | Reasoning models in a Bertrand duopoly/triopoly under 19 prompt variants, monitoring notices, LLM judges, activation steering (GPU, untouched) | 1.2, 1.4 |
| [`focal-points/`](focal-points/) | Focal-point / Schelling coordination study | Do LLMs pick the same "obvious" answers humans do? Coordination index vs. human data; benign control for detectors | 1.4, 2.1, 3.2 |
| [`llm-agent-collusion/`](llm-agent-collusion/) | Agrawal et al. (2025), double auctions | LLM sellers and buyers in a continuous double auction with seller chat, an overseer, pressure and message caps | 2.1, 2.2, 3.3, 3.4 |
| [`colosseum/`](colosseum/) | UMass AI Safety, Colosseum on Terrarium | Tool-calling agent teams in Jira / hospital environments; topologies, private channels, persuasion, misinformation | 1.1, 2.4, 1.3 |
| [`llm-trust-breaking/`](llm-trust-breaking/) | Shi et al., LLM Trust Breaking | Promise-breaking and trust dynamics over 10 rounds of strategic games with private plans and public commitments | 2.3, 3.2 |
| [`collusive-llm-agents/`](collusive-llm-agents/) | Lin et al., *Strategic Collusion of LLM Agents* | Bertrand and Cournot notebooks: do pricing agents divide a multi-commodity market between them? | 1.3 (fallback) |
| [`llm-agent-collusion-2/`](llm-agent-collusion-2/) | Voluntary Collusion framework | Liar's Bar and Cleanup games with secret alliance channels: when do agents willingly collude against others? | 3.1 |
| [`steganographic-collusion/`](steganographic-collusion/) | *Audit the Whisper*, ColludeBench-v0 | Covert-channel theory plus calibrated detectors for steganographic collusion across pricing, auction, peer-review and double-auction environments | 2.4 |
| [`trace-guard/`](trace-guard/) | TraceGuard (Apart x Redwood AI Control hackathon) | Single-agent monitor scoring actions on five dimensions incl. action-trace consistency; a reusable rubric, not a collusion detector | 2.3 |

Project numbers refer to the *Collusion Research Sprint - How to get started* brief:
track 1 Markets and Antitrust, track 2 Workflows and Audit, track 3 Carriers and Countermeasures.

## The projects in more detail

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

### 7. [`collusive-llm-agents/`](collusive-llm-agents/)

**Question:** can LLM pricing agents carve up a multi-commodity market between themselves
instead of competing on every product?

Paper: *Strategic Collusion of LLM Agents: Market Division in Multi-Commodity Competitions*
(Lin et al., 2024). Two Jupyter notebooks, one for Bertrand (price) and one for Cournot
(quantity) competition, where firms observe market history and output structured JSON
decisions. The sprint uses it as the lighter fallback for project 1.3: prices or quantity
vectors are the observable actions, so visibility of those actions can be ablated without
a tool-using environment. Calls go through OpenRouter with the paper's models set in a
constant at the top of each notebook.

```bash
cd collusive-llm-agents && pip install -r requirements.txt && cp .env.example .env   # add OPENROUTER_API_KEY
jupyter notebook            # open bertrand.ipynb (~10 calls) or cournot.ipynb (~100 calls)
```

### 8. [`llm-agent-collusion-2/`](llm-agent-collusion-2/)

**Question:** when agents are handed a secret channel or a secret advantage, do they
voluntarily collude against the other players, and how does that evolve?

The Voluntary Collusion framework. Two games: **Liar's Bar**, a four-player bluffing card
game with hidden information, and **Cleanup**, a grid-world social dilemma balancing apple
collection against pollution. Each has a baseline, a secret-communication condition between
alliance partners, and a secret-hint condition. Sprint project 3.1 replaces the
experimenter-chosen partner with a scripted or monitor-controlled player that offers the same
pact to everyone and measures who accepts. Originally built for local Llama / Mistral / Qwen
models; see its README for the API route.

### 9. [`steganographic-collusion/`](steganographic-collusion/)

**Question:** can colluding agents hide coordination inside innocent-looking messages, and
what evidence is enough to catch them?

*Audit the Whisper* couples channel-capacity theory with **ColludeBench-v0**: pricing,
first-price auction, peer review and continuous-double-auction environments with
configurable colluders and covert channels, plus a calibrated detector stack (mutual
information, permutation invariance, watermark variance, acceptance-bias and welfare
guards) tuned to low false-positive rates. Sprint project 2.4 uses its environments,
detector code and stored result manifests, with the brief's caveat to preflight them rather
than treat them as a turnkey bag of trajectories. Heavy on results and docs; start from its
README's smoke test.

### 10. [`trace-guard/`](trace-guard/)

**Question:** does scoring an agent's reasoning and actions on several structured
dimensions catch what a single "is this suspicious?" check misses?

TraceGuard, built at the Apart x Redwood AI Control hackathon (March 2026). It scores each
agent action on five dimensions in parallel (goal alignment, constraint adherence, reasoning
coherence, safety awareness, action-trace consistency) with tiered deeper analysis and
heuristic detectors. It is a **single-agent** monitor, not a collusion detector; sprint
project 2.3 reuses its action-trace consistency rubric as one of the monitor views compared
on the trust-breaking logs.

## Ground rules

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

The projects are independent; start with the question that interests you. Nothing here
answers a sprint question for you: the runs, comparisons, detectors and conclusions are the
teams' work.
