import json
import pandas as pd
from clean import clean_tickets
from kpis import sla_by_priority, time_to_resolve, backlog, ticket_aging, reopen_rate, SLA_TARGET_HOURS
from categorise import add_themes
from drivers import escalation_drivers
from llm import ask_llm
from grounding import check_grounding, remove_citations

SLA_ATTAINMENT_GOAL_PCT = 95

NARRATIVE_PROMPT = """You are a senior IT service analyst writing a short service review for managers.
You will receive a JSON facts packet. It is your only source of information.

Strict rules:
- Use only numbers that appear in the facts packet, written exactly as they appear there.
- Cite every number by putting the path of its fact in square brackets straight after it,
  for example: 73.4% [sla_attainment_pct_by_priority.P4] or 27 [open_backlog_total] tickets.
- Do not calculate anything new: no ratios, differences, totals or percentages of your own.
- Do not estimate or promise the impact of any recommendation.
- Refer to priorities as P1, P2, P3 and P4.
- Use bullet points starting with "- ". Do not number anything, including findings: refer to them by topic.
- Judge SLA performance only by sla_attainment_pct. Median and mean hours describe typical speed, not SLA compliance.
- One finding must cover the access_theme facts, including how many access tickets were filed under other request types.

Write exactly these three sections:
## Summary
Three or four sentences on overall service health.
## Key findings
Three to five bullets, most important first.
## Recommendations
Three bullets. Each must say which finding it addresses.
End with one sentence noting the data quality adjustments."""


def build_facts(df, notes):
    sla = sla_by_priority(df)
    times = time_to_resolve(df)
    aging = ticket_aging(df)
    by_type = escalation_drivers(df, "request_type")
    by_theme = escalation_drivers(df, "theme")

    top_type = by_type.index[0]
    others = by_type.drop(top_type)
    baseline_rate = others["escalations"].sum() / others["tickets"].sum() * 100

    misfiled = df[(df["theme"] == "Access and permissions") & (df["request_type"] != "Access request")]

    facts = {
        "data_quality_notes": notes,
        "total_tickets": len(df),
        "sla_attainment_pct_by_priority": {p: float(v) for p, v in sla["sla_attainment_pct"].items()},
        "sla_attainment_goal_pct": SLA_ATTAINMENT_GOAL_PCT,
        "sla_target_hours_by_priority": SLA_TARGET_HOURS,
        "median_hours_to_resolve_by_priority": {p: float(v) for p, v in times["median"].items()},
        "mean_hours_to_resolve_by_priority": {p: float(v) for p, v in times["mean"].items()},
        "open_backlog_total": int(backlog(df).sum()),
        "open_tickets_older_than_14_days": int(aging["15+ days"]),
        "reopen_rate_pct": float(reopen_rate(df)),
        "total_escalations": int(by_type["escalations"].sum()),
        "top_escalation_driver": {
            "request_type": top_type,
            "share_of_tickets_pct": round(float(by_type.loc[top_type, "tickets"] / len(df) * 100), 1),
            "escalation_rate_pct": float(by_type.loc[top_type, "escalation_rate_pct"]),
            "share_of_escalations_pct": float(by_type.loc[top_type, "share_of_escalations_pct"]),
            "escalation_rate_of_all_other_types_pct": round(float(baseline_rate), 1),
        },
        "access_theme": {
            "tickets_filed_as_access_request": int(by_type.loc["Access request", "tickets"]),
            "tickets_ai_themed_as_access": int(by_theme.loc["Access and permissions", "tickets"]),
            "access_tickets_filed_under_other_request_types": len(misfiled),
            "share_of_escalations_pct": float(by_theme.loc["Access and permissions", "share_of_escalations_pct"]),
        },
    }
    return facts


def write_narrative(facts, problems=None):
    message = json.dumps(facts, indent=2)
    if problems:
        message += "\n\nYour previous draft broke the rules. Rewrite it and fix these problems:\n"
        message += "\n".join(f"- {problem}" for problem in problems)
    return ask_llm(NARRATIVE_PROMPT, message)


if __name__ == "__main__":
    raw = pd.read_csv("data/tickets.csv")
    df, notes = clean_tickets(raw)
    df = add_themes(df)

    facts = build_facts(df, notes)

    with open("data/facts.json", "w") as f:
        json.dump(facts, f, indent=2)

    problems = None
    for attempt in range(1, 4):
        narrative = write_narrative(facts, problems)
        cited, problems = check_grounding(narrative, facts)
        print(f"Attempt {attempt}: {cited} cited numbers, {len(problems)} problems")
        for problem in problems:
            print("  -", problem)
        if not problems:
            break

    with open("data/narrative_cited.md", "w") as f:
        f.write(narrative)
    with open("data/narrative.md", "w") as f:
        f.write(remove_citations(narrative))
    with open("data/grounding.json", "w") as f:
        json.dump({"cited_numbers": cited, "problems": problems}, f, indent=2)

    print()
    print(narrative)