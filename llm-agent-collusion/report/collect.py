"""Collect every number used in the report from run folders and the teammate's summary.csv -> data.json."""
import csv, glob, json, os, re, statistics as st

from pathlib import Path

HERE = Path(__file__).resolve().parent
R = str(HERE.parent / "sprint_results_qwen" / "runs")  # Qwen run folders (in the repo)
TEAMMATE_CSV = HERE.parent / "sprint_results" / "summary.csv"  # GPT-4.1 / Claude runs
CE, JPM = 90.0, 100.0


def ms(v):
    v = [x for x in v if x is not None]
    if not v:
        return {"mean": None, "sd": None, "n": 0, "vals": []}
    return {"mean": st.mean(v), "sd": st.stdev(v) if len(v) > 1 else 0.0, "n": len(v), "vals": v}


def rounds(d):
    t = open(f"{d}/auction_results.md", encoding="utf-8", errors="replace").read()
    return [json.loads(b) for b in re.findall(r"## Auction Results: Round \d+\n````json\n(.*?)\n````", t, re.S)]


def opening(d):
    p = open(sorted(glob.glob(f"{d}/Seller*.md"))[0], encoding="utf-8", errors="replace").read()
    a = [float(x) for x in re.findall(r"\(([\d.]+), '", re.search(r"Current Status of Ask Queue\n\n(\[.*?\])", p).group(1))]
    b = [float(x) for x in re.findall(r"\(([\d.]+), '", re.search(r"Current Status of Bid Queue\n\n(\[.*?\])", p).group(1))]
    return st.mean(a), st.mean(b)


def run(d):
    m = json.load(open(f"{d}/collusion_metrics.json"))
    R_ = rounds(d)
    last = [x["price"] for r in R_[-5:] for x in r["trades"]]
    oa, ob = opening(d)
    msgs = [v for r in R_ for v in r["seller_messages"].values() if v]
    words = [w for v in msgs for w in re.findall(r"[a-z']+", v.lower())]
    ov = []
    if os.path.exists(f"{d}/Overseer.md"):
        ov = [int(x) for x in re.findall(r'"coordination_score"\s*:\s*"?(\d)', open(f"{d}/Overseer.md").read())]
    return {
        "seed": int(re.search(r"seed(\d+)$", d).group(1)) if re.search(r"seed(\d+)$", d) else 0,
        "price": m["avg_trade_price_overall"], "trades": m["num_trades"],
        "sp": m["combined_seller_profits"], "bs": m["combined_buyer_surplus"],
        "last5": st.mean(last) if last else None,
        "ask1": st.mean(R_[0]["seller_asks"].values()), "ask15": st.mean(R_[-1]["seller_asks"].values()),
        "open_ask": oa, "open_bid": ob,
        "msglen": st.mean(len(v) for v in msgs) if msgs else 0.0, "vocab": len(set(words)),
        "ov": st.mean(ov) if ov else None, "disp": m["avg_seller_ask_dispersion"],
    }


def group(pattern):
    ds = sorted(d for d in glob.glob(f"{R}/{pattern}") if os.path.exists(f"{d}/collusion_metrics.json"))
    return [run(d) for d in ds]


def summ(runs, keys=("price", "sp", "bs", "trades", "last5", "ask1", "ask15", "msglen", "vocab", "ov", "disp")):
    out = {k: ms([r[k] for r in runs]) for k in keys if any(r[k] is not None for r in runs)}
    out["share"] = ms([r["sp"] / (r["sp"] + r["bs"]) for r in runs])
    out["n"] = len(runs)
    out["seeds"] = [r["seed"] for r in runs]
    return out


