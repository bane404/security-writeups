#!/usr/bin/env python3
"""
Regenerates the challenge index table in README.md by scanning every
<platform>/<challenge>/README.md file for a YAML front-matter block.

Each challenge README.md must start with a front-matter block like:

---
title: PacketMaze
platform: CyberDefenders
category: Network Forensics
difficulty: Medium
skills: Wireshark, IOC extraction, multi-protocol analysis
---

Usage:
    python3 generate_readme.py

Run this from the repo root before committing. It edits README.md in
place, replacing everything between the markers:
    <!-- INDEX_START -->
    <!-- INDEX_END -->
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent
START_MARKER = "<!-- INDEX_START -->"
END_MARKER = "<!-- INDEX_END -->"

# Folders to skip when scanning for challenge subfolders
SKIP_DIRS = {".git", ".github", "__pycache__"}


def parse_front_matter(readme_path: Path) -> dict:
    text = readme_path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}
    fm_text = match.group(1)
    data = {}
    for line in fm_text.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            data[key.strip()] = value.strip()
    return data


def find_challenges():
    challenges = []
    for platform_dir in sorted(ROOT.iterdir()):
        if not platform_dir.is_dir() or platform_dir.name in SKIP_DIRS:
            continue
        for challenge_dir in sorted(platform_dir.iterdir()):
            readme = challenge_dir / "README.md"
            if not readme.exists():
                continue
            fm = parse_front_matter(readme)
            if not fm:
                continue
            rel_link = readme.relative_to(ROOT).parent
            challenges.append({
                "title": fm.get("title", challenge_dir.name),
                "platform": fm.get("platform", platform_dir.name),
                "category": fm.get("category", "-"),
                "difficulty": fm.get("difficulty", "-"),
                "skills": fm.get("skills", "-"),
                "link": f"./{rel_link}/",
            })
    return challenges


def build_table(challenges):
    if not challenges:
        return "_No write-ups yet — check back soon._"
    header = "| Challenge | Platform | Category | Difficulty | Key Skills |\n"
    header += "|---|---|---|---|---|\n"
    rows = []
    for c in challenges:
        rows.append(
            f"| [{c['title']}]({c['link']}) | {c['platform']} | "
            f"{c['category']} | {c['difficulty']} | {c['skills']} |"
        )
    return header + "\n".join(rows)


def update_readme(table: str):
    readme_path = ROOT / "README.md"
    text = readme_path.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        re.DOTALL,
    )
    replacement = f"{START_MARKER}\n{table}\n{END_MARKER}"
    if pattern.search(text):
        new_text = pattern.sub(replacement, text)
    else:
        # Markers not found — append at the end as a fallback
        new_text = text.rstrip() + f"\n\n## Index\n\n{replacement}\n"
    readme_path.write_text(new_text, encoding="utf-8")


def main():
    challenges = find_challenges()
    table = build_table(challenges)
    update_readme(table)
    print(f"Updated README.md with {len(challenges)} challenge(s).")


if __name__ == "__main__":
    main()
