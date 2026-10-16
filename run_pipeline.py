import subprocess
import sys

STEPS = [
    ("Generate synthetic tickets", "src/generate_data.py"),
    ("Validate data quality", "src/validate.py"),
    ("Classify ticket themes with the LLM", "src/categorise.py"),
    ("Write the grounded narrative", "src/narrative.py"),
    ("Build the HTML report", "src/report.py"),
]

for number, (name, script) in enumerate(STEPS, start=1):
    print(f"\n=== Step {number} of {len(STEPS)}: {name} ===")
    result = subprocess.run([sys.executable, script])
    if result.returncode != 0:
        print(f"\nStopped: '{name}' failed. Fix the error above and run again.")
        sys.exit(1)

print("\nDone. Open reports/service_report.html to see the report.")