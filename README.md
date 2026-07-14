## Security Write-ups
Documented walkthroughs of blue team challenges I've completed — investigation methodology, findings, and lessons learned. Written to reinforce my own process and track progress as I build toward a SOC analyst role.
Each write-up follows the same structure: scenario, objective, methodology, key findings, and lessons learned — not just the answer, but how I got there.
Index
<!-- INDEX_START -->
| Challenge | Platform | Category | Difficulty | Key Skills |
|---|---|---|---|---|
| [The Report](./btlo/the-report/) | BTLO | Security Operations | Easy | Threat intel analysis, report review |
<!-- INDEX_END -->
(This table is auto-generated from each challenge's README — see `generate_readme.py`.)
Structure
```
security-writeups/
├── btlo/
│   └── <challenge-name>/
│       └── README.md
└── cyberdefenders/
    └── <challenge-name>/
        └── README.md
```
Each platform gets a folder; each challenge gets a subfolder with its own README. New platforms (e.g. THM, HTB) are added the same way as they come up.
Write-up format
Every challenge README starts with a small front-matter block, then follows this template:
```markdown
---
title: Challenge Name
platform: BTLO
category: Security Operations
difficulty: Easy
skills: comma, separated, skills
---

# Challenge Name — Platform

## Scenario
The premise, in my own words.

## Objective
What I was asked to find or determine.

## Methodology
The actual investigation steps, in order.

## Key Findings / IOCs
Attacker IPs, payloads, techniques, artifacts.

## Lessons Learned
What this taught me, what I'd do differently.
```
The front-matter block is what powers the auto-generated index table above — fill it in accurately and the table updates itself.
About
Part of my self-directed SOC analyst training, alongside a home lab running Wazuh and Suricata (soc-blue-team-lab).
https://blueteamlabs.online/public/user/7a6d290e29071e3c9faea9
