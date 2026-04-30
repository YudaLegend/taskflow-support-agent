"""RAG asnwerer - retrireve context, build prompt, call LLM"""

from agent.llm import chat
from rag.retrieve import retrieve

RAG_SYSTEM_PROMPT = """You are the customer support assistant for TaskFlow, \
a web-based project management tool.

Answer the user's question using ONLY the context provided below. \
If the context does not contain enough information to answer, say \
"I don't have enough information to answer that. Would you like me \
to connect you with a human agent?"

Always cite which of sources documents your answer came from using \
[Source: filename] at the end of your answer.

Keep your answers concise — 2-4 sentences for simple questions.

## Context
{context}
"""


def format_context(results: list[dict]) -> str:
    """Format retrieved chunks into a context string for the prompt.

    Takes the output of retrieve() and turns it into:
        [Source: pricing-plans.md]
        Pro is $12/user/month...

        [Source: faq-general.md]
        We offer 20% off...
    """
    # TODO 1: Loop through results, build a string with source + text
    # for each chunk. Separate chunks with a blank line.
    pieces = []
    for r in results:
        pieces.append(f"[Source: {r['source']}]\n{r['text']}")
    return "\n\n".join(pieces)


def answer(question: str, k: int = 5) -> str:
    """Full RAG pipeline: retrieve → format → LLM → answer."""
    # TODO 2:
    # 1. Call retrieve(question, k) to get chunks
    # 2. Call format_context() to build the context string
    # 3. Build the system prompt by replacing {context} with the context
    #    Hint: RAG_SYSTEM_PROMPT.format(context=context_str)
    # 4. Call chat() with the system message + user question
    # 5. Return the LLM's reply

    chunks = retrieve(question, k)
    context_str = format_context(chunks)
    system_message = RAG_SYSTEM_PROMPT.format(context=context_str)
    reply = chat(
        [
            {"role": "system", "content": system_message},
            {"role": "user", "content": question},
        ]
    )
    return reply


if __name__ == "__main__":
    import sys

    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "How much does Pro cost?"
    print(f"Question: {question}\n")
    reply = answer(question)
    print(f"Answer: {reply}")
