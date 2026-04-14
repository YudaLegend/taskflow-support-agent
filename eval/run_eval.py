"""Evalutate the RAG pipeline against a golden dataset"""

import json
import os
import sys

from agent.llm import chat
from rag.answer import answer, format_context
from rag.retrieve import retrieve

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


def run_eval():
    golden = load_golden(GOLDEN_PATH)
    results = []

    for i, case in enumerate(golden, 1):
        question = case["question"]
        expected = case["expected"]
        print(f"\n[{i}/{len(golden)}] {question}")

        # TODO 2: Get the actual answer from your RAG pipeline
        # Hint: use the answer() function from rag.answer
        actual_answer = answer(question)

        # TODO 3: Get the retrieved context too (for faithfulness judging)
        # Hint: call retrieve() separately to get the raw chunks,
        #       then format them into a string
        chunks = retrieve(question, k=5)
        context_str = format_context(chunks)

        # TODO 4: Judge faithfulness and relevancy
        faith = judge_faithfulness(question, actual_answer, context_str)
        relev = judge_relevancy(question, actual_answer)

        # TODO 5: Store the result
        results.append({
            "question": question,
            "expected": expected,
            "actual": actual_answer,
            "faithfulness": faith,
            "relevancy": relev,
        })

        # TODO 6: Print a summary for this question
        print(f"  Faith: {faith['score']}/5 — {faith['reason']}")
        print(f"  Relev: {relev['score']}/5 — {relev['reason']}")
        
    # Print overall scores
    avg_faith = sum(r["faithfulness"]["score"] for r in results) / len(results)
    avg_relev = sum(r["relevancy"]["score"] for r in results) / len(results)
    print(f"\n{'='*50}")
    print(f"Results: {len(results)} questions")
    print(f"Avg Faithfulness: {avg_faith:.2f}/5")
    print(f"Avg Relevancy:    {avg_relev:.2f}/5")

    # Save detailed results
    output_path = os.path.join(os.path.dirname(__file__), "results.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Detailed results saved to {output_path}")


if __name__ == "__main__":
    run_eval()