"""Tool functions the support agent can call.

Each tool is a plain Python function with:
  - A Pydantic model defining its input schema (types, constraints, descriptions)
  - A clear docstring that tells the LLM *when* to use it and *what* it returns
  - A return type of dict (JSON-serialisable) so it can travel back to the LLM

The LLM never executes these directly — your orchestrator (LangGraph) will.
"""

import os
from datetime import UTC, datetime

from pydantic import BaseModel, Field
from pymongo import MongoClient

from rag.retrieve import retrieve

# ---------------------------------------------------------------------------
# MongoDB connection  (override via MONGO_URI env var; default = local dev)
# In Docker we set MONGO_URI=mongodb://host.docker.internal:27017 to reach
# the Mongo Service on the host machine.
# ---------------------------------------------------------------------------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "taskflow")

_client: MongoClient | None = None


def _get_db():
    """Lazy-connect so importing this module doesn't require a live server."""
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client[DB_NAME]


# ===========================  TOOL 1: search_docs  ===========================

class SearchDocsInput(BaseModel):
    """Schema the LLM fills in when it wants to search the knowledge base."""
    query: str = Field(description="Natural-language search query about TaskFlow features, pricing, or usage")
    k: int = Field(default=3, ge=1, le=10, description="Number of doc chunks to return")


def search_docs(query: str, k: int = 3) -> dict:
    """Search the TaskFlow knowledge base for product information.

    Use this when the user asks about TaskFlow features, pricing, plans,
    integrations, or how-to questions. Returns the top-k most relevant
    document chunks with their source files.
    """
    # TODO 1: Call retrieve(query, k) and return the results.
    #
    # retrieve() returns: [{"text": "...", "source": "...", "score": 0.42}, ...]
    #
    # Return a dict like:
    #   {"results": <the list from retrieve()>}
    #
    # This one is intentionally simple — the point is to see how an existing
    # function gets wrapped as a tool.
    return {"results": retrieve(query, k)}



# ============================  TOOL 2: get_user  ============================

class GetUserInput(BaseModel):
    """Schema the LLM fills in when it needs to look up a user."""
    email: str = Field(description="The user's email address to look up")


def get_user(email: str) -> dict:
    """Look up a TaskFlow user by their email address.

    Use this when you need to identify who the customer is before performing
    account-specific actions (listing tickets, creating tickets, etc.).
    Returns the user document or an error message if not found.
    """
    # TODO 2: Use _get_db() to access the 'users' collection.
    #         Find one document where the "email" field matches.
    #
    # If found, return:  {"user": <the document>}
    # If not found:      {"error": f"No user found with email {email}"}
    #
    # Hint: MongoDB's find_one() returns None if no match.
    # Hint: The _id field is already a string like "user_0001" (not ObjectId),
    #       so no special serialisation needed.

    db = _get_db()
    user_doc = db.users.find_one({"email": email})
    if user_doc:
        return {"user": user_doc}
    else:
        return {"error": f"No user found with email {email}"}



# ========================  TOOL 3: list_user_tickets  ========================

class ListUserTicketsInput(BaseModel):
    """Schema the LLM fills in when it needs to see a user's support tickets."""
    user_id: str = Field(description="The user's ID (e.g. 'user_0001')")
    status: str | None = Field(default=None, description="Optional filter: 'open', 'in_progress', 'waiting_customer', 'resolved', or 'closed'")


