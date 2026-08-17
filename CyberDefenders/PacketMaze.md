---
title: PacketMaze
platform: CyberDefenders
category: Network Forensics
difficulty: Easy
skills: Wireshark, PCAP analysis, TLS handshake analysis, EXIF metadata, DNS analysis
---

# PacketMaze — CyberDefenders

## Scenario
Working as an analyst for a security service provider, I was given a packet capture (PCAP) of a customer's employee whose activity had been flagged for monitoring — a possible insider threat case. The only source of evidence was the PCAP itself.

## Objective
Answer a set of questions about the employee's network activity using nothing but the packet capture: credentials sent in the clear, DNS and browsing activity, device identification, TLS handshake metadata, and file metadata pulled from a transferred image.

## Methodology

**FTP password**
FTP sends everything in cleartext, so filtering on `ftp` isolates the control channel directly. Following the TCP stream shows the `USER`/`PASS` exchange in plain text — password was `AfricaCTF2021`.

**IPv6 DNS server used by 192.168.1.26**
Filtered `dns` traffic to/from the host, then checked the source address of the DNS responses. The resolver was answering from a link-local IPv6 address, `fe80::c80b:adff:feaa:1db7`.

**Domain looked up in packet 15174**
Jumped straight to the frame with `frame.number==15174` and read the DNS query in that packet — `www.7-zip.org`.

**UDP packets from 192.168.1.26 to 24.39.217.246**
Filtered `udp && ip.src==192.168.1.26 && ip.dst==24.39.217.246` and counted the matching packets (cross-checked against Statistics → Conversations → UDP tab). Total: 10.

**MAC address of the monitored system**
Went to Statistics → Conversations → Ethernet tab and matched the entry for `192.168.1.26` to get its MAC: `c8:09:a8:57:47:93`.

**Camera model for 20210429_152157.jpg**
The image had been transferred over a file protocol in the capture, so I used File → Export Objects to pull it out of the stream, then checked its EXIF metadata. The `Model` field read `LM-Q725K`.

**Ephemeral public key for TLS session da4a0000...**
Filtered on `tls.handshake.session_id == da4a0000342e4b73459d7360b4bea971cc303ac18d29b99067e46d16cc07f4ff` to land on that specific handshake, then opened the Server Key Exchange / Server Hello packet and read the EC Diffie-Hellman public key field.

**First TLS 1.3 client random for protonmail.com**
Resolved which IP protonmail.com pointed to via Statistics → Resolved Addresses, filtered TLS traffic to that IP, and pulled the `Random` field from the first Client Hello.

**Country of registration for the FTP server's MAC vendor**
Found the FTP server's MAC the same way as above (Conversations → Ethernet), then looked up the OUI (first three octets) against a MAC vendor database — registered in the United States.

**Time a non-standard folder was created on the FTP server (20th of April)**
Filtered `ftp` traffic on that date and scanned the control stream for an `MKD` (make directory) command — timestamped `17:53`.

**URL visited on 104.21.89.171**
Filtered `ip.addr==104.21.89.171 && http` and read the `Host` header / GET request in the stream — `http://dfir.science/`.

## Key Findings / IOCs

| # | Question | Answer |
|---|----------|--------|
| 1 | FTP password | `AfricaCTF2021` |
| 2 | IPv6 DNS server (192.168.1.26) | `fe80::c80b:adff:feaa:1db7` |
| 3 | Domain in packet 15174 | `www.7-zip.org` |
| 4 | UDP packets, 192.168.1.26 → 24.39.217.246 | `10` |
| 5 | MAC of monitored system | `c8:09:a8:57:47:93` |
| 6 | Camera model (20210429_152157.jpg) | `LM-Q725K` |
| 7 | Ephemeral public key (session da4a0000...) | `04edcc123af7b13e90ce101a31c2f996f471a7c8f48a1b81d765085f548059a550f3f4f62ca1f0e8f74d727053074a37bceb2cbdc7ce2a8994dcd76dd6834eefc5438c3b6da929321f3a1366bd14c877cc83e5d0731b7f80a6b80916efd4a23a4d` |
| 8 | First TLS 1.3 client random (protonmail.com) | `24e92513b97a0348f733d16996929a79be21b0b1400cd7e2862a732ce7775b70` |
| 9 | FTP server MAC vendor country | `United States` |
| 10 | Non-standard FTP folder creation time (20th April) | `17:53` |
| 11 | URL visited on 104.21.89.171 | `http://dfir.science/` |

## Lessons Learned
- FTP has no place carrying anything sensitive — the credentials were sitting in plain text for anyone capturing traffic.
- TLS 1.3 encrypts the handshake body, but session IDs, client randoms, and certificate/key exchange fields are still visible and enough to fingerprint or correlate a connection without decrypting it.
- Files transferred over plaintext protocols carry their metadata with them — EXIF data on a transferred image gave up the device model without needing the device itself.
- Wireshark's Statistics menu (Conversations, Resolved Addresses) is usually faster than manually filtering when the question is about volume or endpoint identity rather than packet content.
