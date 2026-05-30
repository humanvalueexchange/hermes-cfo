#!/usr/bin/env bash

set -euo pipefail

REPO_DIR="${HOME}/hermes-v2"
HERMES_PY="${HOME}/.hermes/hermes-agent/venv/bin/python"
HERMES_ROOT="${HOME}/.hermes"
ACTIVE_PROFILE="$(cat "${HERMES_ROOT}/active_profile" 2>/dev/null || echo default)"

if [[ "${ACTIVE_PROFILE}" == "default" || -z "${ACTIVE_PROFILE}" ]]; then
  export HERMES_HOME="${HERMES_ROOT}"
else
  export HERMES_HOME="${HERMES_ROOT}/profiles/${ACTIVE_PROFILE}"
fi

mkdir -p "${REPO_DIR}/logs/briefings"
mkdir -p "${HERMES_HOME}/scripts"
install -m 755 "${REPO_DIR}/scripts/hermes_cron/common.py" "${HERMES_HOME}/scripts/common.py"
install -m 755 "${REPO_DIR}/scripts/hermes_cron/nightly_assessment.py" "${HERMES_HOME}/scripts/nightly_assessment.py"
install -m 755 "${REPO_DIR}/scripts/hermes_cron/morning_briefing.py" "${HERMES_HOME}/scripts/morning_briefing.py"
install -m 755 "${REPO_DIR}/scripts/hermes_cron/btc_forecast.py" "${HERMES_HOME}/scripts/btc_forecast.py"

"${HERMES_PY}" <<'PY'
from pathlib import Path
import sys
import os

repo_dir = Path.home() / "hermes-v2"
sys.path.insert(0, str(Path.home() / ".hermes" / "hermes-agent"))

from cron.jobs import create_job, list_jobs, remove_job

workdir = str(repo_dir)

targets = [
    {
        "name": "hermes-nightly-assessment",
        "schedule": "0 2 * * *",
        "deliver": "local",
        "script": "nightly_assessment.py",
        "no_agent": True,
    },
    {
        "name": "hermes-morning-briefing",
        "schedule": "30 6 * * *",
        "deliver": "telegram",
        "script": "morning_briefing.py",
        "no_agent": True,
    },
    {
        "name": "hermes-btc-forecast",
        "schedule": "0 9 * * *",
        "deliver": "telegram",
        "script": "btc_forecast.py",
        "no_agent": True,
    },
    {
        "name": "hermes-nightly-skill",
        "schedule": "0 3 * * *",
        "deliver": "local",
        "no_agent": False,
        "prompt": """You are running the nightly skill-evolution cron job. Work silently and do not ask Hans to continue.

Choose exactly one new self-selected skill that closes the highest-value gap you found in the nightly assessment. Prioritize:
1. trading research
2. execution
3. risk control
4. forecasting
5. market data
6. validation
7. operational autonomy

Steps:
1. Pick a skill name and category (use category "trading" for all CFO skills).
2. Create the directory: ~/.hermes/profiles/main/skills/trading/{skill-name}/
3. Write SKILL.md using EXACTLY this YAML frontmatter format (no deviation):

---
name: {skill-name}
description: "One sentence description of what this skill does."
category: trading
version: 1.0
date: {YYYY-MM-DD}
---

# {skill-name} — Short Title

## Overview
What this skill does and why it matters.

## When to Invoke
- Bullet list of trigger conditions

## Notes
Any implementation notes, data sources, or limitations.

4. Append exactly one line to ~/.hermes/profiles/main/evolution.log in this format:
   {YYYY-MM-DD} | trading/{skill-name} | One sentence summary of what was added

Rules:
- exactly one skill
- do not duplicate an existing skill in ~/.hermes/profiles/main/skills/trading/
- the YAML frontmatter must match the template above exactly (dashes, field names, no extras)
- use bash write tools or the file write tool — do NOT just show the content without writing it

Success gate (run after writing):
- verify the SKILL.md file exists and is non-empty
- verify the evolution log entry was appended
- if either check fails, treat the job as FAIL

Your final response must start with PASS or FAIL and include the skill name and file path.""",
    },
]

target_names = {job["name"] for job in targets}

for job in list_jobs(include_disabled=True):
    if job.get("name") in target_names:
        remove_job(job["id"])

for job in targets:
    create_job(
        prompt=job.get("prompt"),
        schedule=job["schedule"],
        name=job["name"],
        deliver=job["deliver"],
        workdir=workdir,
        script=job.get("script"),
        no_agent=job.get("no_agent", False),
    )

print("Installed Hermes cron jobs:")
for job in targets:
    print(f"- {job['name']} @ {job['schedule']} -> {job['deliver']}")
print(f"- HERMES_HOME={os.environ['HERMES_HOME']}")
PY

if [[ "${HERMES_HOME}" != "${HERMES_ROOT}" ]]; then
  HERMES_HOME="${HERMES_ROOT}" "${HERMES_PY}" <<'PY'
from pathlib import Path
import sys

sys.path.insert(0, str(Path.home() / ".hermes" / "hermes-agent"))

from cron.jobs import list_jobs, remove_job

target_names = {
    "hermes-nightly-assessment",
    "hermes-morning-briefing",
    "hermes-btc-forecast",
    "hermes-nightly-skill",
}

for job in list_jobs(include_disabled=True):
    if job.get("name") in target_names:
        remove_job(job["id"])
PY
fi

bash "${REPO_DIR}/scripts/validate-hermes-cron.sh"
