import pandas as pd
from clean import clean_tickets

SLA_TARGET_HOURS = {"P1": 4, "P2": 24, "P3": 72, "P4": 120}


def sla_by_priority(df):
    resolved = df[df["resolved_at"].notna() & df["priority"].notna()].copy()

    resolved["hours_to_resolve"] = (resolved["resolved_at"] - resolved["created_at"]).dt.total_seconds() / 3600
    resolved["target_hours"] = resolved["priority"].map(SLA_TARGET_HOURS)
    resolved["met_sla"] = resolved["hours_to_resolve"] <= resolved["target_hours"]

    summary = resolved.groupby("priority").agg(
        resolved_tickets=("ticket_id", "count"),
        met_sla=("met_sla", "sum"),
    )
    summary["sla_attainment_pct"] = (summary["met_sla"] / summary["resolved_tickets"] * 100).round(1)
    return summary

def time_to_resolve(df):
    resolved = df[df["resolved_at"].notna() & df["priority"].notna()].copy()
    resolved["hours_to_resolve"] = (resolved["resolved_at"] - resolved["created_at"]).dt.total_seconds() / 3600

    summary = resolved.groupby("priority")["hours_to_resolve"].agg(["mean", "median"])
    return summary.round(1)


def backlog(df):
    open_tickets = df[df["status"] != "Resolved"]
    return open_tickets["priority"].value_counts().sort_index()


def ticket_aging(df):
    open_tickets = df[df["status"] != "Resolved"].copy()
    report_date = df["created_at"].max()

    open_tickets["age_days"] = (report_date - open_tickets["created_at"]).dt.days
    open_tickets["age_bucket"] = pd.cut(
        open_tickets["age_days"],
        bins=[-1, 2, 7, 14, 10000],
        labels=["0-2 days", "3-7 days", "8-14 days", "15+ days"],
    )
    return open_tickets["age_bucket"].value_counts().sort_index()


def reopen_rate(df):
    resolved = df[df["status"] == "Resolved"]
    reopened = (resolved["reopened"] == "Yes").sum()
    return round(reopened / len(resolved) * 100, 1)

if __name__ == "__main__":
    raw = pd.read_csv("data/tickets.csv")
    df, notes = clean_tickets(raw)

    print("SLA attainment by priority:")
    print(sla_by_priority(df))

    print("\nTime to resolve in hours, by priority:")
    print(time_to_resolve(df))

    print("\nBacklog (open tickets) by priority:")
    print(backlog(df))

    print("\nAge of open tickets:")
    print(ticket_aging(df))

    print("\nReopen rate:", reopen_rate(df), "%")