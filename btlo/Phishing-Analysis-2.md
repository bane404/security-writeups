---
title: Phishing Analysis 2
platform: BTLO
category: Security Operations
difficulty: Easy
skills: Email header analysis, Base64 decoding, URL triage, OSINT
---

# Phishing Analysis 2 — Blue Team Labs Online

## Scenario
A follow-up to the first Phishing Analysis lab, using a different sample: another phishing email forwarded to the SOC for investigation. This one adds a wrinkle over the first — the email body itself is encoded, so getting to the embedded URLs takes an extra decoding step before the usual triage.

## Objective
Pull the standard header artifacts (sender, recipient, subject, timestamp), identify which brand the email is impersonating, decode the body to recover the URLs it contains, and then chase those URLs down — including one that, oddly, resolves to a Facebook profile.

## Methodology

**Sender, recipient, subject, and timestamp**
Opened the `.eml` in a text editor and read the headers directly. Sender was `amazon@zyevantoby.cn` — a domain with nothing to do with Amazon, sent to `saintington73@outlook.com`, subject `Your Account has been locked`, timestamped `Wed, 14 Jul 2021 01:40:32 +0900` in the raw `Date` header.

**Company being impersonated**
Obvious from both the subject line and the sender's display name — the email was styled to look like an Amazon account-lockout notice, despite the sending domain giving it away immediately.

**Encoding scheme in the body**
Unlike the first lab, this email's body wasn't plaintext. Looking at the raw source in a text editor, the main content was Base64 — a long block of encoded text sitting where the HTML body should be.

**CTA button URL**
Decoded the Base64 body (CyberChef makes this fast — paste in, add a "From Base64" step) to get the raw HTML back, then searched the decoded output for the link behind the main call-to-action button. It resolved to an Outlook SafeLinks-wrapped redirect pointing to a lookalike domain (`amaozn.zzyuchengzhika.cn`) — a classic case of a legitimate corporate link-wrapping service being abused to launder a malicious link past filters that trust `safelinks.protection.outlook.com`.

**URL2PNG heading**
Ran the decoded destination URL through URL2PNG to see what the page displayed without visiting it directly. The site returned "This web page could not be loaded." — infrastructure that had already gone offline by the time of analysis.

**Company logo URL**
Still working from the decoded HTML, found the `<img>` source for the Amazon logo used in the email template — hosted on Squarespace's CDN rather than Amazon's own infrastructure, which is common when a phishing kit borrows brand assets from wherever they're publicly hosted rather than hosting a copy themselves.

**Facebook profile URL and username**
Continuing through the decoded body for other embedded links turned up something unrelated to the Amazon pretext — a Facebook profile URL. The username in the URL path (not the display name shown on the profile) was `amir.boyka.7`.

## Key Findings / IOCs

| # | Question | Answer |
|---|----------|--------|
| 1 | Sending email address | `amazon@zyevantoby.cn` |
| 2 | Recipient email address | `saintington73@outlook.com` |
| 3 | Subject line | `Your Account has been locked` |
| 4 | Company impersonated | Amazon |
| 5 | Date/time sent | `Wed, 14 Jul 2021 01:40:32 +0900` |
| 6 | CTA button URL | SafeLinks redirect → `amaozn.zzyuchengzhika.cn` (lookalike domain) |
| 7 | URL2PNG heading | "This web page could not be loaded." |
| 8 | Body encoding scheme | Base64 |
| 9 | Logo URL | Squarespace CDN-hosted Amazon logo |
| 10 | Facebook profile username | `amir.boyka.7` |

## Lessons Learned
- Encoding the body doesn't add real protection against analysis — it's a step to slow down automated scanning and casual review, not a serious obstacle once you know to check the raw source for non-plaintext content.
- Trusted link-wrapping services (Outlook SafeLinks, and similarly Google's or other redirect services) can be abused to smuggle a malicious destination past filters and past a user's own instinct — the visible domain in a wrapped link means nothing without unwrapping it.
- A domain like `amaozn.zzyuchengzhika.cn` is a typosquat riding on a suspicious TLD/registrar combination — worth flagging both independently, since either one alone is a decent phishing indicator.
- Not every artifact in a phishing sample belongs to the pretext. An unrelated Facebook profile link buried in the body is a reminder to extract and check every URL in a sample, not just the obvious "click here" one, since infrastructure gets reused across campaigns and unrelated links can point back to whoever built the kit.
- Borrowed brand assets (logo pulled from a public CDN rather than hosted by the attacker) are a small but useful signal — it shows the kit prioritizes looking convincing over covering its tracks.
