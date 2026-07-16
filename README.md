## Security Write-ups
Documented walkthroughs of blue team challenges I've completed — investigation methodology, findings, and lessons learned. Written to reinforce my own process and track progress as I build toward a SOC analyst role.
Each write-up follows the same structure: scenario, objective, methodology, key findings, and lessons learned — not just the answer, but how I got there.

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
Each platform gets a folder; each challenge gets a subfolder with its own README. New platforms (e.g. THM, HTB) are added the same way as they come up. Browse the folders above for the full list of write-ups.

Write-up format
Every challenge README follows this template:
```markdown
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
About
Part of my self-directed SOC analyst training, alongside a home lab running Wazuh and Suricata ([soc-blue-team-lab](https://github.com/bane404/soc-blue-team-lab)) and ongoing certification prep.