def list_user_tickets(user_id: str, status: str | None = None) -> dict:
    """List support tickets belonging to a user.

    Use this after identifying the user (via get_user) to show them their
    ticket history. Optionally filter by status. Returns up to 10 most
    recent tickets sorted by creation date.
    """
    # TODO 3: Build a MongoDB query dict.
    #         - Always filter by {"user_id": user_id}
    #         - If status is not None, also add {"status": status}
    #         Then query the 'tickets' collection:
    #           db.tickets.find(query).sort("created_at", -1).limit(10)
    #
    # find() returns a cursor — convert to a list.
    #
    # Return: {"tickets": <list of ticket dicts>, "count": <len of list>}
    #
    # Hint: pymongo sort order: -1 = descending (newest first)
    db = _get_db()
    query = {"user_id": user_id}
    if status is not None:
        query["status"] = status
    tickets_cursor = db.tickets.find(query).sort("created_at", -1).limit(10)
    tickets = list(tickets_cursor)
    return {"tickets": tickets, "count": len(tickets)}


# =========================  TOOL 4: create_ticket  =========================

class CreateTicketInput(BaseModel):
    """Schema the LLM fills in when it needs to create a new support ticket."""
    user_id: str = Field(description="The user's ID (e.g. 'user_0001')")
    subject: str = Field(min_length=5, max_length=200, description="Brief summary of the issue")
    body: str = Field(min_length=10, description="Detailed description of the issue")
    priority: str = Field(default="medium", description="Ticket priority: 'low', 'medium', 'high', or 'urgent'")


def create_ticket(user_id: str, subject: str, body: str, priority: str = "medium") -> dict:
    """Create a new support ticket for a user.

    Use this when the user explicitly asks to open/create/file a support
    ticket. Requires user_id (get it from get_user first), a subject line,
    a description body, and an optional priority level.
    """
    # TODO 4: Validate that priority is one of the allowed values.
    #         Then build a ticket document and insert it into the 'tickets'
    #         collection.
    #
    # Steps:
    #   1. Check priority is in {"low", "medium", "high", "urgent"}.
    #      If not, return {"error": f"Invalid priority: {priority}"}
    #
    #   2. Generate a ticket_id. One approach:
    #      count = db.tickets.count_documents({}) → ticket_id = f"TF-{1000 + count}"
    #
    #   3. Build the document dict with these fields:
    #      _id, user_id, subject, description (=body), status ("open"),
    #      priority, category ("other"), created_at (now as ISO string),
    #      updated_at (same), assigned_to (None)
    #
    #      Use: datetime.now(timezone.utc).isoformat()
    #
    #   4. Insert it:  db.tickets.insert_one(ticket)
    #
    #   5. Return: {"ticket_id": ticket_id, "message": "Ticket created successfully"}

    if priority not in {"low", "medium", "high", "urgent"}:
        return {"error": f"Invalid priority: {priority}"}

    db = _get_db()
    count = db.tickets.count_documents({})
    ticket_id = f"TF-{1000 + count}"

    ticket = {
        "_id": ticket_id,
        "user_id": user_id,
        "subject": subject,
        "description": body,
        "status": "open",
        "priority": priority,
        "category": "other",
        "created_at": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
        "assigned_to": None
    }
    db.tickets.insert_one(ticket)

    return {"ticket_id": ticket_id, "message": "Ticket created successfully"}


# ========================  TOOL 5: escalate_to_human  ========================

class EscalateToHumanInput(BaseModel):
    """Schema the LLM fills in when it decides the issue needs a human agent."""
    reason: str = Field(description="Why this conversation needs human attention")


def escalate_to_human(reason: str) -> dict:
    """Escalate the current conversation to a human support agent.

    Use this when:
    - The user explicitly asks to speak with a human
    - The issue involves billing disputes, legal matters, or account deletion
    - You've been unable to resolve the issue after multiple attempts
    """
    # TODO 5: This is a stub — in a real system it would create an escalation
    #         record, notify the on-call team, etc.
    #
    # Just return:
    #   {
    #       "escalated": True,
    #       "reason": reason,
    #       "message": "I've escalated this to our support team. A human agent will reach out to you shortly."
    #   }
    return {
        "escalated": True,
        "reason": reason,
        "message": "I've escalated this to our support team. A human agent will reach out to you shortly."
    }


