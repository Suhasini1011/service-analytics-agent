import json
import markdown
import pandas as pd
import plotly.graph_objects as go
from clean import clean_tickets
from categorise import add_themes
from kpis import sla_by_priority, ticket_aging
from drivers import escalation_drivers

BLUE = "#2a78d6"
ORANGE = "#eb6834"
GREY = "#52514e"


def style_chart(fig):
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#0b0b0b", size=13),
        showlegend=False,
        bargap=0.35,
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#e3e2dd")
    return fig


def chart_html(fig):
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"displayModeBar": False, "responsive": True},
                       default_height="100%", default_width="100%")


def sla_chart(df, goal):
    sla = sla_by_priority(df)
    fig = go.Figure(go.Bar(
        x=sla.index, y=sla["sla_attainment_pct"], marker_color=BLUE,
        text=[f"{v}%" for v in sla["sla_attainment_pct"]], textposition="outside",
        hovertemplate="%{x}: %{y}% met SLA<extra></extra>",
    ))
    fig.add_hline(y=goal, line_dash="dash", line_color=GREY,
                  annotation_text=f"Goal {goal}%", annotation_position="top right")
    fig.update_yaxes(range=[0, 105], ticksuffix="%")
    return chart_html(style_chart(fig))


def escalation_chart(df):
    drivers = escalation_drivers(df, "request_type").sort_values("escalation_rate_pct")
    colours = [ORANGE if name == drivers["escalation_rate_pct"].idxmax() else BLUE for name in drivers.index]
    fig = go.Figure(go.Bar(
        x=drivers["escalation_rate_pct"], y=drivers.index, orientation="h", marker_color=colours,
        text=[f"{v}%" for v in drivers["escalation_rate_pct"]], textposition="outside",
        customdata=drivers[["escalations", "tickets"]],
        hovertemplate="%{y}: %{x}% escalated (%{customdata[0]} of %{customdata[1]})<extra></extra>",
    ))
    fig.update_xaxes(range=[0, drivers["escalation_rate_pct"].max() * 1.25], ticksuffix="%", gridcolor="#e3e2dd")
    fig.update_yaxes(showgrid=False)
    return chart_html(style_chart(fig))


def aging_chart(df):
    aging = ticket_aging(df)
    fig = go.Figure(go.Bar(
        x=aging.index.astype(str), y=aging.values, marker_color=BLUE,
        text=aging.values, textposition="outside",
        hovertemplate="%{x}: %{y} open tickets<extra></extra>",
    ))
    fig.update_yaxes(range=[0, aging.max() * 1.25])
    return chart_html(style_chart(fig))


def tile(value, label):
    return f'<div class="tile"><div class="value">{value}</div><div class="label">{label}</div></div>'


if __name__ == "__main__":
    raw = pd.read_csv("data/tickets.csv")
    df, notes = clean_tickets(raw)
    df = add_themes(df)

    with open("data/facts.json") as f:
        facts = json.load(f)
    with open("data/narrative.md") as f:
        narrative = f.read()
    with open("data/grounding.json") as f:
        grounding = json.load(f)

    tiles = "".join([
        tile(f"{facts['total_tickets']:,}", "Tickets analysed"),
        tile(f"{facts['sla_attainment_pct_by_priority']['P4']}%", "P4 SLA attainment (lowest)"),
        tile(facts["open_backlog_total"], "Open backlog"),
        tile(f"{facts['reopen_rate_pct']}%", "Reopen rate"),
        tile(f"{facts['top_escalation_driver']['share_of_escalations_pct']}%", "Escalations from access requests"),
        tile(facts["access_theme"]["access_tickets_filed_under_other_request_types"], "Access tickets filed under other types"),
    ])

    if grounding["problems"]:
        badge = f'<span class="badge fail">Grounding check: {len(grounding["problems"])} unverified numbers</span>'
    else:
        badge = f'<span class="badge pass">Grounding check passed: {grounding["cited_numbers"]} numbers verified</span>'

    created = pd.to_datetime(df["created_at"])
    subtitle = f"Synthetic data, {created.min():%d %b %Y} to {created.max():%d %b %Y}"

    with open("templates/report.html") as f:
        page = f.read()

    replacements = {
        "{{SUBTITLE}}": subtitle,
        "{{TILES}}": tiles,
        "{{CHART_SLA}}": sla_chart(df, facts["sla_attainment_goal_pct"]),
        "{{CHART_ESCALATION}}": escalation_chart(df),
        "{{CHART_AGING}}": aging_chart(df),
        "{{GROUNDING_BADGE}}": badge,
        "{{NARRATIVE}}": markdown.markdown(narrative),
        "{{QUALITY_NOTES}}": "".join(f"<li>{note}</li>" for note in notes),
    }
    for placeholder, content in replacements.items():
        page = page.replace(placeholder, str(content))

    with open("reports/service_report.html", "w") as f:
        f.write(page)
    print("Saved reports/service_report.html")