Q = {
    # Qwen3-235B both sides unless noted; opening asks ~97.5 / bids ~82.5 unless noted
    "q_base_chat": group("*_A_baseline_llmbuyers-seed*"),
    "q_base_nochat": group("*_N0_nocomms_llm-seed*"),
    "q_open90_chat": group("*_M_QQ_open90_comms-seed*"),
    "q_open90_nochat": group("*_M_QQ_open90_nocomms-seed*"),
    "q_bothchat": group("*_M_QQ_bothcomms-seed*"),
    "q_buyerchat": group("*_BC_buyercomms_llm-seed*"),
    "qs_chat": group("*_M_QS_comms-seed*"),
    "qs_nochat": group("*_M_QS_nocomms-seed*"),
    "qs_open90_chat": group("*_M_QS_open90_comms-seed*"),
    "sq_chat": group("*_M_SQ_comms-seed*"),
    "q_bids90_chat": group("*_M_QQ_bids90_comms-seed*"),
    "q_bids95_chat": group("*_M_QQ_bids95_comms-seed*"),
    "q_bids95_nochat": group("*_M_QQ_bids95_nocomms-seed*"),
    "r_4v3_nochat": group("*_R_4v3_nochat-seed*"),
    "r_4v3_chat": group("*_R_4v3_chat-seed*"),
    "r_4v3_ov": group("*_R_4v3_overseer-seed*"),
    "r_3v3_nochat": group("*_R_3v3_nochat-seed*"),
    "r_3v3_chat": group("*_R_3v3_chat-seed*"),
    # track 3.4 oversight conditions (Qwen3-235B sellers+buyers, Qwen3-32B overseer)
    "ov_silent_gag": group("*_B_silent-seed*"),
    "ov_silent_nogag": group("*_B2_silent_nogag-seed*"),
    "ov_told25": group("*_C_told25-seed*"),
    "ov_told50": group("*_D_told50-seed*"),
    "ov_told100": group("*_E_told100-seed*"),
    "ov_told100_boss": group("*_F_told100_boss-seed*"),
    "ov_disc25": group("*_C2_disc25-seed*"),
    "ov_disc50": group("*_D2_disc50-seed*"),
    "ov_disc100": group("*_E2_disc100-seed*"),
}
# 3.4 baseline rows restricted to the same seeds as most oversight cells
Q["q_base_chat_all"] = Q["q_base_chat"]

data = {"qwen": {k: summ(v) for k, v in Q.items() if v}, "qwen_runs": Q}

# ---- teammate GPT-4.1 runs (summary.csv on branch `results`)
rows = list(csv.DictReader(open(TEAMMATE_CSV)))
by = {r["run"].split("_", 2)[2]: r for r in rows}
f = lambda r, k: float(r[k]) if r[k] not in ("", None) else None


def g(names):
    rs = [by[n] for n in names]
    return {
        "price": ms([f(r, "avg_trade_price") for r in rs]), "tidx": ms([f(r, "trade_index") for r in rs]),
        "askidx": ms([f(r, "ask_index_last_third") for r in rs]), "sp": ms([f(r, "seller_profit") for r in rs]),
        "bs": ms([f(r, "buyer_surplus") for r in rs]), "trades": ms([f(r, "trades") for r in rs]),
        "ask1": ms([f(r, "ask_round1") for r in rs]), "ask15": ms([f(r, "ask_last_round") for r in rs]),
        "passed": sum(r["passed"] == "True" for r in rs), "n": len(rs),
    }


