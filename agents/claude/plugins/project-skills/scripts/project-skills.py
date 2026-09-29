#!/usr/bin/env python3
"""Advertise project .agents skills through Claude Code's SessionStart hook."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def project_directories(cwd: Path) -> list[Path]:
    directories = [cwd, *cwd.parents]
    for index, directory in enumerate(directories):
        if (directory / ".git").exists():
            return list(reversed(directories[: index + 1]))
    return [cwd]


def skill_description(path: Path) -> str:
    try:
        lines = path.read_text().splitlines()
    except (OSError, UnicodeError):
        return ""
    if not lines or lines[0] != "---":
        return ""
    for index, line in enumerate(lines[1:], start=1):
        if line == "---":
            break
        if line.startswith("description:"):
            value = line.partition(":")[2].strip()
            if value in {"|", ">", "|-", ">-"}:
                block = []
                for following in lines[index + 1 :]:
                    if not following.startswith((" ", "\t")):
                        break
                    block.append(following.strip())
                return " ".join(block)
            return value.strip("\"'")
    return ""


def main() -> None:
    event = json.load(sys.stdin)
    cwd = Path(event["cwd"]).resolve()
    skills: list[str] = []
    for directory in project_directories(cwd):
        root = directory / ".agents" / "skills"
        if not root.is_dir():
            continue
        for skill in sorted(root.iterdir()):
            path = skill / "SKILL.md"
            if not path.is_file():
                continue
            description = skill_description(path)[:300]
            skills.append(f"- {skill.name}: {description} ({path})")

    if not skills:
        return
    context = (
        "Project skills are available in .agents/skills. When a skill matches the task, "
        "read its SKILL.md and follow it. These skills are project instructions, "
        "not Claude slash commands.\n" + "\n".join(skills)
    )
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": context[:10000],
    }}))


if __name__ == "__main__":
    main()
