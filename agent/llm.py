import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()


client = Groq(api_key=os.getenv("GROQ_API_KEY"))
DEFAULT_MODEL = "llama-3.3-70b-versatile"
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 1024


def chat(messages: list[dict], model: str = DEFAULT_MODEL, temperature: float = DEFAULT_TEMPERATURE,max_tokens: int = DEFAULT_MAX_TOKENS, ) -> str:
    """Send a list of messages to the LLM and return the text reply.

    Each message is a dict with 'role' (system/user/assistant) and 'content'.
    """
    # TODO 2: call the Groq client's chat completions endpoint.
    response = client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )


    # TODO 3: extract and return the assistant's reply text.
    # The response object structure is:
    #     response.choices[0].message.content
    return response.choices[0].message.content


if __name__ == "__main__":
    # Quick test when you run `python agent/llm.py` directly
    reply = chat([
        {"role": "system", "content": "You are a concise assistant."},
        {"role": "user", "content": "In one sentence, what is a RAG system?"},
    ])
    print(reply)