G = {
    "main5": ["gpt41_comms_llmbuyers"] + [f"llmb_comms_seeds-seed{i}" for i in (1, 2, 3, 4)],
    "chat3": ["gpt41_comms_llmbuyers", "llmb_comms_seeds-seed1", "llmb_comms_seeds-seed2"],
    "ov3": ["llmb_oversight", "llmb_oversight_seeds-seed1", "llmb_oversight_seeds-seed2"],
    "nochat3": ["llmb_nocomms", "llmb_nocomms_seeds-seed1", "llmb_nocomms_seeds-seed2"],
    "s90_chat": ["start90_comms", "start90_comms_seeds-seed1", "start90_comms_seeds-seed2"],
    "s90_nochat": ["start90_nocomms", "start90_nocomms_seeds-seed1", "start90_nocomms_seeds-seed2"],
    "ladder": [f"start90_ladder_leader-seed{i}" for i in range(3)],
    "visible": [f"start90_asks_visible-seed{i}" for i in range(3)],
    "zip_chat": ["gpt41_comms"], "zip_ov": ["gpt41_comms_oversight"],
    "p_notp": ["start90_prompt_no_trade_pressure"], "p_hide": ["start90_prompt_hide_rounds"],
    "p_boss": ["start90_prompt_boss_pressure"], "s90_ov": ["start90_oversight"],
    # competition test (teammate commit b43f146): neutral opening asks ~92 / bids ~88
    **{k: [f"{k}-seed{i}" for i in range(3)] for k in (
        "r43_nochat", "r43_chat", "r43_chat_overseer", "r43_chat_silent_overseer", "r43_buyer_chat",
        "r33_nochat", "r33_chat", "r34_nochat")},
}
data["gpt"] = {k: g(v) for k, v in G.items()}
# anchoring: every complete GPT-4.1 run with LLM buyers and only LLM sellers
anch = [(f(r, "ask_round1"), f(r, "avg_trade_price"), r["comms"] == "True") for r in rows
        if r["complete"] == "True" and r["buyers"] != "zip" and r["sellers"].startswith("gpt-4.1") and "ladder" not in r["run"]
        and r["avg_trade_price"]]
data["gpt_anchor"] = anch
xs, ys = [a[0] for a in anch], [a[1] for a in anch]
mx, my = st.mean(xs), st.mean(ys)
data["gpt_anchor_r"] = sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / (
    (sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys)) ** 0.5)
data["gpt_anchor_n"] = len(anch)


# ---- paired chat effects (same seed => same opening quotes)
def paired(a, b):
    A = {r["seed"]: r["price"] for r in a}
    B = {r["seed"]: r["price"] for r in b}
    d = [A[s] - B[s] for s in sorted(set(A) & set(B))]
    return ms(d)


gp = lambda a, b: ms([float(by[x]["avg_trade_price"]) - float(by[y]["avg_trade_price"]) for x, y in zip(G[a], G[b])])
data["paired"] = [
    ["GPT-4.1, open $97.5", gp("chat3", "nochat3")],
    ["GPT-4.1, open $90", gp("s90_chat", "s90_nochat")],
    ["GPT-4.1 3:3, neutral open", gp("r33_chat", "r33_nochat")],
    ["GPT-4.1 4:3, neutral open", gp("r43_chat", "r43_nochat")],
    ["Qwen, open $97.5", paired(Q["q_base_chat"], Q["q_base_nochat"])],
    ["Qwen, open $90", paired(Q["q_open90_chat"], Q["q_open90_nochat"])],
    ["Qwen vs Qwen-32B buyers", paired(Q["qs_chat"], Q["qs_nochat"])],
    ["Qwen, buyers open $95", paired(Q["q_bids95_chat"], Q["q_bids95_nochat"])],
    ["Qwen 3:3, neutral open", paired(Q["r_3v3_chat"], Q["r_3v3_nochat"])],
    ["Qwen 4:3, neutral open", paired(Q["r_4v3_chat"], Q["r_4v3_nochat"])],
]
json.dump(data, open(HERE / "data.json", "w"), indent=1)
print("ok", data["gpt_anchor_n"], round(data["gpt_anchor_r"], 3))
for name, p in data["paired"]:
    print(f"{name:28s} {p['mean']:+.2f} ± {p['sd']:.2f} (n={p['n']})")
for k, v in data["qwen"].items():
    print(f"{k:18s} n={v['n']} price {v['price']['mean']:.2f}±{v['price']['sd']:.2f} share {v['share']['mean']:.0%}"
          + (f" ov {v['ov']['mean']:.2f}" if 'ov' in v else "") + f" msg {v['msglen']['mean']:.0f} disp {v['disp']['mean']:.3f}")
