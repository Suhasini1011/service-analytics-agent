import pandas as pd


def clean_tickets(df):
    notes = []

    rows_before = len(df)
    df = df.drop_duplicates(subset="ticket_id", keep="first").copy()
    notes.append(f"{rows_before - len(df)} duplicate tickets removed")

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["resolved_at"] = pd.to_datetime(df["resolved_at"], errors="coerce")

    bad_dates = df["resolved_at"] < df["created_at"]
    df.loc[bad_dates, "resolved_at"] = pd.NaT
    notes.append(f"{bad_dates.sum()} tickets with impossible dates excluded from resolution-time KPIs")

    notes.append(f"{df['priority'].isna().sum()} tickets with no priority excluded from SLA by priority")
    notes.append(f"{df['description'].isna().sum()} tickets with no description will be labelled Unclassified")

    return df, notes


if __name__ == "__main__":
    raw = pd.read_csv("data/tickets.csv")
    clean, notes = clean_tickets(raw)

    print(f"Raw tickets: {len(raw)}   Clean tickets: {len(clean)}\n")
    for note in notes:
        print("-", note)