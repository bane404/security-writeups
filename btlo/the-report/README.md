---
title: The Report
platform: BTLO
category: Security Operations
Verify: https://blueteamlabs.online/achievement/share/challenge/166217/42
difficulty: Easy
skills: Threat intel analysis, report review
---

# The Report — BTLO

**Category:** Security Operations | **Difficulty:** Easy | **Points:** 10

## Scenario
Working in a newly established SOC, tasked with reviewing a 2022 threat
detection report and pulling out actionable findings for the team. The
report provided was Red Canary's 2022 Threat Detection Report.

## Objective
Analyze the report and answer a set of questions covering notable 2021/2022
threats: a supply-chain attack tied to a Java logging library, top MITRE
ATT&CK techniques by prevalence, Exchange Server vulnerabilities, a
zero-day driver RCE, malicious script execution parent processes, and
ransomware-related RDP hardening.

## Methodology
Rather than reading the ~40-page PDF cover to cover, I treated it like a
search problem: opened the report in a PDF viewer and used Ctrl+F against
keywords pulled directly from each question's wording (e.g. searching
"TOP TECHNIQUES" for the MITRE technique question, "Exchange" for the
vulnerability question, "coin miner" for the outdated-software question).
This is a faster and more realistic approach for a SOC analyst than linear
reading — in practice you rarely have time to read a 40-page vendor report
end to end, so keyword-driven scanning against the specific data point you
need is the actual skill being tested here.

For the driver CVE question specifically, once the report text pointed me
toward the print-spooler vulnerability, I cross-referenced it against the
public GitHub PoC/advisory activity around PrintNightmare to confirm the
exact CVE number and mechanism — a good habit for verifying a report's
claims against a primary source rather than trusting the report's
phrasing alone.

## Key Findings
- **Supply chain attack (Java logging library, late 2021):** Log4Shell,
  the RCE vulnerability in the Log4j logging library (CVE-2021-44228)
- **Most prevalent MITRE ATT&CK technique (>50% of customers):** T1059 —
  Command and Scripting Interpreter
- **Exchange Server vulnerabilities:** ProxyLogon and ProxyShell
- **Zero-day driver RCE (CVE):** CVE-2021-34527 ("PrintNightmare") — a
  flaw in how the Windows Print Spooler service authenticates printer
  driver DLL loading, allowing an unprivileged user to gain remote
  SYSTEM-level code execution
- **Adversary groups leveraging SEO poisoning for initial access:**
  Gootloader (Gootkit) and Yellow Cockatoo
- **Detection rule parent process for malicious JS execution:**
  `wscript.exe`
- **Conti affiliate precursor malware:** Qbot, BazarLoader, IcedID
- **Outdated software targeted by coin miners:** JBoss and WebLogic
- **Ransomware group threatening DDoS as extortion leverage:** Fancy
  Lazarus
- **RDP hardening measure against ransomware:** enforcing MFA on RDP
  connections

## Lessons Learned
Keyword-driven searching through a large report is a legitimate and
efficient triage technique, not a shortcut to be embarrassed about — the
real skill is knowing which terms to search for based on how the question
is phrased. I also learned the value of double-checking a CVE against an
external, primary source (GitHub advisory/patch notes) rather than taking
a single report's phrasing at face value, since vendor reports sometimes
use nicknames or shorthand that don't map 1:1 to the canonical CVE ID.

Going forward: I'll keep a lightweight running notes file during future
challenges (even just search terms + answers as I go) so write-ups like
this one don't rely purely on memory afterward.
