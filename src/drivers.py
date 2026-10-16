import pandas as pd


def escalation_drivers(df, column):
    df = df.copy()
    df["is_escalated"] = df["escalated"] == "Yes"

    summary = df.groupby(column).agg(
        tickets=("ticket_id", "count"),
        escalations=("is_escalated", "sum"),
    )
    summary = summary.sort_values("escalations", ascending=False)

    summary["escalation_rate_pct"] = summary["escalations"] / summary["tickets"] * 100
    summary["share_of_escalations_pct"] = summary["escalations"] / summary["escalations"].sum() * 100
    summary["cumulative_share_pct"] = summary["share_of_escalations_pct"].cumsum()

    return summary.round(1)


if __name__ == "__main__":
    df = pd.read_csv("data/tickets_with_themes.csv")
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", None)

    print(f"Total tickets: {len(df)}   Escalated: {(df['escalated'] == 'Yes').sum()}\n")

    print("Escalation drivers by request type:")
    print(escalation_drivers(df, "request_type"))

    print("\nEscalation drivers by theme:")
    print(escalation_drivers(df, "theme"))