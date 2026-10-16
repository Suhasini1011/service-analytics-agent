import json
import re

NUMBER_PATTERN = r"(?<![A-Za-z\d.,])\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![A-Za-z\d.,])\d+(?:\.\d+)?"
CITED_NUMBER_PATTERN = r"(?<![A-Za-z\d.,])(\d[\d,]*(?:\.\d+)?)[^\[\]]{0,25}?\[([A-Za-z0-9_.]+(?:\[\d+\])?)\]"
CITATION_PATTERN = r"\s*\[[A-Za-z0-9_.]+(?:\[\d+\])?\]"


def find_numbers(text):
    return [float(match.replace(",", "")) for match in re.findall(NUMBER_PATTERN, text)]


def look_up(facts, path):
    path = re.sub(r"\[(\d+)\]", r".\1", path)
    value = facts
    for part in path.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        elif isinstance(value, list) and part.isdigit() and int(part) < len(value):
            value = value[int(part)]
        else:
            return None
    return value


def check_grounding(narrative, facts):
    problems = []

    cited = re.findall(CITED_NUMBER_PATTERN, narrative)
    for number_text, path in cited:
        number = float(number_text.replace(",", ""))
        value = look_up(facts, path)

        if number in find_numbers(path.replace("_", " ")):
            continue

        if value is None:
            problems.append(f"{number_text} cites a fact that does not exist: {path}")
        elif isinstance(value, (int, float)):
            if float(value) != number:
                problems.append(f"{number_text} does not match {path}, which is {value}")
        elif number not in find_numbers(json.dumps(value)):
            problems.append(f"{number_text} is not in {path}")

    allowed = set(find_numbers(json.dumps(facts)))
    uncited_text = re.sub(CITATION_PATTERN, "", re.sub(CITED_NUMBER_PATTERN, "", narrative))
    for number in find_numbers(uncited_text):
        if number not in allowed:
            problems.append(f"{number:g} has no citation and is not in the facts")

    return len(cited), problems


def remove_citations(text):
    return re.sub(CITATION_PATTERN, "", text)


if __name__ == "__main__":
    facts = {"reopen_rate_pct": 7.5, "sla_attainment_pct_by_priority": {"P4": 73.4},
             "top_escalation_driver": {"share_of_escalations_pct": 44.4},
             "access_theme": {"share_of_escalations_pct": 46.8}}

    tests = {
        "Correct": "P4 attainment is 73.4% [sla_attainment_pct_by_priority.P4] and reopens are 7.5% [reopen_rate_pct].",
        "Wrong label": "Access requests cause 46.8% [top_escalation_driver.share_of_escalations_pct] of escalations.",
        "Invented": "This will cut escalations by 25%.",
        "Fake source": "Satisfaction is 4.2 [customer_satisfaction_score].",
        "Real AI style": "Lowest is 73.4% for P4 [sla_attainment_pct_by_priority.P4], with 1 ticket older than 14 days [open_tickets_older_than_14_days].",
    }
    for name, sentence in tests.items():
        cited, problems = check_grounding(sentence, {**facts, "open_tickets_older_than_14_days": 1})
        print(f"{name}: {problems if problems else 'OK'}")

    print("\nClean text:", remove_citations(tests["Correct"]))