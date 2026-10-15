import random
from datetime import datetime, timedelta
import pandas as pd

random.seed(42)

NUM_TICKETS = 2000

APPLICATIONS = ["Expense tool", "HR system", "Procurement portal", "Learning platform"]

PRIORITIES = ["P1", "P2", "P3", "P4"]
PRIORITY_WEIGHTS = [5, 15, 50, 30]

FIRST_NAMES = ["Priya", "Rahul", "Ananya", "Arjun", "Sneha", "Vikram", "Meera", "Karan"]
LAST_NAMES = ["Nair", "Mehta", "Iyer", "Sharma", "Rao", "Kulkarni", "Das", "Patil"]

CATALOG_REQUESTS = {
    "Access request": [
        "Need access for my new role",
        "Please grant approver access",
        "Access removed after team move, need it back",
    ],
    "General IT request": [
        "Need a new report added to my dashboard",
        "Please update my cost centre",
    ],
}

PORTAL_ISSUES = {
    "Login issue": [
        "Can't log in after password reset",
        "Stuck in a sign-in loop on mobile",
    ],
    "Error or bug": [
        "Page shows an error when I click submit",
        "Report export is failing",
    ],
    "How-to question": [
        "How do I submit an expense for approval?",
        "Where do I find my training history?",
    ],
}

START_DATE = datetime(2026, 1, 1)
DAYS_OF_DATA = 180
END_DATE = START_DATE + timedelta(days=DAYS_OF_DATA)

TYPICAL_HOURS = {"P1": 3, "P2": 12, "P3": 40, "P4": 80}

SUPPORT_STAFF = ["Neha Joshi", "Amit Verma", "Kavya Reddy", "Rohan Gupta", "Divya Menon"]


def make_ticket(number):
    if random.random() < 0.4:
        channel = "Service catalog"
        prefix = "RITM"
        request_type = random.choice(list(CATALOG_REQUESTS))
        description = random.choice(CATALOG_REQUESTS[request_type])
    else:
        channel = "Employee portal"
        prefix = "INC"
        request_type = random.choice(list(PORTAL_ISSUES))
        description = random.choice(PORTAL_ISSUES[request_type])

    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    priority = random.choices(PRIORITIES, weights=PRIORITY_WEIGHTS)[0]

    created_at = START_DATE + timedelta(minutes=random.randint(0, DAYS_OF_DATA * 24 * 60))

    if request_type == "Access request":
        escalated = random.random() < 0.35
    else:
        escalated = random.random() < 0.10

    hours_to_fix = random.expovariate(1 / TYPICAL_HOURS[priority])
    if escalated:
        hours_to_fix = hours_to_fix * 2
    resolved_at = created_at + timedelta(hours=hours_to_fix)

    if resolved_at > END_DATE:
        status = "In progress"
        resolved_at = None
    else:
        status = "Resolved"

    assignee = random.choice(SUPPORT_STAFF)
    reopened = status == "Resolved" and random.random() < 0.08

    return {
        "ticket_id": f"{prefix}{number:07d}",
        "created_at": created_at.strftime("%Y-%m-%d %H:%M"),
        "resolved_at": resolved_at.strftime("%Y-%m-%d %H:%M") if resolved_at else "",
        "priority": priority,
        "status": status,
        "channel": channel,
        "application": random.choice(APPLICATIONS),
        "request_type": request_type,
        "requester_name": f"{first} {last}",
        "requester_email": f"{first.lower()}.{last.lower()}@example.com",
        "assignee_name": assignee,
        "assignee_email": assignee.lower().replace(" ", ".") + "@example.com",
        "assigned_group": "L2 application support" if escalated else "L1 service desk",
        "escalated": "Yes" if escalated else "No",
        "reopened": "Yes" if reopened else "No",
        "description": description,
    }

tickets = []
for number in range(1, NUM_TICKETS + 1):
    tickets.append(make_ticket(number))

df = pd.DataFrame(tickets)

# --- Plant some data quality problems on purpose ---

duplicates = df.sample(5, random_state=1)
df = pd.concat([df, duplicates], ignore_index=True)

bad_dates = df[df["status"] == "Resolved"].sample(5, random_state=2).index
df.loc[bad_dates, "resolved_at"] = "2025-12-01 09:00"

missing_priority = df.sample(8, random_state=3).index
df.loc[missing_priority, "priority"] = ""

missing_description = df.sample(6, random_state=4).index
df.loc[missing_description, "description"] = ""
df.to_csv("data/tickets.csv", index=False)

print(df.shape)
print(df.head())
print(df["priority"].value_counts())