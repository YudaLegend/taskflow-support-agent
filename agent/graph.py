"""ReAct-style agent with tool calling via LangGraph.

Architecture:
    START → [agent] → should_continue? → YES → [tools] → [agent] → ...
                                        → NO  → END

The agent node calls the LLM (with tools bound).
The tools node executes whatever tool the LLM asked for.
The router (should_continue) checks: did the LLM emit a tool call or plain text?
"""

import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage

from agent.tools import LANGCHAIN_TOOLS

load_dotenv()

# ---------------------------------------------------------------------------
# System prompt — defines the agent's persona and rules
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are the customer support assistant for TaskFlow, a web-based project management tool.

Rules:
- Be concise, friendly, and professional.
- For product questions (features, pricing, how-to), ALWAYS use search_docs first.
- For account-specific requests, ALWAYS use get_user to identify the customer first.
- Never guess user data — always look it up.
- If you cannot resolve an issue, use escalate_to_human.
- When citing information, mention which doc it came from.
- Do NOT invent features that TaskFlow doesn't have."""

# ---------------------------------------------------------------------------
# LLM setup — ChatGroq with tools bound
# ---------------------------------------------------------------------------

# TODO 1: Create a ChatGroq instance.
#
#   llm = ChatGroq(
#       model="llama-3.3-70b-versatile",
#       temperature=0,
#       api_key=os.getenv("GROQ_API_KEY"),
#   )
#
# Then bind your tools to it so every call includes the tool definitions:
#
#   llm_with_tools = llm.bind_tools(...)
#
# bind_tools() takes a list of tools — use LANGCHAIN_TOOLS (imported above).
#
# Why bind_tools? It converts your Pydantic schemas into the JSON format
# the Groq API expects, and attaches them to every request automatically.

llm = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
    )

llm_with_tools = llm.bind_tools(LANGCHAIN_TOOLS, parallel_tool_calls=False)


# ---------------------------------------------------------------------------
# Node 1: agent — calls the LLM
# ---------------------------------------------------------------------------

def agent(state: MessagesState) -> dict:
    """Call the LLM with the conversation history + tool definitions.

    The system prompt is prepended if this is the first call.
    Returns the LLM's response (which may be text OR a tool call).
    """
    # TODO 2: Build the messages list.
    #
    #   messages = state["messages"]
    #
    #   Check if the first message is already a system message.
    #   If not, prepend one:
    #
    #   from langchain_core.messages import SystemMessage
    #   if not messages or messages[0].type != "system":
    #       messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    #
    #   Then call the LLM:
    #       response = llm_with_tools.invoke(messages)
    #
    #   Return: {"messages": [response]}
    #
    # Note: Unlike your old chat() wrapper which returned a string,
    # llm_with_tools.invoke() returns a rich message object that may
    # contain tool_calls. LangGraph needs this object, not just text.

    messages = state["messages"]
    if not messages or messages[0].type != "system":
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    response = llm_with_tools.invoke(messages)

    return {"messages": [response]}


# ---------------------------------------------------------------------------
# Node 2: tools — executes tool calls
# ---------------------------------------------------------------------------

# TODO 3: Create a ToolNode.
#
#   tool_node = ToolNode(...)
#
# ToolNode takes a list of tools (same LANGCHAIN_TOOLS list).
# It automatically:
#   1. Reads the tool_calls from the LLM's last message
#   2. Executes the matching function
#   3. Returns a ToolMessage with the result
#
# This is pure scaffolding — one line.

tool_node = ToolNode(LANGCHAIN_TOOLS) # ← replace this


# ---------------------------------------------------------------------------
# Router: should the loop continue or exit?
# ---------------------------------------------------------------------------

def should_continue(state: MessagesState) -> str:
    """Decide whether to route to tools or end the conversation.

    Checks the last message in state:
    - If it has tool_calls → return "tools" (continue the loop)
    - If it's plain text  → return END (we're done)
    """
    # TODO 4: Get the last message from state["messages"].
    #
    #   last_message = state["messages"][-1]
    #
    #   Check if it has tool_calls:
    #       if last_message.tool_calls:
    #           return "tools"
    #       return END
    #
    # That's it — this is the "brain" of the routing decision,
    # but the LLM already made the decision. You're just reading it.
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

