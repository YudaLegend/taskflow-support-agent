"""" Minimal one-node Langgraph Agent"""


from langgraph.graph import StateGraph, MessagesState, START,END

from agent.llm import chat


SYSTEM_PROMPT = (
    "You are the customer support assistant for TaskFlow, "
    "a web-based project management tool. "
    "Be concise and helpful."
)
def support_agent(state: MessagesState) -> dict:
    """The single LLM node — takes conversation state, returns a reply."""

    role_map = {"human": "user", "ai": "assistant"}

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in state["messages"]:
        messages.append({
            "role": role_map.get(m.type, m.type),
            "content": m.content,
        })

    reply = chat(messages)

    return {"messages": [reply]}

def build_graph():
    """Build and compile the one-node graph."""

    # TODO 4: Create a StateGraph with MessagesState
    # graph = StateGraph(MessagesState)
    graph = StateGraph(MessagesState)

    # TODO 5: Add the support_agent node
    # graph.add_node("support", support_agent)
    graph.add_node("support", support_agent)

    # TODO 6: Wire the edges:
    #   START → "support" → END
    graph.add_edge(START, "support")
    graph.add_edge("support", END)

    # TODO 7: Compile and return
    return graph.compile()

if __name__ == "__main__":
    from langchain_core.messages import HumanMessage

    agent = build_graph()
    result = agent.invoke({"messages": [HumanMessage(content="What is TaskFlow?")]})

    # Print the last message (the agent's reply)
    print(result["messages"][-1].content)