"""Evalutate the RAG pipeline against a golden dataset"""

import json
import os
import sys

from agent.llm import chat
from rag.answer import answer, format_context
from rag.retrieve import retrieve
from rag.retrieve_hybrid import retrieve_hybrid


GOLDEN_PATH = os.path.join(os.path.dirname(__file__), "golden.jsonl")


def load_golden(path: str) -> list[dict]:
    """Load question/expected pairs from JSONL."""
    # TODO 1: Read the file line by line, json.loads each line, return a list
    
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def judge_faithfulness(question: str, actual_answer: str, context: str) -> dict:
    """Use LLM to judge if the answer is faithful to the context (no hallucination)."""

    prompt = f"""You are an evaluation judge. Given a question, an answer, and the context \
    the answer was supposed to be based on, score the answer's FAITHFULNESS.

    Faithfulness means: does the answer ONLY contain information that is supported by the context? \
    An answer that adds facts not in the context is unfaithful (hallucination).

    Question: {question}
    Context: {context}
    Answer: {actual_answer}

    Score from 1 to 5:
    1 = completely made up, not in context at all
    2 = mostly hallucinated with some real info
    3 = partially faithful, some unsupported claims
    4 = mostly faithful, minor additions
    5 = fully faithful, everything is supported by context

    Respond with ONLY a JSON object: {{"score": <number>, "reason": "<one sentence>"}}"""

    reply = chat([{"role": "user", "content": prompt}], temperature=0.0)
    return json.loads(reply)


def judge_relevancy(question: str, actual_answer: str) -> dict:
    """Use LLM to judge if the answer actually addresses the question."""
    prompt = f"""You are an evaluation judge. Given a question and an answer, \
    score the answer's RELEVANCY.

    Relevancy means: does the answer actually address what was asked?

    Question: {question}
    Answer: {actual_answer}

    Score from 1 to 5:
    1 = completely irrelevant
    2 = vaguely related but doesn't answer the question
    3 = partially answers the question
    4 = answers the question but missing details
    5 = fully answers the question

    Respond with ONLY a JSON object: {{"score": <number>, "reason": "<one sentence>"}}"""

    reply = chat([{"role": "user", "content": prompt}], temperature=0.0)
    return json.loads(reply)


def hit_rate(retrieved_chunks: list[dict], expected_source: str | None) -> int:
    """Did the expected source appear in the retrieved chunks?

    Returns 1 if expected_source is found among retrieved chunks' sources,
    0 otherwise. If expected_source is None (e.g. questions that should
    trigger a "don't know" response), return 1 only if NOTHING relevant
    was retrieved — but for now just return None and skip these cases.
    """
    # TODO A1: If expected_source is None, return None (skip this case)
    if expected_source is None:
        return None
    # TODO A2: Collect the set of sources from retrieved_chunks
    sources = {c["source"] for c in retrieved_chunks}
    # TODO A3: Return 1 if expected_source in that set, else 0
    return 1 if expected_source in sources else 0
    


def run_eval(retrieval_only: bool = False,retriever: str = "dense"):
    """Run the eval. If retrieval_only=True, skip LLM answer + judges
    (free, fast — use this for retrieval sweeps)."""
    golden = load_golden(GOLDEN_PATH)
    results = []
    retrieve_fn = retrieve_hybrid if retriever == "hybrid" else retrieve

    for i, case in enumerate(golden, 1):
        question = case["question"]
        expected = case["expected"]
        expected_source = case.get("source")  # may be None
        print(f"\n[{i}/{len(golden)}] {question}")

        
        chunks_k3 = retrieve_fn(question, k=3)
        chunks_k5 = retrieve_fn(question, k=5)

        hit_at_3 = hit_rate(chunks_k3, expected_source)
        hit_at_5 = hit_rate(chunks_k5, expected_source)

        row = {
            "question": question,
            "expected": expected,
            "expected_source": expected_source,
            "retrieved_sources": [c["source"] for c in chunks_k5],
            "hit@3": hit_at_3,
            "hit@5": hit_at_5,
        }
        print(f"  Hit@3: {hit_at_3}  Hit@5: {hit_at_5}")

        if not retrieval_only:
            context_str = format_context(chunks_k5)
            actual_answer = answer(question)
            faith = judge_faithfulness(question, actual_answer, context_str)
            relev = judge_relevancy(question, actual_answer)
            row.update({
                "actual": actual_answer,
                "faithfulness": faith,
                "relevancy": relev,
            })
            print(f"  Faith: {faith['score']}/5 — {faith['reason']}")
            print(f"  Relev: {relev['score']}/5 — {relev['reason']}")

        results.append(row)

    scored_3 = [r["hit@3"] for r in results if r["hit@3"] is not None]
    scored_5 = [r["hit@5"] for r in results if r["hit@5"] is not None]
    avg_hit_3 = sum(scored_3) / len(scored_3)
    avg_hit_5 = sum(scored_5) / len(scored_5)

    print(f"\n{'='*50}")
    print(f"Results: {len(results)} questions")
    print(f"Avg Hit@3:        {avg_hit_3:.2f} ({sum(scored_3)}/{len(scored_3)})")
    print(f"Avg Hit@5:        {avg_hit_5:.2f} ({sum(scored_5)}/{len(scored_5)})")

    summary = {
        "n": len(results),
        "hit@3": avg_hit_3,
        "hit@5": avg_hit_5,
    }

    if not retrieval_only:
        avg_faith = sum(r["faithfulness"]["score"] for r in results) / len(results)
        avg_relev = sum(r["relevancy"]["score"] for r in results) / len(results)
        print(f"Avg Faithfulness: {avg_faith:.2f}/5")
        print(f"Avg Relevancy:    {avg_relev:.2f}/5")
        summary["faithfulness"] = avg_faith
        summary["relevancy"] = avg_relev

    output_path = os.path.join(os.path.dirname(__file__), "results.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Detailed results saved to {output_path}")

    return summary


if __name__ == "__main__":
    run_eval()