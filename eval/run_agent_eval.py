"""Agent eval — runs scripted scenarios and checks trajectory + endpoint assertions.

Unlike run_eval.py (which tests RAG answers with LLM-as-judge), this eval is
fully DETERMINISTIC — every assertion is a hand-coded check on the trajectory
or the final response. No judge noise, no extra LLM calls, fast to run.

Usage:
    uv run python -m eval.run_agent_eval
"""

import json
import uuid
from pathlib import Path

from langchain_core.messages import HumanMessage

from agent.graph import build_graph, flush_langfuse, get_langfuse_handler
from agent.guardrails import REFUSAL_MESSAGE

SCENARIOS_PATH = Path(__file__).parent / "agent_scenarios.jsonl"
RESULTS_PATH = Path(__file__).parent / "agent_results.json"


def load_scenarios() -> list[dict]:
    """Read scenarios from JSONL (one JSON object per line)."""
    scenarios = []
    with open(SCENARIOS_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                scenarios.append(json.loads(line))
    return scenarios


def run_scenario(agent_graph, scenario: dict, langfuse_handler=None) -> dict:
    """Run one scenario and extract its trajectory + final response."""
    thread_id = f"eval-{scenario['id']}-{uuid.uuid4().hex[:6]}"
    final_state = None

    # TODO D (observability): Add the Langfuse callback to config so each
    #   scenario becomes a trace in the Langfuse UI. Tag it with the
    #   scenario id so you can find specific failures later.
    #
    #   config = {
    #       "configurable": {"thread_id": thread_id},
    #       "recursion_limit": 15,
    #       "callbacks": [langfuse_handler] if langfuse_handler else [],
    #       "metadata": {"scenario_id": scenario["id"], "category": scenario["category"]},
    #       "run_name": f"eval:{scenario['id']}",
    #   }
    #
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 15,
        "callbacks": [langfuse_handler] if langfuse_handler else [],
        "metadata": {"scenario_id": scenario["id"], "category": scenario["category"]},
        "run_name": f"eval:{scenario['id']}",
    }
    # Why metadata + run_name? In the Langfuse UI you can filter traces
    # by metadata.scenario_id — invaluable when you have 15 scenarios and
    # want to click straight to the one that failed.

    # Send each message in sequence on the SAME thread_id (multi-turn support)
    for message in scenario["messages"]:
        final_state = agent_graph.invoke(
            {"messages": [HumanMessage(content=message)]},
            config=config,
        )

    # Extract trajectory data from the full message history
    all_msgs = final_state["messages"]
    tool_calls = []
    for m in all_msgs:
        if m.type == "ai" and getattr(m, "tool_calls", None):
            for tc in m.tool_calls:
                tool_calls.append(tc["name"])

    final_response = all_msgs[-1].content or ""
    return {
        "tool_calls": tool_calls,
        "final_response": final_response,
    }


