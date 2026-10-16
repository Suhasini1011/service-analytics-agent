import json
import re

NUMBER_PATTERN = r"(?<![A-Za-z\d.,])\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![A-Za-z\d.,])\d+(?:\.\d+)?"
PLACEHOLDER_PATTERN = r"\{\{\s*([A-Za-z0-9_.]+)\s*\}\}"


def find_numbers(text):
    return [float(match.replace(",", "")) for match in re.findall(NUMBER_PATTERN, text)]


def look_up(facts, path):
    value = facts
    for part in path.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        elif isinstance(value, list) and part.isdigit() and int(part) < len(value):
            value = value[int(part)]
        else:
            return None
    return value


def all_fact_names(facts, prefix=""):
    names = []
    for key, value in facts.items():
        names.append(prefix + key)
        if isinstance(value, dict):
            names.extend(all_fact_names(value, prefix + key + "."))
    return names


def check_grounding(template, facts):
    problems = []

    paths = re.findall(PLACEHOLDER_PATTERN, template)
    for path in paths:
        value = look_up(facts, path)
        if value is None:
            problems.append(f"{{{{{path}}}}} is not a fact in the facts packet")
        elif isinstance(value, (dict, list)):
            problems.append(f"{{{{{path}}}}} is a group of facts, not a single fact")

    numbers_in_names = set(find_numbers(" ".join(all_fact_names(facts)).replace("_", " ")))
    typed_text = re.sub(PLACEHOLDER_PATTERN, "", template)
    for number in find_numbers(typed_text):
        if number not in numbers_in_names:
            problems.append(f"typed the number {number:g} instead of using a fact placeholder")

    return len(paths), problems


def format_value(value):
    if isinstance(value, int) and value >= 1000:
        return f"{value:,}"
    return str(value)


def fill_placeholders(template, facts):
    def replace(match):
        value = look_up(facts, match.group(1))
        return format_value(value) if value is not None else match.group(0)
    return re.sub(PLACEHOLDER_PATTERN, replace, template)


if __name__ == "__main__":
    facts = {"total_tickets": 2000, "reopen_rate_pct": 7.5,
             "sla_attainment_pct_by_priority": {"P4": 73.4},
             "open_tickets_older_than_14_days": 1,
             "data_quality_notes": ["5 duplicate tickets removed"]}

    tests = {
        "Correct": "P4 attainment is {{sla_attainment_pct_by_priority.P4}}% across {{total_tickets}} tickets.",
        "Typed a number": "This will cut escalations by 25%.",
        "Fake fact": "Satisfaction is {{customer_satisfaction_score}}.",
        "Whole group": "Attainment was {{sla_attainment_pct_by_priority}}.",
        "Name with a number": "{{open_tickets_older_than_14_days}} ticket is older than 14 days.",
    }
    for name, sentence in tests.items():
        used, problems = check_grounding(sentence, facts)
        print(f"{name}: {problems if problems else 'OK'}")

    print("\nFilled:", fill_placeholders(tests["Correct"], facts))
    print("Filled:", fill_placeholders("Adjustments: {{data_quality_notes.0}}.", facts))