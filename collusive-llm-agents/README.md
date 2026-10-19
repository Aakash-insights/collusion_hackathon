# Strategic Collusion of LLM Agents: Market Division in Multi-Commodity Competitions 📈

## Overview 🌎
This repository contains the accompanying code for the [paper](https://arxiv.org/abs/2410.00031) titled "Strategic Collusion of LLM Agents: Market Division in Multi-Commodity Competitions". The study focuses on the application and implications of Large Language Models (LLMs) in setting prices and strategies in multi-commodity markets. Specifically, it investigates whether LLMs can engage in anti-competitive behavior such as specialization to monopolize different commodities within a market.

## Research Context 🔬
With the increasing deployment of AI technologies in marketplaces, the study explores the behavior of LLM-based pricing agents within the frameworks of both Bertrand and Cournot competition models. Key questions addressed include:
- Are LLMs capable of engaging in anti-competitive, specialization behavior in a multi-commodity market environment?
- How do LLMs adapt their strategies in response to varying market conditions and competition?

## Repository Structure ⛏️
- `cournot.ipynb`: Jupyter notebook containing the code for the Cournot competition experiments.
- `bertrand.ipynb`: Jupyter notebook containing the code for the Bertrand competition experiments.

## Setup ⚙️

Requires Python 3.9+. Configure inference once in the repo-root `compute.env` (`NEBIUS_API_KEY`) — see `COMPUTE.md`.

```bash
pip install -r requirements.txt
cp .env.example .env      # optional per-project overrides
jupyter notebook          # open cournot.ipynb or bertrand.ipynb
```

The notebooks keep the paper's original models —
`openai/gpt-4o-2024-08-06` for Cournot and `openai/gpt-3.5-turbo` for Bertrand — set in
the `MODEL_SPEC` constant near the top of each notebook. Adjust the constants and the
number of rounds as you see fit, and run the cells in order.

**Cost:** each round is one call per firm. The Cournot notebook defaults to 50 rounds
(~100 calls on gpt-4o); Bertrand to 5 rounds (~10 calls on gpt-3.5-turbo, ~30 s end to end).

**What to expect when running.** Outputs go to `bertrand_data/` and `cournot_data/`
(created on first run, ignored by git): one `run-NNN/` folder per run with a folder per
round (prompts and the model's structured reply), the two firms' history JSONs and a
`run_metadata.csv`. The plotting cells at the end read the latest run by default
(`RUN_TO_PLOT_FOLDER` in Bertrand, `RUN_TO_PLOT` in Cournot) — change that to compare
runs. A price below marginal cost is recorded as `Invalid Price: <p>` with zero sales,
which gpt-3.5-turbo does regularly; it is part of the experiment, not an error. The
notebooks only ask for keyboard input ("Manual Assist") when a reply cannot be parsed at
all, which did not happen in our runs.


## Implementation Details 📖

### Parsing

We found that using a JSON-style output format yielded more consistent, albeit imperfect, results. The output is then converted into a JSON object, which would then be parsed to update variables like the market history, firm info, etc.

### Validation

After parsing an agent's response, the information was validated. In both problem settings, we ensured that every field (e.g. price/quantity, observations, etc.) was included in the output.

During initial Bertrand experiments, we would give LLMs the option to invest in product A or product B in every run, but only if they met the prerequisites (number of investment options and enough money). However, the agents often chose to invest when these prerequisites were not met. As a result, we transitioned to calculating the list of possible options given the state of each agent and then prompted each agent to choose from the list of options. This significantly reduced the frequency of invalid options being chosen. With this new format, we added another validation step that ensured that the LLM picked an option from the list of options we gave it.

### Manual Assist & Retry Behavior

For our experiments, we also implemented a Manual Assist feature in the case where our code wasn't able to parse the LLM output. With Manual Assist, we would read the output and manually enter the values to be stored. 

In cases where the output was simply malformed, the LLM would be re-prompted 3 times. If it failed 3 times, the experiment would be interrupted. However, this only occurred during initial prompting while we were experimenting with the prompt format.

We find that in our experiments, the Manual Assist feature was only used $< 10$ times, and the re-prompting feature was **never** used. 

### Querying Format
For both experiments, we used the OpenAI API and set the user message to the entire prompt. We also specified the response format of the API to be a JSON object.

## How to Cite 📚
If you use any of the material here, please cite our paper:

```
@misc{lin2024strategiccollusionllmagents,
      title={Strategic Collusion of LLM Agents: Market Division in Multi-Commodity Competitions}, 
      author={Ryan Y. Lin and Siddhartha Ojha and Kevin Cai and Maxwell F. Chen},
      year={2024},
      eprint={2410.00031},
      archivePrefix={arXiv},
      primaryClass={cs.GT},
      url={https://arxiv.org/abs/2410.00031}, 
}
```