def check_assertions(scenario: dict, result: dict) -> list[dict]:
    """Run every assertion in the scenario against the actual result.

    Returns a list of {"name": ..., "passed": bool, "detail": ...} records
    so we can print a detailed pass/fail report.
    """
    a = scenario.get("assertions", {})
    checks = []

    # tools_called_contains — every listed tool appears at least once
    if "tools_called_contains" in a:
        expected = a["tools_called_contains"]
        actual = result["tool_calls"]
        missing = [t for t in expected if t not in actual]
        checks.append(
            {
                "name": "tools_called_contains",
                "passed": len(missing) == 0,
                "detail": f"expected⊇{expected}, actual={actual}, missing={missing}",
            }
        )

    # tools_called_ordered — listed tools appear in this exact order (others may be interleaved)
    if "tools_called_ordered" in a:
        expected = a["tools_called_ordered"]
        actual = result["tool_calls"]
        idx = 0
        for tool in actual:
            if idx < len(expected) and tool == expected[idx]:
                idx += 1
        checks.append(
            {
                "name": "tools_called_ordered",
                "passed": idx == len(expected),
                "detail": f"expected order={expected}, actual={actual}, matched={idx}/{len(expected)}",
            }
        )

    # tools_not_called — none of these tools were used
    if "tools_not_called" in a:
        forbidden = a["tools_not_called"]
        actual = result["tool_calls"]
        violations = [t for t in forbidden if t in actual]
        checks.append(
            {
                "name": "tools_not_called",
                "passed": len(violations) == 0,
                "detail": f"forbidden={forbidden}, actual={actual}, violations={violations}",
            }
        )

    # response_contains — every listed substring appears (case-insensitive)
    if "response_contains" in a:
        expected = a["response_contains"]
        response_lower = result["final_response"].lower()
        missing = [s for s in expected if s.lower() not in response_lower]
        checks.append(
            {
                "name": "response_contains",
                "passed": len(missing) == 0,
                "detail": f"missing substrings: {missing}",
            }
        )

    # response_refused — final response matches the canonical refusal message
    if "response_refused" in a:
        expected = a["response_refused"]
        actual = result["final_response"].strip() == REFUSAL_MESSAGE.strip()
        checks.append(
            {
                "name": "response_refused",
                "passed": expected == actual,
                "detail": f"expected={expected}, actual={actual}",
            }
        )

    # max_tool_calls — total calls ≤ this number (efficiency check)
    if "max_tool_calls" in a:
        limit = a["max_tool_calls"]
        actual = len(result["tool_calls"])
        checks.append(
            {
                "name": "max_tool_calls",
                "passed": actual <= limit,
                "detail": f"limit={limit}, actual={actual}",
            }
        )

    return checks


def main() -> None:
    scenarios = load_scenarios()
    print(f"Loaded {len(scenarios)} scenarios from {SCENARIOS_PATH.name}\n")

    agent_graph = build_graph()
    langfuse_handler = get_langfuse_handler()
    if langfuse_handler:
        print("  [OBSERVABILITY] Langfuse tracing enabled → http://localhost:3000\n")

    all_results = []
    passed_scenarios = 0

    for scenario in scenarios:
        print(f"── {scenario['id']} ({scenario['category']}) ──")
        print(f"   {scenario['description']}")

        try:
            result = run_scenario(agent_graph, scenario, langfuse_handler)
        except Exception as e:
            print(f"   💥 ERROR running scenario: {e}\n")
            all_results.append({"id": scenario["id"], "error": str(e), "passed": False})
            continue

        checks = check_assertions(scenario, result)
        scenario_passed = all(c["passed"] for c in checks)
        passed_scenarios += int(scenario_passed)

        status = "✅ PASS" if scenario_passed else "❌ FAIL"
        print(f"   {status}  tools={result['tool_calls']}")
        for c in checks:
            mark = "✓" if c["passed"] else "✗"
            print(f"      {mark} {c['name']:25} — {c['detail']}")
        print()

        all_results.append(
            {
                "id": scenario["id"],
                "category": scenario["category"],
                "passed": scenario_passed,
                "tool_calls": result["tool_calls"],
                "final_response": result["final_response"][:500],
                "checks": checks,
            }
        )

    # Summary
    total = len(scenarios)
    print("=" * 60)
    print(f"Result: {passed_scenarios}/{total} scenarios passed")
    print("=" * 60)

    # Category breakdown
    by_category: dict[str, list[bool]] = {}
    for r in all_results:
        by_category.setdefault(r.get("category", "unknown"), []).append(r["passed"])
    for cat, results in sorted(by_category.items()):
        print(f"  {cat:20} {sum(results)}/{len(results)}")

    # Persist results for later inspection
    RESULTS_PATH.write_text(json.dumps(all_results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nFull results saved to {RESULTS_PATH.name}")

    # Flush buffered traces to Langfuse before exiting
    flush_langfuse()


if __name__ == "__main__":
    main()
