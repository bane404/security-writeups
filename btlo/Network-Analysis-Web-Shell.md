---
title: Network Analysis – Web Shell
platform: BTLO
category: Network Forensics
difficulty: Easy
skills: PCAP analysis, port scan detection, HTTP traffic analysis, web shell identification
---

# Network Analysis – Web Shell — Blue Team Labs Online

## Scenario
Investigating a packet capture covering a full attack chain against a web application — starting from initial reconnaissance against the host, through to a file upload vulnerability being abused to drop a web shell, and finishing with the attacker using that shell to get command execution and pivot to a reverse shell.

## Objective
Trace the attack in order: identify who scanned the target and how, identify the follow-up recon tools used against the discovered web service, find the vulnerable upload point and the web shell it delivered, confirm how the shell accepted commands, and identify the first command run and the reverse shell connection that followed.

## Methodology

**Port scan source and range**
Filtered the capture for the high volume of short, sequential connection attempts characteristic of a scan — many source ports from one host hitting a wide range of destination ports on the target in quick succession. That traffic all came from `10.251.96.4`, covering ports `1-1024` (the well-known port range).

**Scan type**
Looked at the TCP flags on the scanning packets rather than the payload — the scanning host was sending SYN packets and not completing the three-way handshake on the vast majority of ports, only following through where a port actually answered. That flag pattern (SYN, then RST or nothing back from closed ports) is the signature of a TCP SYN scan — Nmap's default scan type.

**Additional recon tools**
Once the open web port was identified, follow-up HTTP traffic from the same source showed automated request patterns rather than a human browsing — checked the `User-Agent` header on the requests immediately after the scan and found two distinct signatures: `Gobuster 3.0.1` (directory/path brute-forcing) and `sqlmap 1.4.7` (automated SQL injection testing).

**Upload vector**
Filtered HTTP traffic for POST requests carrying file uploads (`multipart/form-data`) from the attacker's IP and found the malicious file being submitted through `editprofile.php` — a profile-editing feature that apparently accepted file uploads without validating what was actually being uploaded.

**Web shell name**
The file uploaded through that form was `dbfunctions.php` — named to blend in with legitimate application files rather than looking obviously malicious.

**Command execution parameter**
Followed the attacker's subsequent GET requests to `dbfunctions.php` and found they were all passing a `cmd` parameter in the query string — the web shell was written to take that parameter's value and execute it directly on the server.

**First command executed**
The first request to the shell carrying a `cmd` value ran `id` — the standard first move to confirm code execution and check what user context the shell is running as before doing anything more involved.

**Reverse shell and port**
After confirming execution, the attacker's next `cmd` value initiated an outbound connection back to their own listener rather than working purely through the web shell — a reverse shell, connecting out on port `4422`.

## Key Findings / IOCs

| # | Question | Answer |
|---|----------|--------|
| 1 | Port scan source IP | `10.251.96.4` |
| 2 | Scanned port range | `1-1024` |
| 3 | Scan type | TCP SYN scan |
| 4 | Additional recon tools | Gobuster 3.0.1, sqlmap 1.4.7 |
| 5 | Upload vector file | `editprofile.php` |
| 6 | Web shell filename | `dbfunctions.php` |
| 7 | Command execution parameter | `cmd` |
| 8 | First command executed | `id` |
| 9 | Shell connection type | Reverse shell |
| 10 | Reverse shell port | `4422` |

## Lessons Learned
- A SYN scan against the full well-known port range before any application-layer activity is a strong early indicator — catching this stage means catching the attacker before they've found anything to exploit.
- Automated tool fingerprints in the `User-Agent` header (Gobuster, sqlmap) are free detection opportunities as long as the attacker doesn't bother spoofing them — which, in this case, they didn't.
- File upload features are a recurring weak point when they don't validate file type or content — `editprofile.php` accepting a `.php` file at all was the root cause of everything that followed.
- Naming a web shell after a plausible application file (`dbfunctions.php`) is a basic evasion tactic aimed at anyone eyeballing the file listing — validating uploaded file contents, not just extensions, and diffing the file listing against a known-good baseline would both catch this.
- `id` as the first command is close to universal once an attacker gets code execution — it's cheap, safe, and tells them immediately what privilege level they're working with, which is worth having as a detection signature on its own for any endpoint capable of command execution.