def build_graph():
    """Assemble the ReAct agent graph and compile it."""

    graph = StateGraph(MessagesState)

    # TODO 5: Add nodes.
    #   graph.add_node("agent", agent)
    #   graph.add_node("tools", tool_node)

    graph.add_node("agent",agent)
    graph.add_node("tools",tool_node)
    # TODO 6: Add edges.
    #   START → agent (always start with the LLM)
    #   graph.add_edge(START, "agent")
    graph.add_edge(START, "agent")

    #   agent → conditional routing (should_continue decides next step)
    #   graph.add_conditional_edges("agent", should_continue)
    graph.add_conditional_edges("agent", should_continue)
    #   tools → agent (after executing a tool, always go back to the LLM)
    #   graph.add_edge("tools", "agent")
    graph.add_edge("tools", "agent")

    # Compile with checkpointer for conversation memory.
    # MemorySaver stores message history in RAM (per thread_id).
    return graph.compile(checkpointer=MemorySaver())
    

# ---------------------------------------------------------------------------
# CLI for testing
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from langchain_core.messages import HumanMessage

    agent_graph = build_graph()

    # Track message count per thread so we can show only NEW messages each turn.
    # This is the key to PROVING memory works:
    #   - If a turn answers WITHOUT calling tools, it pulled from history (memory)
    #   - If a turn calls a tool, it re-fetched fresh data
    _seen = {}

    def send(message: str, thread_id: str) -> str:
        """Send a message to the agent and report which tools (if any) were used."""
        result = agent_graph.invoke(
            {"messages": [HumanMessage(content=message)]},
            config={"configurable": {"thread_id": thread_id}, "recursion_limit": 10},
        )
        all_msgs = result["messages"]
        start = _seen.get(thread_id, 0)
        new_msgs = all_msgs[start:]
        _seen[thread_id] = len(all_msgs)

        # Count tool calls made during THIS turn only
        tools_used = []
        for m in new_msgs:
            if m.type == "ai" and getattr(m, "tool_calls", None):
                for tc in m.tool_calls:
                    tools_used.append(tc["name"])

        print(f"\nUser: {message}")
        if tools_used:
            print(f"  → tools called this turn: {tools_used}")
        else:
            print(f"  → NO tools called (answered from memory)")
        print(f"Agent: {all_msgs[-1].content[:400]}")
        return all_msgs[-1].content

    # =================================================================
    # Test 1: Multi-turn with memory (same thread_id)
    # =================================================================
    # Strategy: Turn 1 forces a search_docs call. Turn 2 asks a follow-up
    # that uses pronouns ("that", "it") — so the agent can ONLY answer if
    # it remembers what we discussed. If the agent calls search_docs again
    # on turn 2, that proves it didn't really "remember" the context.
    print("=" * 60)
    print("TEST 1: Multi-turn product question (with memory)")
    print("=" * 60)

    THREAD_1 = "test-memory-1"
    send("What is the price of the Pro plan?", THREAD_1)
    send("How much would that cost me per year if I pay annually?", THREAD_1)
    send("What was the exact monthly dollar amount you mentioned earlier?", THREAD_1)

    # =================================================================
    # Test 2: Different thread = no memory
    # =================================================================
    # Same follow-up question as Test 1 turn 2, but on a fresh thread.
    # Without memory, "that" has no referent — the agent should be
    # confused, ask for clarification, or guess wrong.
    print("\n" + "=" * 60)
    print("TEST 2: New thread (no memory) — same follow-up should fail")
    print("=" * 60)

    THREAD_2 = "test-memory-2"
    send("How much would that cost me per year if I pay annually?", THREAD_2)

    # =================================================================
    # Test 3: Account conversation (practical use case)
    # =================================================================
    # Turn 1: identify the user + show their tickets (forces 2 tool calls)
    # Turn 2: ask about a specific ticket WITHOUT re-stating the email.
    # If the agent remembers, it should answer without calling get_user
    # again. The ticket details are already in the message history.
    print("\n" + "=" * 60)
    print("TEST 3: Account conversation with memory")
    print("=" * 60)

    THREAD_3 = "test-memory-3"
    send("Hi, I'm williamjohnson@example.org. Can you list my tickets?", THREAD_3)
    send("What is the status of the Kanban-related ticket you just showed me?", THREAD_3)
