"""A/B comparison of three LLM backends on the agent eval suite.

Runs eval/agent_scenarios.jsonl through each backend in turn, capturing:
  - pass rate     (same deterministic assertions as run_agent_eval.py)
  - latency       (wall-clock per scenario)
  - tool calls    (count + which tools)
  - tokens + cost (from response usage_metadata)

Writes one combined JSON to eval/backend_comparison.json and prints a markdown
table you can paste into README.md and HANDOFF.md.

Usage:
    uv run python -m eval.compare_backends
    uv run python -m eval.compare_backends --backends deepseek   # one only
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import uuid
from pathlib import Path

from langchain_core.messages import HumanMessage

# We import the eval helpers but NOT agent.graph at module level — graph.py
# builds its LLM at import time, so we have to reload it after setting
# LLM_BACKEND for each backend in the loop.
from eval.run_agent_eval import check_assertions, load_scenarios

RESULTS_PATH = Path(__file__).parent / "backend_comparison.json"

# Prices in USD per 1M tokens. Groq's free tier → cost stays at 0.
# (For DeepSeek we use the standard tier; cache-hit pricing is cheaper.)
PRICING = {
    "deepseek": {"input_per_m": 0.27, "output_per_m": 1.10},
    "groq": {"input_per_m": 0.0, "output_per_m": 0.0},  # free tier
}

# Per-backend pause between scenarios — used if a provider rate-limits.
# Neither remaining backend needs throttling at the moment.
PER_SCENARIO_DELAY_S = {
    "deepseek": 0.0,
    "groq": 0.0,
}


# ---------------------------------------------------------------------------
# Per-scenario runner — instrumented version of run_agent_eval.run_scenario
# ---------------------------------------------------------------------------


def run_scenario_instrumented(agent_graph, scenario: dict) -> dict:
    """Run one scenario and return trajectory + latency + token usage.

    This is the per-scenario equivalent of run_agent_eval.run_scenario, but
    it also captures wall-clock latency and per-call token usage.

    TODO 1 (timing):
        Wrap the for-loop over scenario["messages"] with time.perf_counter()
        to measure total wall-clock for the whole multi-turn conversation.
        Store the result in a local `latency_s` float.


    TODO 2 (token accounting):
        Each AIMessage from a LangChain chat model carries a
        `usage_metadata` dict that looks like:
            {"input_tokens": N, "output_tokens": M, "total_tokens": N+M}
        For each ai-typed message in final_state["messages"], sum these into
        input_tokens / output_tokens totals.
        Notes:
          - Some messages may not have usage_metadata (None or {}). Skip those.
          - This works the same way for ChatOpenAI and ChatGroq, but the
            actual values depend on what the provider returns. If Groq omits
            them, fall back to len(content)//4 as a rough estimate and note
            it in the docstring of summarize().
    """
    thread_id = f"compare-{scenario['id']}-{uuid.uuid4().hex[:6]}"
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 15,
    }

    # --- TODO 1: time the multi-turn loop ---
    start = time.perf_counter()
    final_state = None
    for message in scenario["messages"]:
        final_state = agent_graph.invoke(
            {"messages": [HumanMessage(content=message)]},
            config=config,
        )
    latency_s = time.perf_counter() - start

    # --- Trajectory extraction (same as run_agent_eval) ---
    all_msgs = final_state["messages"]
    tool_calls = [
        tc["name"]
        for m in all_msgs
        if m.type == "ai" and getattr(m, "tool_calls", None)
        for tc in m.tool_calls
    ]
    final_response = all_msgs[-1].content or ""

    # --- TODO 2: aggregate token usage from all AI messages ---
    # usage_metadata only exists on AIMessage (and even then can be None if
    # the provider didn't return usage). getattr + `or {}` makes both checks
    # one expression and avoids AttributeError on Human/Tool/System messages.
    input_tokens = 0
    output_tokens = 0
    for m in all_msgs:
        usage = getattr(m, "usage_metadata", None) or {}
        input_tokens += usage.get("input_tokens", 0)
        output_tokens += usage.get("output_tokens", 0)

    return {
        "id": scenario["id"],
        "category": scenario["category"],
        "tool_calls": tool_calls,
        "final_response": final_response,
        "latency_s": latency_s,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }


# ---------------------------------------------------------------------------
# Backend loop — sets env var, reloads agent.graph, runs all scenarios
# ---------------------------------------------------------------------------


def run_one_backend(label: str, scenarios: list[dict]) -> list[dict]:
    """Run all scenarios through one backend and return per-scenario records.

    The reload dance is necessary because agent/graph.py builds its LLM at
    module import time. If we just `import agent.graph` once, the second
    backend would silently reuse the first one's LLM.
    """
    import os

    os.environ["LLM_BACKEND"] = label

    # Drop any cached agent.graph + dependent modules so the next import
    # rebuilds the LLM with the new LLM_BACKEND.
    for mod_name in list(sys.modules):
        if mod_name == "agent.graph" or mod_name.startswith("agent.graph."):
            del sys.modules[mod_name]

    import agent.graph as graph_mod  # noqa: PLC0415 — must be after env+cache reset

    agent_graph = graph_mod.build_graph()

    print(f"  → LLM class: {type(graph_mod.llm).__name__}")
    print(
        f"  → model:     {getattr(graph_mod.llm, 'model_name', getattr(graph_mod.llm, 'model', '?'))}"
    )

    records = []
    delay = PER_SCENARIO_DELAY_S.get(label, 0.0)
    for i, scenario in enumerate(scenarios, start=1):
        print(f"  [{i:2d}/{len(scenarios)}] {scenario['id']:35} ", end="", flush=True)
        try:
            result = run_scenario_instrumented(agent_graph, scenario)
            checks = check_assertions(scenario, result)
            result["passed"] = all(c["passed"] for c in checks)
            result["checks"] = checks
            print(
                f"{'✅' if result['passed'] else '❌'}  "
                f"{result['latency_s']:5.2f}s  "
                f"{len(result['tool_calls'])} tools  "
                f"{result['input_tokens']:>5}in/{result['output_tokens']:>4}out"
            )
        except Exception as e:
            print(f"💥 {e}")
            result = {"id": scenario["id"], "error": str(e), "passed": False}
        records.append(result)
        if delay:
            time.sleep(delay)
    return records


# ---------------------------------------------------------------------------
# Aggregation + markdown reporting
# ---------------------------------------------------------------------------


def _aggregate(records: list[dict], label: str) -> dict:
    """Reduce one backend's per-scenario records to a single summary row.

    Errored scenarios (no "latency_s" key) are skipped for latency / token
    aggregates but still count as failures in the pass-rate denominator.
    """
    total = len(records)
    passed = sum(1 for r in records if r.get("passed"))

    ok = [r for r in records if "latency_s" in r]
    latencies = [r["latency_s"] for r in ok]
    total_tool_calls = sum(len(r.get("tool_calls", [])) for r in ok)
    total_input = sum(r.get("input_tokens", 0) for r in ok)
    total_output = sum(r.get("output_tokens", 0) for r in ok)

    # statistics.quantiles needs at least 2 data points; fall back to max
    # for tiny samples so the column never reads "n/a" in normal runs.
    median_latency = statistics.median(latencies) if latencies else 0.0
    if len(latencies) >= 2:
        p95_latency = statistics.quantiles(latencies, n=20)[18]
    else:
        p95_latency = max(latencies) if latencies else 0.0

    price = PRICING.get(label, {"input_per_m": 0.0, "output_per_m": 0.0})
    cost_usd = (total_input * price["input_per_m"] + total_output * price["output_per_m"]) / 1e6

    return {
        "backend": label,
        "pass_rate": f"{passed}/{total}",
        "median_latency_s": median_latency,
        "p95_latency_s": p95_latency,
        "total_tool_calls": total_tool_calls,
        "total_tokens": total_input + total_output,
        "cost_usd": cost_usd,
    }


def summarize(all_results: dict[str, list[dict]]) -> str:
    """Build a markdown comparison table from the per-backend records."""
    rows = [_aggregate(records, label) for label, records in all_results.items()]

    header = (
        "| Backend | Pass rate | Median latency | P95 latency | "
        "Total tool calls | Total tokens | Cost (USD) |"
    )
    sep = "|---|---|---|---|---|---|---|"
    body = [
        f"| `{r['backend']}` | {r['pass_rate']} | "
        f"{r['median_latency_s']:.2f}s | {r['p95_latency_s']:.2f}s | "
        f"{r['total_tool_calls']} | {r['total_tokens']:,} | "
        f"${r['cost_usd']:.4f} |"
        for r in rows
    ]
    return "\n".join([header, sep, *body])


# ---------------------------------------------------------------------------
# Per-scenario divergence — show where backends disagreed
# ---------------------------------------------------------------------------


def print_divergence(all_results: dict[str, list[dict]]) -> None:
    """Print scenarios where backends disagreed on pass/fail or tool-call count.

    With exactly two backends this is the most useful "see the difference"
    artifact: a row per scenario, marking which backend(s) passed, and
    flagging tool-call mismatches.
    """
    labels = list(all_results.keys())
    if len(labels) < 2:
        return

    # Build a per-scenario index keyed by scenario id.
    by_id: dict[str, dict[str, dict]] = {}
    for label, recs in all_results.items():
        for r in recs:
            by_id.setdefault(r["id"], {})[label] = r

    print("\n## Per-scenario divergence\n")
    print("| Scenario | " + " | ".join(labels) + " | tool-count diff |")
    print("|" + "---|" * (len(labels) + 2))

    diverged = 0
    for sid, by_label in by_id.items():
        row = []
        results_per_backend = [by_label.get(l, {}) for l in labels]
        # Pass/fail glyphs per backend
        for r in results_per_backend:
            if not r:
                row.append("—")
            elif r.get("passed"):
                row.append("✅")
            else:
                row.append("❌")

        # Tool-call counts
        tool_counts = [len(r.get("tool_calls", [])) for r in results_per_backend]
        tool_diff = max(tool_counts) - min(tool_counts) if tool_counts else 0

        # Only show rows where backends disagreed in some way
        passes = [r.get("passed", False) for r in results_per_backend]
        if len(set(passes)) == 1 and tool_diff == 0:
            continue
        diverged += 1

        diff_marker = f"{tool_diff}" if tool_diff else "0"
        print(f"| `{sid}` | " + " | ".join(row) + f" | {diff_marker} |")

    print(f"\n{diverged} of {len(by_id)} scenarios diverged between {' / '.join(labels)}.\n")


# ---------------------------------------------------------------------------
# Charts — write PNGs for the README writeup
# ---------------------------------------------------------------------------


def plot_results(all_results: dict[str, list[dict]], out_dir: Path) -> list[Path]:
    """Render two PNGs comparing backends. Returns the saved paths.

    chart 1 — aggregate.png         : 2x2 grid of pass rate, median + p95
                                       latency, total tool calls, total tokens.
    chart 2 — latency_per_scenario  : grouped bars, one group per scenario.
    """
    # Import matplotlib lazily so non-plot usage of this module stays light.
    import matplotlib.pyplot as plt  # noqa: PLC0415

    out_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []

    labels = list(all_results.keys())
    rows = [_aggregate(records, label) for label, records in all_results.items()]
    # Two strong, accessible colors — deepseek=indigo, groq=orange.
    palette = {"deepseek": "#5b21b6", "groq": "#ea580c", "openrouter": "#0891b2"}
    colors = [palette.get(l, "#666666") for l in labels]

    # --- chart 1: 2x2 aggregate ------------------------------------------------
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    fig.suptitle("LLM backend comparison — agent eval (15 scenarios)", fontsize=13, fontweight="bold")

    # Pass rate as a percentage
    pass_rates = [
        100 * sum(1 for r in all_results[l] if r.get("passed")) / len(all_results[l])
        for l in labels
    ]
    axes[0, 0].bar(labels, pass_rates, color=colors)
    axes[0, 0].set_title("Pass rate (%)")
    axes[0, 0].set_ylim(0, 100)
    for i, v in enumerate(pass_rates):
        axes[0, 0].text(i, v + 1.5, f"{v:.0f}%", ha="center", fontweight="bold")

    # Latency: median + p95 grouped
    x = range(len(labels))
    width = 0.35
    medians = [r["median_latency_s"] for r in rows]
    p95s = [r["p95_latency_s"] for r in rows]
    axes[0, 1].bar([i - width / 2 for i in x], medians, width, label="median", color=colors, alpha=0.95)
    axes[0, 1].bar([i + width / 2 for i in x], p95s, width, label="p95", color=colors, alpha=0.55, hatch="//")
    axes[0, 1].set_xticks(list(x))
    axes[0, 1].set_xticklabels(labels)
    axes[0, 1].set_title("Latency per scenario (s)")
    axes[0, 1].legend()

    # Total tool calls
    tool_calls = [r["total_tool_calls"] for r in rows]
    axes[1, 0].bar(labels, tool_calls, color=colors)
    axes[1, 0].set_title("Total tool calls (across 15 scenarios)")
    for i, v in enumerate(tool_calls):
        axes[1, 0].text(i, v + 0.3, str(v), ha="center", fontweight="bold")

    # Total tokens
    tokens = [r["total_tokens"] for r in rows]
    axes[1, 1].bar(labels, tokens, color=colors)
    axes[1, 1].set_title("Total tokens consumed")
    for i, v in enumerate(tokens):
        axes[1, 1].text(i, v + max(tokens) * 0.01, f"{v:,}", ha="center", fontweight="bold")

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    p1 = out_dir / "comparison_aggregate.png"
    fig.savefig(p1, dpi=120)
    plt.close(fig)
    saved.append(p1)

    # --- chart 2: per-scenario latency grouped bars ----------------------------
    # Build a stable scenario order from whichever backend has the most records.
    primary = max(all_results.values(), key=len)
    scenario_ids = [r["id"] for r in primary]

    fig, ax = plt.subplots(figsize=(12, max(4, 0.4 * len(scenario_ids))))
    y = range(len(scenario_ids))
    bar_h = 0.35

    for i, label in enumerate(labels):
        by_id = {r["id"]: r for r in all_results[label]}
        lats = [by_id.get(sid, {}).get("latency_s", 0.0) for sid in scenario_ids]
        offset = (i - (len(labels) - 1) / 2) * bar_h
        ax.barh([j + offset for j in y], lats, bar_h, label=label, color=palette.get(label, "#666"))

    ax.set_yticks(list(y))
    ax.set_yticklabels(scenario_ids, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Wall-clock latency per scenario (s)")
    ax.set_title("Per-scenario latency — DeepSeek vs Groq")
    ax.legend()
    fig.tight_layout()
    p2 = out_dir / "comparison_latency_per_scenario.png"
    fig.savefig(p2, dpi=120)
    plt.close(fig)
    saved.append(p2)

    return saved


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    # Windows legacy consoles default to a code page that can't encode emoji.
    # Force UTF-8 so the ✅/❌ glyphs in the divergence table don't crash.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--backends",
        nargs="+",
        default=["deepseek", "groq"],
        choices=["deepseek", "groq"],
        help="Subset of backends to run (default: both).",
    )
    parser.add_argument(
        "--from-json",
        action="store_true",
        help="Skip eval; just regenerate report + charts from eval/backend_comparison.json.",
    )
    parser.add_argument(
        "--no-charts",
        action="store_true",
        help="Skip PNG generation (faster; useful if you only want the text report).",
    )
    args = parser.parse_args()

    if args.from_json:
        if not RESULTS_PATH.exists():
            raise SystemExit(f"--from-json needs {RESULTS_PATH} to exist. Run without it first.")
        all_results: dict[str, list[dict]] = json.loads(
            RESULTS_PATH.read_text(encoding="utf-8")
        )
        print(f"Loaded cached results for: {list(all_results.keys())}\n")
    else:
        scenarios = load_scenarios()
        print(f"Loaded {len(scenarios)} scenarios.\n")

        all_results = {}
        for label in args.backends:
            print(f"\n=== {label.upper()} ===")
            all_results[label] = run_one_backend(label, scenarios)

        RESULTS_PATH.write_text(
            json.dumps(all_results, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"\nRaw results → {RESULTS_PATH}")

    # Only chart/diverge the backends we ran (or asked to compare).
    selected = (
        {l: all_results[l] for l in args.backends if l in all_results}
        if args.from_json
        else all_results
    )

    print("\n## Aggregate comparison\n")
    print(summarize(selected))
    print_divergence(selected)

    if not args.no_charts:
        charts_dir = Path(__file__).parent / "charts"
        saved = plot_results(selected, charts_dir)
        print("Charts saved:")
        for p in saved:
            print(f"  {p}")


if __name__ == "__main__":
    main()
