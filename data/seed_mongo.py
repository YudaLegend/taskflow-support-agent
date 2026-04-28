"""Seeds the taskflow MongoDB database with fake data for development."""

import os
import random
from datetime import datetime, timedelta, timezone

from faker import Faker
from pymongo import MongoClient

fake = Faker()
Faker.seed(42)
random.seed(42)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "taskflow")

PLANS = ["free", "pro", "business", "enterprise"]
BILLING_CYCLES = ["monthly", "annual"]
SUB_STATUSES = ["active", "past_due", "canceled", "trialing"]

TICKET_STATUSES = ["open", "in_progress", "waiting_customer", "resolved", "closed"]
TICKET_PRIORITIES = ["low", "medium", "high", "urgent"]
TICKET_CATEGORIES = ["billing", "integrations", "bug", "account", "other"]

USER_STATUSES = ["active", "suspended", "deleted"]
EVENT_TYPES = ["task_created", "task_completed", "login", "api_call", "project_created"]

SUPPORT_AGENTS = ["agent_sarah", "agent_marcus", "agent_lina", "agent_david", None]

TICKET_SUBJECTS_BY_CATEGORY = {
    "billing": [
        "Invoice shows wrong amount",
        "Can't update my payment method",
        "Charged twice this month",
        "Request a refund for annual plan",
        "How do I download old invoices?",
    ],
    "integrations": [
        "Slack integration stopped working",
        "Google Drive files not attaching",
        "GitHub PR sync is delayed",
        "Zapier webhook failing with 500",
        "Can't connect Slack to private channel",
    ],
    "bug": [
        "Task description not saving",
        "Kanban drag and drop broken on Firefox",
        "Mobile app crashes on startup",
        "Notifications arriving twice",
        "Timeline view not loading",
    ],
    "account": [
        "Can't log in after 2FA reset",
        "Need to change my email",
        "How do I delete my account?",
        "Lost access to authenticator app",
        "SSO login keeps looping",
    ],
    "other": [
        "How do I export my data?",
        "Is there a student discount?",
        "Feature request: time tracking",
        "Where is your status page?",
        "Question about your privacy policy",
    ],
}


def make_subscriptions(n: int) -> list[dict]:
    subscriptions = []
    for i in range(1, n + 1):
        plan = random.choice(PLANS)
        seats = 2 if plan == "free" else random.randint(3, 50)
        cycle = random.choice(BILLING_CYCLES)
        start = fake.date_between(start_date="-2y", end_date="-1m")
        period_length = 365 if cycle == "annual" else 30
        end = start + timedelta(days=period_length)
        subscriptions.append(
            {
                "_id": f"ws_{i:04d}",
                "plan": plan,
                "billing_cycle": cycle,
                "seats": seats,
                "status": random.choices(
                    SUB_STATUSES, weights=[80, 8, 5, 7], k=1
                )[0],
                "current_period_start": start.isoformat(),
                "current_period_end": end.isoformat(),
                "payment_method": random.choice(
                    ["card_visa_4242", "card_mc_5555", "paypal", "bank_transfer"]
                ),
            }
        )
    return subscriptions


def make_users(n: int, workspace_ids: list[str]) -> list[dict]:
    users = []
    for i in range(1, n + 1):
        signup = fake.date_between(start_date="-2y", end_date="today")
        users.append(
            {
                "_id": f"user_{i:04d}",
                "email": fake.unique.email(),
                "full_name": fake.name(),
                "company": fake.company(),
                "signup_date": signup.isoformat(),
                "status": random.choices(
                    USER_STATUSES, weights=[92, 5, 3], k=1
                )[0],
                "workspace_id": random.choice(workspace_ids),
            }
        )
    return users


def _random_datetime_within_days(days_back: int) -> datetime:
    now = datetime.now(timezone.utc)
    delta = timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )
    return now - delta


def make_tickets(n: int, users: list[dict]) -> list[dict]:
    tickets = []
    for i in range(n):
        user = random.choice(users)
        category = random.choice(TICKET_CATEGORIES)
        subject = random.choice(TICKET_SUBJECTS_BY_CATEGORY[category])
        created_at = _random_datetime_within_days(90)
        updated_at = created_at + timedelta(
            hours=random.randint(1, 72),
            minutes=random.randint(0, 59),
        )
        status = random.choices(
            TICKET_STATUSES,
            weights=[25, 15, 15, 25, 20],
            k=1,
        )[0]
        tickets.append(
            {
                "_id": f"TF-{1000 + i}",
                "user_id": user["_id"],
                "workspace_id": user["workspace_id"],
                "subject": subject,
                "description": fake.paragraph(nb_sentences=3),
                "status": status,
                "priority": random.choices(
                    TICKET_PRIORITIES, weights=[30, 40, 20, 10], k=1
                )[0],
                "category": category,
                "created_at": created_at.isoformat(),
                "updated_at": updated_at.isoformat(),
                "assigned_to": random.choice(SUPPORT_AGENTS),
            }
        )
    return tickets


def make_usage_events(n: int, users: list[dict]) -> list[dict]:
    events = []
    for i in range(n):
        user = random.choice(users)
        event_type = random.choice(EVENT_TYPES)
        timestamp = _random_datetime_within_days(30)

        if event_type in ("task_created", "task_completed"):
            metadata = {"project_id": f"proj_{random.randint(1, 100):04d}"}
        elif event_type == "api_call":
            metadata = {
                "endpoint": random.choice(
                    ["/tasks", "/users", "/projects", "/tasks/bulk"]
                ),
                "status_code": random.choices([200, 400, 429, 500], weights=[85, 8, 5, 2], k=1)[0],
            }
        elif event_type == "login":
            metadata = {"ip": fake.ipv4(), "device": random.choice(["web", "ios", "android"])}
        else:
            metadata = {}

        events.append(
            {
                "_id": f"evt_{i:06d}",
                "workspace_id": user["workspace_id"],
                "user_id": user["_id"],
                "event_type": event_type,
                "timestamp": timestamp.isoformat(),
                "metadata": metadata,
            }
        )
    return events


def main() -> None:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    for coll in ["users", "subscriptions", "tickets", "usage_events"]:
        db[coll].drop()

    subscriptions = make_subscriptions(20)
    db.subscriptions.insert_many(subscriptions)

    workspace_ids = [s["_id"] for s in subscriptions]
    users = make_users(50, workspace_ids)
    db.users.insert_many(users)

    tickets = make_tickets(200, users)
    db.tickets.insert_many(tickets)

    events = make_usage_events(500, users)
    db.usage_events.insert_many(events)

    db.users.create_index("email", unique=True)
    db.users.create_index("workspace_id")
    db.tickets.create_index("user_id")
    db.tickets.create_index("workspace_id")
    db.tickets.create_index("status")
    db.usage_events.create_index("user_id")
    db.usage_events.create_index("timestamp")

    print(
        f"Seeded: "
        f"{db.subscriptions.count_documents({})} subscriptions, "
        f"{db.users.count_documents({})} users, "
        f"{db.tickets.count_documents({})} tickets, "
        f"{db.usage_events.count_documents({})} events."
    )


if __name__ == "__main__":
    main()
