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


if __name__ == "__main__":
    raw = pd.read_csv("data/tickets.csv")
    df, notes = clean_tickets(raw)

    print("SLA attainment by priority:")
    print(sla_by_priority(df))