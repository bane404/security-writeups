\---

title: JetBrains
platform: CyberDefenders
category: Network Forensics
difficulty: Easy
skills: Wireshark packet analysis, HTTP stream analysis, CVE identification, malicious plugin analysis, MITRE ATT\&CK mapping
---

# JetBrains — CyberDefenders

## Scenario

A JetBrains TeamCity server was compromised. I was given a PCAP (`Capture.pcap`) of the traffic and asked to work out who the attacker was, how they got in, and what they did once inside.

## Objective

Identify the attacker's IP address, the server version and CVE that was exploited, the credentials the attacker used, the file they uploaded, when it first ran, and which file they tampered with afterwards.

## Methodology

**1. Identifying the attacker's IP**
Started with **Statistics → Conversations → IPv4** to see who talked to the server the most. Two external addresses looked almost identical by volume and duration (`156.197.187.149` and `23.158.56.196`), so packet counts alone could not decide it. Filtering on POST requests, which is where an attacker changes things instead of just browsing, showed the suspicious ones:

```
http.request.method == "POST" \\\&\\\& ip.src == 23.158.56.196
```

The POSTs from `23.158.56.196` went to REST API endpoints through an odd `/hax?jsp=...` path and to a plugin upload page, which is not normal user activity.

The server being attacked is `172.31.25.119`, listening on port `8111` (TeamCity's default).

**2. Identifying the server version**
Filtered for the server's responses to the attacker, followed an HTTP stream, and searched it for `version`:

```
http.response \\\&\\\& ip.dst == 23.158.56.196
```

The match that describes the server itself sits inside `ReactUI.extendServerInfo(...)`, where the application reports information about itself:

```html
ReactUI.extendServerInfo({
  licenseIsCloud: false,
  licenseIsEnterprise: false,
  version: '2023.11.3 (build 147512)',
});
```

The rule I used when picking a match: the version has to belong to the server software, not to a library it ships or to a client User-Agent. The attacker's own first request (step 3) also returned the same version from the REST API, which confirms it.

**3. Identifying the CVE**
TeamCity `2023.11.3` is affected by two vulnerabilities disclosed together in February 2024: `CVE-2024-27198` (authentication bypass, CVSS 9.8) and `CVE-2024-27199` (path traversal, CVSS 7.3). Both were fixed in `2023.11.4`. The version narrows it down but does not separate the two, and a high score is not evidence that it was the one used.

The traffic does. `CVE-2024-27198` abuses a request to a nonexistent page with a `jsp` parameter and `;.jsp` appended, which skips authentication:

```
ip.src == 23.158.56.196 \\\&\\\& http.request.uri contains ";.jsp"
```

Many requests had this pattern. The clearest example is TCP stream `365` (**Follow → HTTP Stream**), with no credentials in any of the requests:

```
GET  /hax?jsp=/app/rest/server;.jsp
POST /hax?jsp=/app/rest/users;.jsp
POST /hax?jsp=/app/rest/users/id:2/tokens/mD5r0yemB0;.jsp
```

The first request returned `200` with the server details, including the version. The second created a new user with the `SYSTEM\\\_ADMIN` role, and the server answered `200` and returned the new user (`id="2"`). The third requested an access token for that user. An unauthenticated client creating an administrator is the authentication bypass in action.

Answer: `CVE-2024-27198`

**4. Recovering the credentials**
The JSON body of the `POST /hax?jsp=/app/rest/users;.jsp` request shows the account the attacker created:

```json
{"username": "c91oyemw", "password": "CL5vzdwLuK", "email": "c91oyemw@example.com", "roles": {"role": \\\[{"roleId": "SYSTEM\\\_ADMIN", "scope": "g"}]}}
```

The server's `200` response echoed the new user back, so the account was created. Credentials: `c91oyemw` / `CL5vzdwLuK`.

**5. Finding the uploaded file**
Searched for the plugin name across the attacker's traffic to the server:

```
ip.src == 23.158.56.196 \\\&\\\& ip.dst == 172.31.25.119 \\\&\\\& frame contains "NSt8bHTg"
```

Packet `24825` is a `POST /admin/pluginUpload.html` with content type `application/zip`, sent at `2024-06-30 08:03:06`. The uploaded file is `NSt8bHTg.zip`. The server's response was the plugins admin page showing "Uploaded plugin: NSt8bHTg" with an "Enable uploaded plugins" button. At this point the plugin is uploaded but not running yet, so the upload is not the execution.

**6. Finding the first execution**
Looking at the packets that reference the plugin after the upload, packet `25566` is the first request to a page the plugin created:

```
POST /plugins/NSt8bHTg/NSt8bHTg.jsp HTTP/1.1
```

Time: `2024-06-30 08:03:57`, 51 seconds after the upload. The server's `Date` header in stream `365` reads `08:02:49 GMT`, about 17 seconds before the upload packet, so the Wireshark times line up with UTC. Similar POSTs to the same JSP repeat every 5 to 10 seconds afterwards, which looks like the attacker running commands one at a time.

My first guess was that the trigger would be a GET request. It was a POST, which fits a web shell taking its commands in the request body. A filter restricted to GET would have missed it, so I now build filters from what the traffic shows instead of what I expect.

**7. Finding the tampered file**
The file the attacker tampered with is `Creds.txt`, the text file holding the admin credentials.

## Key Findings / IOCs

|Type|Value|
|-|-|
|Attacker IP|`23.158.56.196`|
|Target server|`172.31.25.119:8111` (TeamCity)|
|Server version|`2023.11.3 (build 147512)`|
|Exploited CVE|`CVE-2024-27198`|
|Auth bypass pattern|`/hax?jsp=/app/rest/...;.jsp`|
|Attacker-created account|`c91oyemw` / `CL5vzdwLuK` (`SYSTEM\\\_ADMIN`)|
|Access token name|`mD5r0yemB0`|
|Upload endpoint|`/admin/pluginUpload.html`|
|Uploaded file|`NSt8bHTg.zip`|
|Upload time|`2024-06-30 08:03:06`|
|First execution|`2024-06-30 08:03:57`|
|Web shell path|`/plugins/NSt8bHTg/NSt8bHTg.jsp`|
|Tampered file|`Creds.txt`|
|Attacker User-Agent|`Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36`|

## MITRE ATT\&CK

|Technique|ID|
|-|-|
|Exploit Public-Facing Application|`T1190`|
|Create Account|`T1136`|
|Server Software Component: Web Shell|`T1505.003`|

## Lessons Learned

* Packet and byte counts do not tell you who the attacker is. Two external IPs had almost the same shape in the Conversations table, and the request content (methods, URIs, responses) is what separates them.
* A CVSS score is not evidence. The version gave me two candidate CVEs, and only the request pattern in the capture shows which one was used. Here it was `;.jsp` on a nonexistent page, followed by an unauthenticated request that created an admin user.
* When a search returns several matches for something like `version`, ask whose version it is. The server's own version, not a library's or a client's, is the one that matters.
* Uploading a payload and running it are separate events with separate timestamps. The upload response showed the plugin waiting to be enabled, and the first request to the plugin's own JSP was the real execution.
* Build filters from what the traffic shows, not from what I expect it to show.
* Detection ideas from this chain: alert on `;.jsp` in request URIs, on any `POST /admin/pluginUpload.html`, on new users created with `SYSTEM\\\_ADMIN`, and on new directories under `/plugins/`. TeamCity should not be reachable from the internet, and `2023.11.4` or later closes this hole.

