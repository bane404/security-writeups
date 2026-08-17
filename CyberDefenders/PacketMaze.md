---
title: OpenWire
platform: CyberDefenders
category: Network Forensics
difficulty: Medium
skills: Wireshark, PCAP analysis, TCP stream reconstruction, Java deserialization vulnerabilities, CVE research
---

# OpenWire — CyberDefenders

## Scenario
As a tier-2 SOC analyst, I get an escalation from tier-1 about a public-facing server that's been flagged for making outbound connections to multiple suspicious IPs. Standard incident response kicks in — the server gets isolated from the network to stop any lateral movement or exfiltration, and a packet capture is pulled from the NSM tooling for analysis. My job is to work through that PCAP and figure out exactly what happened.

## Objective
Identify the command-and-control infrastructure involved, trace the initial exploitation vector back to the specific vulnerable service and port, find any files the attacker dropped on the server, and pin down the exact vulnerability (CVE, Java class/method) that made the compromise possible.

## Methodology
I opened the PCAP in Wireshark and started from the network layer before working down into individual streams.

- **Mapping the server's external connections**: Statistics → Conversations → IPv4 gave a clean picture of who the server was talking to. One external IP stood out immediately by packet volume and data transferred — that became the primary C2 candidate.
- **Finding the exploited service and port**: with the challenge name pointing at the OpenWire protocol, I checked the destination port on the earliest suspicious packets in that conversation. That port number, cross-referenced against what runs on it by default, named the vulnerable service directly — Apache ActiveMQ.
- **Finding the second C2 server**: going back to the Conversations view, two more external IPs showed up talking to the server beyond the primary C2. Filtering on one of them showed the server requesting a resource from it; following that TCP stream showed the response starting with ELF magic bytes, meaning it was serving a Linux executable rather than a webpage — confirming it as a second stage in the attacker's infrastructure.
- **Finding the dropped file**: following the TCP stream tied to the initial exploitation packet showed the payload being sent to the server, including the destination path it was written to and the filename it was dropped under.
- **Finding the Java class used in the exploit**: the same stream that revealed the dropped file also contained the XML payload sent over the OpenWire protocol. That XML invoked a specific Java class to actually execute a command on the underlying system.
- **Identifying the CVE**: with the vulnerable service, protocol, and Java class in hand, this was a straightforward pivot to public vulnerability research — searching for known Apache ActiveMQ RCEs involving OpenWire and unsafe deserialization led straight to the CVE tied to this exact exploitation chain.
- **Finding the specific vulnerable method**: the CVE identifier alone doesn't say which method/class combination is actually unsafe, so this took digging into vendor writeups and technical breakdowns of the CVE to find the specific class and method in ActiveMQ's marshalling code responsible for the unsafe object instantiation.

## Key Findings / IOCs
- Two separate external C2 IPs were involved: one handling the initial exploitation traffic over the OpenWire protocol, the other serving a second-stage ELF payload.
- The exploited service was Apache ActiveMQ, reachable over its default OpenWire port, rather than a typical web-facing port.
- The attacker delivered an XML payload over OpenWire that abused Java's `ProcessBuilder` class to spawn an arbitrary system process.
- A reverse shell executable was dropped into the server's `/tmp` directory.
- The vulnerability maps to CVE-2023-46604, a critical unauthenticated RCE in Apache ActiveMQ caused by unsafe class instantiation during OpenWire message deserialization — specifically in ActiveMQ's marshaller code that reconstructs Throwable objects from the wire format without validating what class it's being asked to instantiate.

## Lessons Learned
This lab was less about clever Wireshark filtering and more about recognizing that a protocol most people have never heard of (OpenWire) can be a full RCE vector if the service behind it trusts what it's deserializing. The network side of the investigation was fast once I had Conversations and Follow TCP Stream doing the heavy lifting — the real time sink was the CVE research at the end, since knowing "CVE-2023-46604" doesn't automatically tell you which class/method is unsafe; that took reading actual vendor technical breakdowns rather than just the CVE summary. The broader takeaway: exposing a message broker like ActiveMQ to untrusted input without validating the classes it's willing to deserialize is a textbook deserialization vulnerability, and it's worth remembering that "internal" services like message brokers are still worth hardening if they're reachable at all — this one was public-facing, which is what made the whole chain possible in the first place.
