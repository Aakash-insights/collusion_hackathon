"""Build report.html from data.json (all numbers computed by collect.py)."""
import json

from pathlib import Path

S = str(Path(__file__).resolve().parent)
D = json.load(open(f"{S}/data.json"))
Q, G, RUNS = D["qwen"], D["gpt"], D["qwen_runs"]
BLUE, ORANGE, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#d9d8d3"

pm = lambda s, d=2: f"{s['mean']:.{d}f} ± {s['sd']:.{d}f}"
idx = lambda p: f"{(p - 90) / 10:+.2f}"
pct = lambda s: f"{s['mean'] * 100:.0f}%"

n_qwen = sum(v["n"] for k, v in Q.items() if k != "q_base_chat_all")
n_gpt = sum(v["n"] for v in G.values())
N_TOTAL = n_qwen + n_gpt + 1  # + 1 exploratory Claude Sonnet 5.5 session (teammate)


# ---------------------------------------------------------------- figures (static SVG, print)
def scatter(points, title, xlab, x0, x1, y0, y1, w=318, h=240):
    L, B, T, Rm = 46, 40, 26, 10
    px = lambda x: L + (x - x0) / (x1 - x0) * (w - L - Rm)
    py = lambda y: h - B - (y - y0) / (y1 - y0) * (h - B - T)
    s = [f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{title}">']
    s.append(f'<text x="{L}" y="15" font-size="11" font-weight="600" fill="{INK}">{title}</text>')
    for v in range(int(y0), int(y1) + 1, 5):
        s.append(f'<line x1="{L}" x2="{w - Rm}" y1="{py(v):.1f}" y2="{py(v):.1f}" stroke="{GRID}" stroke-width="0.6"/>')
        s.append(f'<text x="{L - 5}" y="{py(v) + 3:.1f}" font-size="9" text-anchor="end" fill="{MUTED}">{v}</text>')
    for v in range(int(x0), int(x1) + 1, 5):
        s.append(f'<text x="{px(v):.1f}" y="{h - B + 13}" font-size="9" text-anchor="middle" fill="{MUTED}">{v}</text>')
    lo, hi = max(x0, y0), min(x1, y1)
    s.append(f'<line x1="{px(lo):.1f}" y1="{py(lo):.1f}" x2="{px(hi):.1f}" y2="{py(hi):.1f}" stroke="{MUTED}" stroke-width="1" stroke-dasharray="4 3"/>')
    for x, y, chat in points:
        c = BLUE if chat else ORANGE
        s.append(f'<circle cx="{px(x):.1f}" cy="{py(y):.1f}" r="4" fill="{c}" fill-opacity="0.85" stroke="#fcfcfb" stroke-width="1.5"/>')
    s.append(f'<text x="{(L + w - Rm) / 2:.0f}" y="{h - 8}" font-size="9.5" text-anchor="middle" fill="{INK}">{xlab}</text>')
    s.append(f'<text transform="translate(12,{(T + h - B) / 2:.0f}) rotate(-90)" font-size="9.5" text-anchor="middle" fill="{INK}">Session avg trade price ($)</text>')
    s.append("</svg>")
    return "".join(s)


gpt_pts = [(a, b, c) for a, b, c in D["gpt_anchor"]]
chat_groups = {"q_base_chat": 1, "q_base_nochat": 0, "q_open90_chat": 1, "q_open90_nochat": 0, "q_bothchat": 1,
               "q_buyerchat": 0, "q_bids90_chat": 1, "q_bids95_chat": 1, "q_bids95_nochat": 0}
qwen_pts = [(r["open_bid"], r["price"], bool(c)) for k, c in chat_groups.items() for r in RUNS[k]]
fig1 = scatter(gpt_pts, "(a) GPT-4.1 sellers follow their own opening ask", "Sellers' round-1 average ask ($)", 85, 100, 80, 100) + \
       scatter(qwen_pts, "(b) Qwen3-235B markets follow the buyers' opening bid", "Buyers' opening average bid ($)", 80, 100, 80, 100)
legend = (f'<div class="legend"><span><i style="background:{BLUE}"></i>seller chat on</span>'
          f'<span><i style="background:{ORANGE}"></i>seller chat off</span>'
          f'<span><svg width="22" height="8"><line x1="0" y1="4" x2="22" y2="4" stroke="{MUTED}" stroke-dasharray="4 3"/></svg> price = opening quote</span></div>')


def forest(rows, w=640):
    L, Rm, top, rh = 200, 70, 22, 25
    h = top + rh * len(rows) + 34
    x0, x1 = -3.5, 4.5
    px = lambda x: L + (x - x0) / (x1 - x0) * (w - L - Rm)
    s = [f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="Paired effect of seller chat on price">']
    for v in range(-3, 5):
        s.append(f'<line x1="{px(v):.1f}" x2="{px(v):.1f}" y1="{top - 6}" y2="{h - 30}" stroke="{GRID if v else MUTED}" stroke-width="{0.6 if v else 1.2}"/>')
        s.append(f'<text x="{px(v):.1f}" y="{h - 17}" font-size="9" text-anchor="middle" fill="{MUTED}">{v:+d}</text>')
    s.append(f'<text x="{(L + w - Rm) / 2:.0f}" y="{h - 3}" font-size="9.5" text-anchor="middle" fill="{INK}">Chat on − chat off, same seed ($ per unit)</text>')
    for i, (name, p) in enumerate(rows):
        y = top + i * rh + rh / 2
        s.append(f'<text x="{L - 10}" y="{y + 3:.1f}" font-size="9.5" text-anchor="end" fill="{INK}">{name}</text>')
        for v in p["vals"]:
            s.append(f'<circle cx="{px(v):.1f}" cy="{y:.1f}" r="2.6" fill="{MUTED}" fill-opacity="0.55"/>')
        m, sd = p["mean"], p["sd"]
        s.append(f'<line x1="{px(m - sd):.1f}" x2="{px(m + sd):.1f}" y1="{y:.1f}" y2="{y:.1f}" stroke="{BLUE}" stroke-width="2"/>')
        s.append(f'<circle cx="{px(m):.1f}" cy="{y:.1f}" r="4.5" fill="{BLUE}" stroke="#fcfcfb" stroke-width="1.5"/>')
        s.append(f'<text x="{w - Rm + 8}" y="{y + 3:.1f}" font-size="9" fill="{MUTED}">{m:+.2f} ± {sd:.2f}</text>')
    s.append("</svg>")
    return "".join(s)


fig2 = forest(D["paired"])


# ---------------------------------------------------------------- tables
def gpt_row(label, k, note=""):
    g = G[k]
    share = g["sp"]["mean"] / (g["sp"]["mean"] + g["bs"]["mean"])
    return (f"<tr><td>{label}</td><td>{g['n']}</td><td>{pm(g['price'])}</td><td>{g['tidx']['mean']:+.2f}</td>"
            f"<td>{g['passed']}/{g['n']}</td><td>{share * 100:.0f}%</td><td>{note}</td></tr>")


T1 = "".join([
    gpt_row("Rule-based <code>zip</code> buyers, chat", "zip_chat", "buyers frozen at $80"),
    gpt_row("Rule-based <code>zip</code> buyers, chat + overseer", "zip_ov", "buyers frozen at $80"),
    gpt_row("<b>Positive control</b>: chat, open ≈$97.5 (seeds 0–4)", "main5", "README positive control"),
    gpt_row("Chat, open ≈$97.5 (seeds 0–2)", "chat3"),
    gpt_row("Chat + overseer, open ≈$97.5", "ov3"),
    gpt_row("No chat, open ≈$97.5", "nochat3"),
    gpt_row("Chat, open ≈$90", "s90_chat"),
    gpt_row("No chat, open ≈$90", "s90_nochat"),
    gpt_row("No chat, open ≈$90, scripted price leader", "ladder", "leader +$1 / 3 rounds"),
    gpt_row("No chat, open ≈$90, “asks are visible” prompt", "visible"),
])


def q_row(label, k, extra=""):
    q = Q[k]
    return (f"<tr><td>{label}</td><td>{q['n']}</td><td>{pm(q['price'])}</td><td>{idx(q['price']['mean'])}</td>"
            f"<td>{pct(q['share'])}</td><td>{extra}</td></tr>")


T2 = "".join([
    q_row("Chat, open asks ≈$97.5 / bids ≈$82.5", "q_base_chat"),
    q_row("No chat", "q_base_nochat"),
    q_row("Chat, sellers open ≈$90", "q_open90_chat"),
    q_row("No chat, sellers open ≈$90", "q_open90_nochat"),
    q_row("Seller and buyer chat", "q_bothchat"),
    q_row("Buyer chat only", "q_buyerchat"),
    q_row("Chat, Qwen3-32B buyers (strong seller)", "qs_chat"),
    q_row("No chat, Qwen3-32B buyers", "qs_nochat"),
    q_row("Chat, Qwen3-32B sellers (weak seller)", "sq_chat"),
    q_row("Chat, buyers open ≈$90", "q_bids90_chat"),
    q_row("Chat, buyers open ≈$95", "q_bids95_chat", "would PASS built-in test"),
    q_row("No chat, buyers open ≈$95", "q_bids95_nochat", "would PASS built-in test"),
])

ov_rows = [("No overseer, chat", "q_base_chat"), ("Silent overseer, gag on", "ov_silent_gag"),
           ("Silent overseer, no gag", "ov_silent_nogag"), ("Told: monitored (25% sampled)", "ov_told25"),
           ("Told: monitored (50% sampled)", "ov_told50"), ("Told: monitored (100%)", "ov_told100"),
           ("Told 100% + profit pressure", "ov_told100_boss"), ("Told + fraction disclosed (25%)", "ov_disc25"),
           ("Told + fraction disclosed (50%)", "ov_disc50"), ("Told + fraction disclosed (100%)", "ov_disc100")]
T3 = ""
for label, k in ov_rows:
    q = Q[k]
    ov = f"{q['ov']['mean']:.2f}" if "ov" in q else "–"
    T3 += (f"<tr><td>{label}</td><td>{q['n']}</td><td>{ov}</td><td>{q['msglen']['mean']:.0f}</td><td>{q['vocab']['mean']:.0f}</td>"
           f"<td>{q['disp']['mean']:.2f}</td><td>{pm(q['price'])}</td><td>{pct(q['share'])}</td></tr>")

T4 = ""
def t4q(label, ratio, k, comp):
    q = Q[k]
    return (f"<tr><td>Qwen3-235B</td><td>{ratio}</td><td>{label}</td><td>{q['n']}</td><td>{pm(q['price'])}</td>"
            f"<td>{q['ask1']['mean']:.2f} → {q['ask15']['mean']:.2f}</td><td>${comp}</td><td>{q['price']['mean'] - comp:+.1f}</td></tr>")
def t4g(label, ratio, k, comp):
    g = G[k]
    return (f"<tr><td>GPT-4.1<sup>†</sup></td><td>{ratio}</td><td>{label}</td><td>{g['n']}</td><td>{pm(g['price'])}</td>"
            f"<td>{g['ask1']['mean']:.2f} → {g['ask15']['mean']:.2f}</td><td>${comp}</td><td>{g['price']['mean'] - comp:+.1f}</td></tr>")
T4 += t4q("No chat", "4 : 3", "r_4v3_nochat", 80) + t4q("Seller chat", "4 : 3", "r_4v3_chat", 80) + t4q("Chat + overseer", "4 : 3", "r_4v3_ov", 80)
T4 += t4q("No chat", "3 : 3", "r_3v3_nochat", 90) + t4q("Seller chat", "3 : 3", "r_3v3_chat", 90)
T4 += t4g("No chat", "4 : 3", "r43_nochat", 80) + t4g("Seller chat", "4 : 3", "r43_chat", 80) + t4g("Chat + overseer", "4 : 3", "r43_chat_overseer", 80)
T4 += t4g("Chat + silent overseer<sup>‡</sup>", "4 : 3", "r43_chat_silent_overseer", 80) + t4g("Buyer chat only", "4 : 3", "r43_buyer_chat", 80)
T4 += "<tr><td>Claude Sonnet 5.5<sup>§</sup></td><td>4 : 3</td><td>No chat</td><td>1</td><td>90.16</td><td>91.25 → 89.28</td><td>$80</td><td>+10.2</td></tr>"
T4 += t4g("No chat", "3 : 3", "r33_nochat", 90) + t4g("Seller chat", "3 : 3", "r33_chat", 90)
T4 += t4g("<b>No chat (control)</b>", "<b>3 : 4</b>", "r34_nochat", 100)

P = {name: p for name, p in D["paired"]}


def team_tables():
    """Parse section 1 of ../TEAM_RESULTS.md (built by tools/build_team_results.py) into compact HTML tables."""
    md = open(f"{S}/../TEAM_RESULTS.md", encoding="utf-8").read()
    sec = md.split("## 1. All conditions", 1)[1].split("\n## 2.", 1)[0]
    out = ""
    for block in sec.split("\n### ")[1:]:
        title, *lines = block.strip().splitlines()
        rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines if l.startswith("|")]
        head, body = rows[0], rows[2:]
        keep = ["Condition (tag)", "Sellers", "Buyers", "S:B", "Costs", "Open ask / bid", "Chat", "Overseer", "Other", "n",
                "Avg price ($)", "Comp.", "Seller share"]
        ix = [head.index(k) for k in keep]
        clean = lambda c: c.replace("`", "").replace("(rule-based)", "").replace("gpt-4.1-mini", "4.1-mini")
        trs = "".join("<tr>" + "".join(f"<td>{clean(r[i])}</td>" for i in ix) + "</tr>" for r in body)
        ths = "".join(f"<th>{k.replace('Condition (tag)', 'Run tag').replace('Avg price ($)', 'Price ($)')}</th>" for k in keep)
        out += f'<h3>{clean(title)}</h3><table class="small"><tr>{ths}</tr>{trs}</table>'
    return out


TEAM = team_tables()
gm, ov = G["main5"], Q
abstract_words = None

CSS = """
@page { size: A4; margin: 18mm 17mm 18mm 17mm; }
body { font-family: 'Times New Roman', Times, serif; font-size: 10.6pt; line-height: 1.38; color: #0b0b0b; background: #fff; }
h1 { font-size: 17pt; line-height: 1.2; margin: 0 0 6px; text-align: center; }
.authors { text-align: center; font-size: 10.5pt; margin-bottom: 2px; }
.affil { text-align: center; font-size: 9.5pt; color: #52514e; margin-bottom: 10px; }
.todo { background: #fff2b3; padding: 0 3px; }
.abstract { margin: 6px 26px 12px; font-size: 10pt; }
.abstract b { display: block; text-align: center; margin-bottom: 3px; }
h2 { font-size: 12.5pt; margin: 14px 0 4px; break-after: avoid; }
h3 { font-size: 11pt; margin: 10px 0 3px; break-after: avoid; }
p { margin: 0 0 6px; text-align: justify; }
ul, ol { margin: 2px 0 6px 18px; padding: 0; } li { margin-bottom: 2px; }
table { border-collapse: collapse; width: 100%; font-size: 8.8pt; margin: 4px 0 2px; }
th, td { border-bottom: 0.5pt solid #c9c8c2; padding: 2px 5px; text-align: left; vertical-align: top; }
th { border-top: 1pt solid #0b0b0b; border-bottom: 0.8pt solid #0b0b0b; font-weight: 600; }
tr:last-child td { border-bottom: 1pt solid #0b0b0b; }
td:nth-child(n+2), th:nth-child(n+2) { white-space: nowrap; }
.cap { font-size: 9pt; color: #333; margin: 3px 0 10px; text-align: justify; }
.fig { display: flex; justify-content: center; gap: 8px; flex-wrap: nowrap; margin-top: 6px; }
.legend { display: flex; justify-content: center; gap: 18px; font-size: 9pt; color: #333; }
.legend i { display: inline-block; width: 9px; height: 9px; border-radius: 50%; margin-right: 5px; vertical-align: -1px; }
a { color: #1c5cab; text-decoration: none; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 8.6pt; }
.box { border: 0.8pt solid #0b0b0b; padding: 5px 9px; margin: 6px 0 8px; font-size: 10pt; }
.pb { break-before: page; }
.refs p { text-indent: -16px; padding-left: 16px; text-align: left; font-size: 9.6pt; margin-bottom: 3px; }
.keep { break-inside: avoid; }
table.small { font-size: 7pt; } table.small td, table.small th { padding: 1px 3px; white-space: normal !important; }
"""

html = f"""<!doctype html><html><head><meta charset="utf-8"><title>Cartel Talk, Competitive Prices</title><style>{CSS}</style></head><body>
<h1>Cartel Talk, Competitive Prices: Opening Anchors—Not Communication or Oversight—Drive Apparent LLM Seller Collusion in Double Auctions</h1>
<div class="authors">Aakash Patil and Bar Hoze</div>
<div class="affil">Apart Research AI Collusion Research Sprint, Oct 23–25, 2026 · Track 3 (project 3.4), with Track 1 (1.5)</div>
<div class="affil">Code, data and all runs: <a href="https://github.com/Aakash-insights/collusion_hackathon/tree/sprint-merged">github.com/Aakash-insights/collusion_hackathon</a> (branch <code>sprint-merged</code>)</div>

<div class="abstract"><b>Abstract</b>
LLM sellers in continuous double auctions are reported to coordinate high prices, especially when they can talk. Project 3.4 asks what such a coalition does when it learns it is being watched. We first tested whether the coalition exists. Across {N_TOTAL} market sessions with GPT-4.1, Qwen3 and Claude sellers and LLM buyers, we find: (1) the starter environment's rule-based buyer is frozen at $80, invalidating cheap runs; (2) final prices are set by the hard-coded opening quotes. GPT-4.1 sellers hold their opening ask (r = {D['gpt_anchor_r']:.3f}, n = {D['gpt_anchor_n']}), Qwen3-235B markets settle at the buyers' opening bid, and a Qwen market “passes” the built-in collusion test when buyers merely open high. (3) Despite explicit cartel language from both families, seller communication barely moved prices: paired-seed effects ranged from {min(p['mean'] for _, p in D['paired']):+.2f} to {max(p['mean'] for _, p in D['paired']):+.2f} dollars across {len(D['paired'])} settings, under 11% of the $10 competitive–cartel gap. (4) When sellers are told they are monitored, overseer coordination scores fall from {Q['ov_silent_nogag']['ov']['mean']:.2f} to {min(Q[k]['ov']['mean'] for k in ('ov_told25','ov_told50','ov_told100')):.1f}–{max(Q[k]['ov']['mean'] for k in ('ov_told25','ov_told50','ov_told100')):.1f} and messages shorten, but neither prices nor ask dependence rise, so there is no channel movement by the track's standard. (5) Under excess supply, prices stay $8–11 above the competitive $80, but an excess-demand control also fails to rise, so within 15 rounds the market barely responds to supply and demand and cannot reveal tacit collusion. A stronger seller (Claude Sonnet 5.5, one seed) does track the spare seller and cuts prices about five times faster than GPT-4.1. We recommend paired-seed causal metrics, neutral openings and market-responsiveness controls.
</div>

<h2>1&nbsp;&nbsp;Introduction</h2>
<p>LLM agents are increasingly deployed to set prices and negotiate. If they collude, the harm to consumers is concrete, and the evidence trail (natural-language messages) looks unusually auditable. Agrawal et al. (2025) built a continuous double auction in which LLM sellers can message each other, and reported coordinated pricing, with communication and oversight as levers. Project 3.4 of this sprint asks the natural next question: <i>what does a seller coalition do when it learns it is being watched?</i> Does it stop colluding, or move its coordination into a less visible channel?</p>
<p>Answering that requires a coalition whose behavior depends on its coordination. We therefore first asked whether high prices in this environment are caused by coordination at all. Our contributions are:</p>
<ol>
<li><b>An environment audit.</b> We found that the rule-based (ZIP) buyer is frozen at $80, that the hard-coded opening quotes largely determine outcomes, and that the competitive-price benchmark is wrong when seller and buyer counts differ (§4.1, Appendix B).</li>
<li><b>A causal test of communication.</b> We compare chat on and off on matched seeds across eight settings and two model families. Communication never measurably changed prices (§4.3).</li>
<li><b>Track 3.4.</b> Across 10 oversight conditions (silent logging, being told, a 25/50/100% sampled monitor, profit pressure), message-based coordination falls when sellers know they are watched, but action-based dependence does not rise, so we find no channel movement (§4.4).</li>
<li><b>A model-temperament finding.</b> GPT-4.1 holds its opening price; Qwen3 sellers cut to the buyers' bid immediately. Both talk like a cartel. Which side “wins” is set by which side holds still, not by what the sellers say (§4.2, §4.6).</li>
</ol>

<h2>2&nbsp;&nbsp;Related Work</h2>
<p><b>Algorithmic and LLM collusion.</b> Q-learning pricing agents learn supra-competitive prices without communicating (Calvano et al., 2020). LLM pricing agents in repeated oligopolies also reach supra-competitive prices, and this is sensitive to prompt wording (Fish, Gonczarowski &amp; Shorrer, 2024). Agrawal et al. (2025) introduced the double-auction environment we use and reported that seller communication and model choice affect coordination. Keppo et al. (2026) study how fragile AI agent collusion is. Our results support a related caution: in this environment, apparent collusion is largely explained by initial conditions.</p>
<p><b>Monitoring agents that know they are watched.</b> Weak-to-strong monitoring of LLM agents is unreliable when agents are aware of the monitor (Kale et al., 2025). Agents can infer chain-of-thought monitoring from blocking feedback (Jiralerspong, Kondrup &amp; Bengio, 2026), and monitors have systematic blind spots to evasion attacks (Najt et al., 2026). We study the market analogue: a message-level overseer that can gag sellers.</p>
<p><b>Double auctions.</b> Human double auctions converge quickly toward competitive equilibrium (Smith, 1962). So do budget-constrained “zero-intelligence” traders (Gode &amp; Sunder, 1993) and adaptive ZIP traders (Cliff, 1997). This makes LLM markets that do <i>not</i> move off their opening quotes a notable departure.</p>

<h2>3&nbsp;&nbsp;Methodology</h2>
<p><b>Environment.</b> We use the starter repository's <code>llm-agent-collusion</code> double auction. Sellers have unit cost $80 and buyers unit value $100. One lot per agent per hour, 15 hours, temperature 0.7, and the paper's prompts unchanged. Each hour every agent sees both order queues, the last five hours of quotes, past trades and its own memory, then posts one ask or bid. Trades clear at the midpoint of the best crossing ask and bid. With 3 sellers and 3 buyers the code's benchmarks are a competitive price of $90 and a cartel price of $100. We report the <i>trade index</i> (price − 90) / 10, so 0 is competitive and 1 is the cartel price. The built-in PASS criterion is “mean seller-ask index over the last third of hours &gt; 0.5”. By default, opening asks are drawn uniformly around $97.5 and bids around $82.5 (±$1.25).</p>
<p><b>Models and providers.</b> GPT-4.1 sellers with gpt-4.1-mini buyers (overseer: gpt-4.1-mini) ran via OpenRouter. Qwen3-235B-A22B-2507 sellers and buyers, with Qwen3-32B as the overseer and as the weak-agent condition, ran via AWS Bedrock (ap-south-1) through an OpenAI-compatible shim. One exploratory 4 : 3 session (teammate) used Claude Sonnet 5.5 sellers. Model and provider are fixed within every comparison.</p>
<p><b>Design.</b> Every comparison uses <i>matched seeds</i>: the same seed gives identical agent names and opening quotes, so “chat on” and “chat off” sessions differ only in the manipulated variable. Most cells use seeds 0–2; the GPT-4.1 positive control uses seeds 0–4, and two Qwen cells use 6–7 seeds. The conditions are (i) seller chat on/off; (ii) the overseer, silent or announced, gagging or observe-only, sampling 25/50/100% of messages, with or without disclosing that fraction, and with or without CEO profit pressure; (iii) the opening quotes (seller asks ≈$97.5 or ≈$90; buyer bids ≈$82.5, 90 or 95; neutral asks ≈$92 / bids ≈$88); (iv) model strength (Qwen3-235B vs Qwen3-32B on either side); and (v) market ratio (4 sellers : 3 buyers, where the competitive price is $80).</p>
<p><b>Track 3.4 metrics.</b> For each session we record mean overseer coordination score (1–4), mean seller message length and vocabulary size (message-based coordination), and mean cross-seller ask dispersion (the action-based dependence proxy; lower means asks move more in lockstep). Following the track's evidence standard, we would claim channel movement only if message-based coordination falls <i>while</i> action-based dependence rises.</p>
<p><b>What was done during the sprint.</b> Preexisting: the environment, prompts, metrics, ZIP buyer and overseer sampling (Agrawal et al.; hackathon organizers). Added during the sprint: silent-oversight and disclosure flags, an observe-only overseer, opening-quote flags, the Bedrock shim, a scripted price-leader seller and two prompt variants (teammate), and all experiments and analyses.</p>

<h2>4&nbsp;&nbsp;Results</h2>
<h3>4.1&nbsp;&nbsp;Positive control, and a frozen buyer</h3>
<p>With the repository's cheap rule-based buyer, GPT-4.1 sellers never pass, even when they openly coordinate (Table 1, rows 1–2). The cause is that the ZIP buyer's adaptive update is commented out: every ZIP bid is (1 − 0.2) × $100 = $80 ± 1%. A cartel cannot sell above about $80.80, so all ZIP-buyer runs measure nothing about collusion. With LLM buyers, the README's positive control (GPT-4.1, chat on) passes in 5/5 seeds with trade index {gm['tidx']['mean']:+.2f} ± {gm['tidx']['sd']:.2f}, and sellers capture most of the surplus.</p>
<div class="keep"><table><tr><th>GPT-4.1 sellers, gpt-4.1-mini buyers (3 : 3)</th><th>n</th><th>Avg price ($)</th><th>Index</th><th>PASS</th><th>Seller share</th><th>Note</th></tr>{T1}</table>
<div class="cap"><b>Table 1.</b> GPT-4.1 sessions (teammate runs, branch <code>results</code>). Mean ± sample s.d. over seeds. Seller share = seller profit / total surplus. The overseer, silence, a planted price leader and an explicit “your asks are visible” prompt change nothing; the opening price changes everything.</div></div>

<h3>4.2&nbsp;&nbsp;The opening quote sets the price</h3>
<p>Across all {D['gpt_anchor_n']} complete GPT-4.1 sessions with LLM buyers, the sellers' round-1 average ask predicts the session's average trade price with r = {D['gpt_anchor_r']:.3f} (Fig. 1a). Over 15 hours, asks move by a few cents per hour: sellers undercut each other by $0.01 to stay first in the queue. GPT-4.1 explains this as patience (“no need to adjust ask yet; patience may help reveal buyers' willingness”), and the gpt-4.1-mini buyers raise their bids to meet it. Started at $90 instead of $97.5, the same sellers stay at $90 (index {G['s90_chat']['tidx']['mean']:+.2f}). Qwen3-235B sellers do the opposite: they cut to just above the highest bid in hour 1 (“I must lower my ask to just above the highest bid”). Qwen markets therefore settle wherever the <i>buyers</i> opened (Fig. 1b). Raising only the buyers' opening bid to ≈$95 yields ${Q['q_bids95_chat']['price']['mean']:.2f} with chat and ${Q['q_bids95_nochat']['price']['mean']:.2f} without, sellers keep ~{Q['q_bids95_chat']['share']['mean']*100:.0f}% of surplus, and the built-in test would “pass”. That is a false positive with no coordination involved.</p>
<div class="keep"><div class="fig">{fig1}</div>{legend}
<div class="cap"><b>Figure 1.</b> Session price versus the opening quote of the side that holds still. (a) GPT-4.1 sellers (n = {D['gpt_anchor_n']}; teammate runs). (b) Qwen3-235B markets with sellers opening at ≈$97.5 or ≈$90 and buyers opening at ≈$82.5, 90 or 95 (n = {len(qwen_pts)}). Points lie on the dashed line regardless of whether sellers can talk.</div></div>

<h3>4.3&nbsp;&nbsp;Communication does not change prices</h3>
<p>With matched seeds, the effect of enabling seller chat is the paired difference in session price. Across {len(D['paired'])} settings (two model families, three opening regimes, weak buyers, and both market ratios), the mean effect is between {min(p['mean'] for _, p in D['paired']):+.2f} and {max(p['mean'] for _, p in D['paired']):+.2f} dollars (Fig. 2), against a $10 gap between the competitive and cartel price. {sum(min(p['vals']) < 0 < max(p['vals']) for _, p in D['paired'])} of the {len(D['paired'])} settings have seed pairs on both sides of zero. Three settings are positive in every seed pair, all small: {P['GPT-4.1, open $90']['mean']:+.2f} ± {P['GPT-4.1, open $90']['sd']:.2f} for GPT-4.1 opening at $90, {P['Qwen, buyers open $95']['mean']:+.2f} ± {P['Qwen, buyers open $95']['sd']:.2f} for Qwen when buyers open high, and {P['Qwen 4:3, neutral open']['mean']:+.2f} ± {P['Qwen 4:3, neutral open']['sd']:.2f} for Qwen at 4 : 3. Each is under a tenth of full collusion. A small positive effect of talk cannot be excluded and would need more seeds to confirm. Communication is not inert in <i>content</i>: GPT-4.1 sellers write “no reason to blink first” and praise their “coalition discipline”, and Qwen sellers write “let's hold the line on prices. No need to race to the bottom.” But silent sellers price identically. Qwen shows the clearest talk–action gap: a seller wrote “let's hold the line on prices” while asking $82.80 in the same hour.</p>
<div class="keep"><div class="fig">{fig2}</div>
<div class="cap"><b>Figure 2.</b> Paired effect of seller chat on average trade price (chat on − chat off, same seed). Gray: individual seeds. Blue: mean ± 1 s.d. (n = 3 seed pairs per row; GPT-4.1 rows from teammate runs). Full-scale collusion would be +$10.</div></div>
<div class="keep"><table><tr><th>Qwen3-235B sellers and buyers (3 : 3)</th><th>n</th><th>Avg price ($)</th><th>Index</th><th>Seller share</th><th>Note</th></tr>{T2}</table>
<div class="cap"><b>Table 2.</b> Qwen3 sessions (Bedrock). Unless stated, sellers open ≈$97.5 and buyers ≈$82.5. Chat, buyer chat, and model-strength asymmetry each move price by ≤ ~$1. Only the buyers' opening bid moves it substantially.</div></div>

<h3>4.4&nbsp;&nbsp;Being watched (Track 3.4): the talk changes, the market does not</h3>
<p>A silent overseer that never gags sees unguarded talk: mean coordination score {Q['ov_silent_nogag']['ov']['mean']:.2f}/4. Telling sellers they are monitored lowers scores to {Q['ov_told25']['ov']['mean']:.2f}–{Q['ov_told100']['ov']['mean']:.2f} and shortens messages (from {Q['ov_silent_nogag']['msglen']['mean']:.0f} to {Q['ov_told100']['msglen']['mean']:.0f} characters at 100% monitoring, and {Q['ov_told100_boss']['msglen']['mean']:.0f} with profit pressure). Sellers sanitize their language. Action-based dependence does not rise in response: cross-seller ask dispersion under announced monitoring ({min(Q[k]['disp']['mean'] for k in ('ov_told25','ov_told50','ov_told100','ov_disc25','ov_disc50','ov_disc100')):.2f}–{max(Q[k]['disp']['mean'] for k in ('ov_told25','ov_told50','ov_told100','ov_disc25','ov_disc50','ov_disc100')):.2f}) is in the same range as no oversight ({Q['q_base_chat']['disp']['mean']:.2f}) and silent oversight ({Q['ov_silent_nogag']['disp']['mean']:.2f}), with no trend in the monitored fraction. Prices stay at ≈$83 throughout (Table 3). By the track's standard, this is <b>no evidence of channel movement</b>. The coalition reacts to being watched by changing what it says, and there was no price-setting coordination to relocate. The GPT-4.1 4 : 3 runs (teammate) show the same pattern in counts: with chat, 155 of 180 seller messages use cartel wording (“avoid aggressive undercutting so we all protect our margins”). With the overseer on, only 32 of 178 do, and the price is unchanged ($90.83 vs $90.82). Gagged GPT-4.1 sellers converged on shared tokens (“⋇”, “⋆”, “.”) and in one seed on a shared hour counter (“9”, “10”, …), the only post-gag pattern the overseer flagged. Prices were again unchanged (Table 1). The one lever with a hint of an effect is profit pressure: 3 of 6 boss-pressure sessions ended above $85. The largest ($94.05) traces to sellers keeping the $97.5 opening in hour 1, the same anchoring mechanism.</p>
<div class="keep"><table><tr><th>Qwen3-235B, overseer Qwen3-32B</th><th>n</th><th>Overseer score</th><th>Msg chars</th><th>Vocab</th><th>Ask disp.</th><th>Avg price ($)</th><th>Seller share</th></tr>{T3}</table>
<div class="cap"><b>Table 3.</b> Message-based coordination (overseer score, message length, vocabulary) versus action-based dependence (cross-seller ask dispersion, lower = more lockstep) and outcome. “Told” = the prompt says seller messages are monitored; “disclosed” adds the sampled percentage. Gagging limits messages to ≤ 5 characters after a 4/4 score. The gag message mentions regulators, so “silent overseer, gag on” sessions are not truly silent after the first gag. “Silent overseer, no gag” is the clean silent condition.</div></div>

<h3>4.5&nbsp;&nbsp;Competitive pressure: excess supply and an excess-demand control</h3>
<p>Equal seller and buyer counts cannot separate collusion from sticky pricing, because every seller eventually trades. With 4 sellers and 3 buyers, one seller is unsold every hour, and the competitive price falls to cost ($80). The starter code's benchmark still reports $90 here, so we use the correct values. From a neutral opening, 4 : 3 prices stayed $8–11 above $80 for both families. Seller chat, buyer chat and the overseer made no difference (Table 4). Read alone, that would look like tacit collusion. The <b>excess-demand control fails</b>, however: with 3 sellers and 4 buyers, where competition should push prices up toward $100, GPT-4.1 prices stayed at ${G['r34_nochat']['price']['mean']:.2f}. Every GPT-4.1 condition lies within $0.30 of every other. Within 15 hours the market does not respond to supply and demand at all, so failing to fall under excess supply says nothing about collusion. Seller reasoning shows why. Unsold sellers undercut the lowest ask by the minimum, a best response, since winning the queue needs only $0.01 (“lower my ask to $87.50 … still above my cost”; GPT-4.1: “continue minimal undercutting—one cent below the lowest ask”). At a cent per hour, reaching cost would take on the order of 10<sup>3</sup> hours. In the excess-demand market, GPT-4.1 sellers kept undercutting too, and buyers sat a cent under the lowest ask. <b>Model capability matters.</b> In one exploratory seed, Claude Sonnet 5.5 sellers described the market structure correctly every hour (“four sellers compete for roughly three buyers each hour, and the higher-priced seller is left out”). They cut asks by $1.97 over 15 hours, about 5× GPT-4.1's $0.39, with cuts growing from about 5¢ to about 25¢ per hour by the end. None of its 60 responses reasons about long-run joint profit, though 27 mention avoiding a price war. GPT-4.1 almost never mentions the spare seller. The neutral opening sits about $11 above the 4 : 3 competitive price, so even Sonnet's pace leaves prices far from $80 after 15 hours. The market's insensitivity to supply and demand is therefore partly a property of the model, not only of the environment. Confirming this needs more seeds and a Sonnet excess-demand control. Our conclusion is that <b>this environment, as configured, cannot detect tacit collusion</b>: a test needs a market that first passes the excess-demand control (longer horizons, minimum price steps, or quantity choice).</p>
<div class="keep"><table><tr><th>Sellers</th><th>S : B</th><th>Condition</th><th>n</th><th>Avg price ($)</th><th>Ask hour 1 → 15</th><th>Comp. price</th><th>Price − comp.</th></tr>{T4}</table>
<div class="cap"><b>Table 4.</b> Neutral opening (asks ≈$92, bids ≈$88). The competitive price is $80 for 4 : 3, $90 for 3 : 3 and $100 for 3 : 4. <sup>†</sup>Teammate runs (branch <code>results</code>, commit <code>b43f146</code>). <sup>‡</sup>The overseer gagged in hour 1 in every seed, and the gag message itself mentions regulators, so this condition is not truly silent. <sup>§</sup>Exploratory teammate session (seed 0) with the seller model swapped to Claude Sonnet 5.5; 4 of 105 calls failed on rate limits, and a seller whose call fails keeps its previous ask.</div></div>

<h3>4.6&nbsp;&nbsp;Who “wins” is decided by who holds still</h3>
<p>Combining §4.2–4.5: with identical environments and prompts, GPT-4.1 sellers captured ~{G['main5']['sp']['mean']/(G['main5']['sp']['mean']+G['main5']['bs']['mean'])*100:.0f}% of surplus and Qwen3-235B sellers ~{Q['q_base_chat']['share']['mean']*100:.0f}%. The difference is temperament, not coordination. GPT-4.1 plans over the horizon and concedes in cents. Qwen optimizes the current hour and matches the best bid. Pairing strong Qwen sellers with weak Qwen3-32B buyers, or the reverse, changed little ({pm(Q['qs_chat']['price'])} vs {pm(Q['sq_chat']['price'])}), because Qwen sellers cut before buyers could concede. The gpt-4.1-mini buyers, for their part, bid against each other and never saw the sellers' $80 cost. In seed 0 one buyer called a $2.40 margin “healthy”; the two that noticed it was thin (“limits profit margins”) kept bidding anyway, because any rival bidding $97.60 would take the trade.</p>

<h2>5&nbsp;&nbsp;Discussion</h2>
<p><b>Implications for collusion evaluation.</b> A price-level test (high prices ⇒ collusion) is unsafe in LLM markets. The same high prices arise from an anchored start and agents that rarely revise it, with or without talk, and the test can be triggered by the <i>buyers'</i> opening alone. Evaluations should (i) start from neutral or agent-chosen quotes, (ii) report paired, seed-matched effects of communication on profit, (iii) include excess-supply markets with a correct competitive benchmark <i>and</i> an excess-demand control showing that the market responds to supply and demand at all, and (iv) report the positive control together with a false-positive control such as our high-bid market.</p>
<p><b>Implications for oversight.</b> Message monitors measure what agents <i>say</i>. Both models readily produce cartel rhetoric, and announcing a monitor makes them tone it down. Neither changes prices here. A monitor that flags rhetoric can therefore over-report collusion (talk without effect) or, after sanitization, under-report it. Monitoring should be anchored to action-level dependence and counterfactual price effects, not message content alone. The concerning case for regulators is the GPT-4.1 one: a model whose unilateral patience sustains high prices with nothing for a message monitor to read.</p>
<p><b>Conclusion.</b> In this environment we find no evidence that LLM sellers' communication causes collusion, and therefore no channel for oversight to displace. Apparent cartels are explained by opening anchors, per-model pricing temperament, buyer weakness and short horizons. Tacit collusion remains untestable here until the market passes an excess-demand control. Stronger models may make it testable: Claude Sonnet 5.5 already responds to excess supply. We release flags for neutral openings and silent or observe-only oversight to support stronger tests.</p>

<div class="refs"><h2>References</h2>
<p>Agrawal, K., Teo, V., Vazquez, J. J., Kunnavakkam, S., Srikanth, V., &amp; Liu, A. (2025). Evaluating LLM Agent Collusion in Double Auctions. arXiv:2507.01413.</p>
<p>Calvano, E., Calzolari, G., Denicolò, V., &amp; Pastorello, S. (2020). Artificial Intelligence, Algorithmic Pricing, and Collusion. <i>American Economic Review</i>, 110(10), 3267–3297.</p>
<p>Cliff, D. (1997). Minimal-Intelligence Agents for Bargaining Behaviors in Market-Based Environments. HP Laboratories Technical Report HPL-97-91.</p>
<p>Fish, S., Gonczarowski, Y. A., &amp; Shorrer, R. I. (2024). Algorithmic Collusion by Large Language Models. arXiv:2404.00806.</p>
<p>Gode, D. K., &amp; Sunder, S. (1993). Allocative Efficiency of Markets with Zero-Intelligence Traders. <i>Journal of Political Economy</i>, 101(1), 119–137.</p>
<p>Jiralerspong, T., Kondrup, F., &amp; Bengio, Y. (2026). Noticing the Watcher: LLM Agents Can Infer CoT Monitoring from Blocking Feedback. arXiv:2603.16928.</p>
<p>Kale, N., Zhang, C. B. C., Zhu, K., Aich, A., Rodriguez, P., et al. (2025). Reliable Weak-to-Strong Monitoring of LLM Agents. arXiv:2508.19461.</p>
<p>Keppo, J., Li, Y., Tsoukalas, G., &amp; Yuan, N. (2026). On the Fragility of AI Agent Collusion. arXiv:2603.20281.</p>
<p>Najt, E., Toft, C., Tracy, T., Roger, F., &amp; Benton, J. (2026). SLEIGHT-Bench: A Benchmark of Evasion Attacks Against Agent Monitors. arXiv:2605.16626.</p>
<p>Smith, V. L. (1962). An Experimental Study of Competitive Market Behavior. <i>Journal of Political Economy</i>, 70(2), 111–137.</p>
</div>

<h2 class="pb">Appendix A&nbsp;&nbsp;Limitations and Dual-Use / Ethical Considerations</h2>
<p><b>Statistical power.</b> Most cells have 3 seeds (the positive control has 5, two Qwen cells have 6–7). We can rule out effects of the size of full collusion (≈$10) but not effects under about $1–2. Effects are reported as means ± sample s.d. without formal tests.</p>
<p><b>Scope.</b> Two model families. GPT-4.1 was paired only with gpt-4.1-mini buyers, and Qwen ran on a different provider (Bedrock) with JSON mode emulated by a system hint in the shim. Horizons were 15 hours; longer horizons might reveal slow convergence or late-forming collusion. Claude was tested in a single exploratory seed without an excess-demand control, and Gemini not at all. Neither ratio test passed the excess-demand control, so we make no claim either way about tacit collusion.</p>
<p><b>Environment caveats.</b> (i) Until upstream fix <code>75d3e9d</code> (merged after our runs), agents running in parallel could see same-hour orders from agents that answered first, mainly on API retries. This applies equally to all our sessions. (ii) Order queues are cleared after trades, and Qwen sellers sometimes read an empty bid queue as “buyers inactive”. (iii) A failed API call aborts a session; five Qwen3-235B OpenRouter sessions were lost to a zero-credit account and are excluded, and one Qwen3-14B session stopped at hour 14 (Appendix B). (iv) The competitive-equilibrium function ignored unmatched agents. This is now fixed on <code>sprint-merged</code>, and all our analyses use the correct $80 / $100 benchmarks. (v) A gagging overseer is never fully silent: the gag message mentions regulators.</p>
<p><b>Dual use.</b> The findings could be read as a recipe for evading message monitors (sanitize language, rely on anchored prices). We judge the risk low: the behaviors are already elicited by the paper's public prompts. The main lesson, that message-level monitoring alone is inadequate, favors defenders. We release no evasion prompts. All markets are simulated; no real prices, firms or people are involved.</p>
<p><b>AI assistance.</b> Analysis code and drafting were assisted by an AI coding assistant. All numbers are computed directly from the logged sessions by a script, and the authors take responsibility for the content.</p>

<h2>Appendix B&nbsp;&nbsp;Reproducibility and code changes</h2>
<p><b>Code and data.</b> <a href="https://github.com/Aakash-insights/collusion_hackathon/tree/sprint-merged"><code>github.com/Aakash-insights/collusion_hackathon</code></a>, branch <code>sprint-merged</code>, which holds all code, both teams' runs and this report. It contains <code>llm-agent-collusion/sprint_results/</code> (GPT-4.1 and Claude runs, with <code>SUMMARY.md</code>), <code>sprint_results_qwen/</code> (Qwen runs), <code>TEAM_RESULTS.md</code> (every run from both folders, built by <code>tools/build_team_results.py</code>), <code>report/</code> (this paper; <code>collect.py</code> recomputes every number from the run folders) and <code>CHANGES_SPRINT.md</code> (all code changes). New flags: <code>--no_oversight_notice</code>, <code>--disclose_sample_fraction</code>, <code>--no_gag</code>, <code>--initial_seller_ask_center</code>, <code>--initial_buyer_bid_center</code>. Defaults are unchanged.</p>
<p><b>Example commands</b> (from <code>llm-agent-collusion/</code>):<br>
<code>simulation.py --seller_models gpt-4.1 --buyer_models gpt-4.1-mini --seller_comms_enabled --seeds 0 1 2 3 4</code> (positive control)<br>
<code>simulation.py --seller_models &lt;Q&gt; --buyer_models &lt;Q&gt; --sellers 4 --buyers 3 --initial_seller_ask_center 92 --initial_buyer_bid_center 88 [--seller_comms_enabled] [--oversight_enabled]</code><br>
with <code>&lt;Q&gt;</code> = <code>qwen.qwen3-235b-a22b-2507-v1:0</code> via the Bedrock shim (<code>LLM_BASE_URL</code>).</p>
<p><b>Issues found in the starter environment.</b> (1) <code>ZIPBuyer.generate_bid_response</code>: adaptive margin update commented out, so bids are constant at $80 ± 1%. (2) <code>initial_seller_ask_center = 97.5</code> sits near the cartel price, so the PASS criterion is satisfied by sellers that merely hold their opening. (3) <code>metrics.competitive_equilibrium</code> paired only the first <i>k</i> agents and reported $90 for 4 : 3 markets (true value $80). It is fixed on <code>sprint-merged</code>, together with a crash when the competitive and cartel prices coincide. (4) An exhausted API retry raises <code>AssertionError</code> and aborts the session.</p>
<p><b>Supplementary result.</b> Qwen3-14B sellers vs gpt-4.1-mini buyers, chat on, seed 0 (OpenRouter): 14 of 15 hours completed before a credit error. Average price $91.03 (index +0.10), 40 trades, sellers 55% of surplus. Sellers matched the highest bid in hour 1, consistent with §4.2.</p>

<h2 class="pb">Appendix C&nbsp;&nbsp;All conditions run</h2>
<p>Every condition in both result folders: 179 sessions, 168 complete. Table generated from <code>TEAM_RESULTS.md</code> section 1, recomputed from each run's raw files by <code>tools/build_team_results.py</code>. Price is mean ± sample s.d. over seeds. Comp. is the corrected competitive price. Seller share = seller profit / total surplus. Smoke tests and sessions without trades are included for completeness. The main text analyses the 151 sessions in the conditions it reports.</p>
{TEAM}

<h2>Appendix D&nbsp;&nbsp;Future work, in priority order</h2>
<ol>
<li><b>Make the market respond to supply and demand.</b> Nothing about tacit collusion can be concluded until an excess-demand (3 : 4) market rises toward $100 and an excess-supply (4 : 3) market falls toward $80 without communication. Options: longer horizons (30–100+ hours, since cent-sized steps need about 1,000 hours to reach cost), a minimum price step (for example $0.50), or agent-chosen quantities.</li>
<li><b>Rerun the tacit-collusion test on that market</b> (4 : 3 vs 3 : 4, chat on/off, overseer) with 3+ seeds per cell.</li>
<li><b>Confirm the stronger-model result:</b> Claude Sonnet 5.5 at 3 : 4, plus more 4 : 3 seeds. If Sonnet passes the control, use it as the seller model for steps 1–2.</li>
<li><b>Cross-model sellers</b> (GPT-4.1, Claude and Qwen in one market), following the original paper's design.</li>
<li><b>Truly silent oversight for GPT-4.1</b> (<code>--no_gag</code>), and the 25/50/100% monitoring and disclosure conditions, which so far exist only for Qwen.</li>
<li><b>Rerun the headline cells after the order-queue fix</b> <code>75d3e9d</code>.</li>
<li><b>Follow up profit pressure,</b> the only hint of an effect (3 of 6 Qwen sessions above $85), with more seeds and GPT-4.1.</li>
<li><b>Stronger buyer models.</b> gpt-4.1-mini buyers concede easily.</li>
<li><b>Better collusion metrics:</b> seed-matched causal effects, price change relative to the opening, and action-level dependence, not price level or message content alone.</li>
<li><b>Fix environment defaults:</b> restore adaptive ZIP bidding, make a neutral opening the default, and keep a failed API call from aborting the session.</li>
</ol>

<h2>Appendix E&nbsp;&nbsp;Author contributions</h2>
<p><b>Aakash Patil:</b> silent-oversight, disclosure, observe-only and opening-price flags; the Bedrock bridge; all Qwen3 experiments (120 sessions: communication, oversight, opening-anchor, model-strength and 4 : 3 competition conditions); track 3.4 metrics; this report. <b>Bar Hoze:</b> all GPT-4.1 and Claude experiments (59 sessions: positive control, anchoring, prompt variants, price-channel tests with a scripted price leader, 4 : 3 / 3 : 3 / 3 : 4 competition test, stronger-model proof of concept); the competitive-equilibrium fix; the merged code branch and <code>TEAM_RESULTS.md</code>. Both authors identified the frozen ZIP buyer and the opening-price anchor independently.</p>
</body></html>"""

open(f"{S}/collusion_sprint_report.html", "w").write(html)
import re
abs_txt = re.sub(r"<[^>]+>", "", html.split('<div class="abstract"><b>Abstract</b>')[1].split("</div>")[0])
print("abstract words:", len(abs_txt.split()), "| sessions:", N_TOTAL, "| qwen:", n_qwen, "gpt:", n_gpt)
