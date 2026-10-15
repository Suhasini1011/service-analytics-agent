import pandas as pd

REQUIRED_COLUMNS = ["ticket_id", "created_at", "priority", "status", "request_type", "description"]


def validate_tickets(df):
    issues = []

    for column in REQUIRED_COLUMNS:
        for ticket_id in df[df[column].isna()]["ticket_id"]:
            issues.append({"ticket_id": ticket_id, "issue": f"Missing {column}"})

    for ticket_id in df[df["ticket_id"].duplicated()]["ticket_id"]:
        issues.append({"ticket_id": ticket_id, "issue": "Duplicate ticket ID"})

    created = pd.to_datetime(df["created_at"], errors="coerce")
    resolved = pd.to_datetime(df["resolved_at"], errors="coerce")

    for ticket_id in df[resolved < created]["ticket_id"]:
        issues.append({"ticket_id": ticket_id, "issue": "Resolved before created"})

    for ticket_id in df[(df["status"] == "Resolved") & resolved.isna()]["ticket_id"]:
        issues.append({"ticket_id": ticket_id, "issue": "Resolved but no resolved date"})

    return pd.DataFrame(issues, columns=["ticket_id", "issue"])


if __name__ == "__main__":
    df = pd.read_csv("data/tickets.csv")
    issues = validate_tickets(df)

    print(f"Checked {len(df)} tickets, found {len(issues)} issues\n")
    print(issues["issue"].value_counts())

    issues.to_csv("data/data_quality_issues.csv", index=False)
    print("\nSaved details to data/data_quality_issues.csv")