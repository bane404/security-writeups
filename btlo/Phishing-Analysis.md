---
title: Phishing Analysis
platform: BTLO
category: Security Operations
difficulty: Easy
skills: Email header analysis, OSINT, reverse DNS, URL triage
---

# Phishing Analysis — Blue Team Labs Online

## Scenario
A user received a phishing email and forwarded it to the SOC. The task was to investigate the email and its attachment to pull out the artifacts an analyst would need to triage and report on the campaign.

## Objective
Extract the key details from the email itself (recipient, subject, send time, sending infrastructure) and then follow the attachment through to the malicious URL it points to, identifying where that page was hosted and what it displayed.

## Methodology

**Primary recipient, subject, and timestamp**
Opened the `.eml` file in a text editor and read the headers directly — `To`, `Subject`, and `Date` give these three answers without needing any tooling. Worth noting the primary recipient wasn't the obvious address in the visible body; the real `To` header pointed elsewhere, which is a good reminder to always check the raw headers rather than trusting what's rendered.

**Originating IP**
Searched the raw headers for the sending IP rather than relying on `Received` chains alone, since those can include intermediate relays. The originating IP was `103.9.171.10`.

**Reverse DNS on the originating IP**
Took that IP to `whois.domaintools.com` and ran a reverse DNS lookup, which resolved to `c5s2-1e-syd.hosting-services.net.au` — a hosting provider, not a mail service, which fits a spoofed/abused sending setup rather than a legitimate mail server.

**Attached file name**
Visible directly in the email's attachment list once opened in a mail client — `Website contact form submission.eml`, an email nested inside the original email.

**URL inside the attachment**
Opened the nested `.eml` and searched for `http`/`https` strings in the body. Found a Blogspot link embedded in the message: `https://35000usdperwwekpodf.blogspot.sg?p=9swghttps://35000usdperwwekpodf.blogspot.co.il?o=0hnd`.

**Hosting service for that URL**
The domain alone gives this away — `blogspot` is Google's Blogger platform, so the page was hosted on Blogger rather than attacker-controlled infrastructure. A common tactic: hosting the malicious landing page on a legitimate, trusted platform to dodge domain reputation checks.

**Page heading via URL2PNG**
Ran the URL through URL2PNG to capture what the page displayed. By the time of analysis the page had already been taken down, and the heading read "Blog has been removed" — the platform had gotten there before the investigation did.

## Key Findings / IOCs

| # | Question | Answer |
|---|----------|--------|
| 1 | Primary recipient | `kinnar1975@yahoo.co.uk` |
| 2 | Subject | `Undeliverable: Website contact form submission` |
| 3 | Date/time sent | `18 March 2021 04:14` |
| 4 | Originating IP | `103.9.171.10` |
| 5 | Reverse DNS host | `c5s2-1e-syd.hosting-services.net.au` |
| 6 | Attached file name | `Website contact form submission.eml` |
| 7 | URL inside attachment | `https://35000usdperwwekpodf.blogspot.sg?p=9swghttps://35000usdperwwekpodf.blogspot.co.il?o=0hnd` |
| 8 | Hosting service | Blogger (Blogspot) |
| 9 | Page heading (URL2PNG) | "Blog has been removed" |

## Lessons Learned
- Headers tell the real story — the visible `To` and body of an email can differ from what's actually in the raw source, so raw header review should always come before trusting the rendered view.
- Reverse DNS on a sending IP is a fast, low-effort way to sanity-check whether mail is coming from real mail infrastructure or a generic hosting box being abused to send phishing.
- Attackers nesting a second `.eml` inside the delivery-failure notice is a deliberate trick — it disguises the phishing payload as an innocuous bounce message, which is more likely to get forwarded around than opened with suspicion.
- Hosting a phishing landing page on a legitimate platform like Blogger is a reputation-evasion tactic — the domain itself won't trip blocklists the way a freshly registered one would, so the URL still needs to be checked even when the domain looks "safe."
- Tools like URL2PNG matter because malicious pages get taken down fast; having a way to see what a URL displayed at the time of the campaign (even after takedown) preserves evidence that would otherwise be lost.