# ---------------------------------------------------------------------------
# Tool registry — maps tool name → (function, input schema)
# LangGraph will use this to wire tools into the agent graph.
# ---------------------------------------------------------------------------
TOOLS = {
    "search_docs":       (search_docs,       SearchDocsInput),
    "get_user":          (get_user,           GetUserInput),
    "list_user_tickets": (list_user_tickets,  ListUserTicketsInput),
    "create_ticket":     (create_ticket,      CreateTicketInput),
    "escalate_to_human": (escalate_to_human,  EscalateToHumanInput),
}


# ---------------------------------------------------------------------------
# LangChain @tool wrappers — used by LangGraph's ToolNode
#
# These wrap your plain functions above so LangChain can:
#   1. Advertise them to the LLM (name + description + schema)
#   2. Execute them when the LLM emits a tool call
#
# The @tool decorator reads the function's docstring as the description
# and uses the args_schema for the input schema.
# ---------------------------------------------------------------------------
from langchain_core.tools import tool  # noqa: E402  (decorator wraps the functions defined above)


@tool(args_schema=SearchDocsInput)
def search_docs_tool(query: str, k: int = 3) -> dict:
    """Search the TaskFlow knowledge base for product information.

    Use this when the user asks about TaskFlow features, pricing, plans,
    integrations, or how-to questions. Returns the top-k most relevant
    document chunks with their source files.
    """
    return search_docs(query, k)


@tool(args_schema=GetUserInput)
def get_user_tool(email: str) -> dict:
    """Look up a TaskFlow user by their email address.

    Use this when you need to identify who the customer is before performing
    account-specific actions (listing tickets, creating tickets, etc.).
    Returns the user document or an error message if not found.
    """
    return get_user(email)


@tool(args_schema=ListUserTicketsInput)
def list_user_tickets_tool(user_id: str, status: str | None = None) -> dict:
    """List support tickets belonging to a user.

    Use this after identifying the user (via get_user) to show them their
    ticket history. Optionally filter by status. Returns up to 10 most
    recent tickets sorted by creation date.
    """
    return list_user_tickets(user_id, status)


@tool(args_schema=CreateTicketInput)
def create_ticket_tool(user_id: str, subject: str, body: str, priority: str = "medium") -> dict:
    """Create a new support ticket for a user.

    Use this when the user explicitly asks to open/create/file a support
    ticket. Requires user_id (get it from get_user first), a subject line,
    a description body, and an optional priority level.
    """
    return create_ticket(user_id, subject, body, priority)


@tool(args_schema=EscalateToHumanInput)
def escalate_to_human_tool(reason: str) -> dict:
    """Escalate the current conversation to a human support agent.

    Use this when:
    - The user explicitly asks to speak with a human
    - The issue involves billing disputes, legal matters, or account deletion
    - You've been unable to resolve the issue after multiple attempts
    """
    return escalate_to_human(reason)


# List of LangChain tools — this is what graph.py will import
LANGCHAIN_TOOLS = [
    search_docs_tool,
    get_user_tool,
    list_user_tickets_tool,
    create_ticket_tool,
    escalate_to_human_tool,
]


# ---------------------------------------------------------------------------
# Quick smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== search_docs ===")
    print(search_docs("How much does the Pro plan cost?"))

    print("\n=== get_user ===")
    # Grab a real email from the DB for testing
    db = _get_db()
    sample_user = db.users.find_one()
    if sample_user:
        print(f"Testing with email: {sample_user['email']}")
        result = get_user(sample_user["email"])
        print(result)

        print("\n=== list_user_tickets ===")
        print(list_user_tickets(sample_user["_id"]))

        print("\n=== create_ticket ===")
        print(create_ticket(sample_user["_id"], "Test ticket from smoke test", "This is a test ticket created during Day 13 development.", "low"))

    print("\n=== escalate_to_human ===")
    print(escalate_to_human("User requested to speak with a human agent"))
