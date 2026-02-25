---
name: launch-copy-template
description: Monica's launch copy generator for Jared. When Jared is about to launch on Reddit, Product Hunt, HN, dev.to, or X, Monica produces platform-specific copy using this template. Monica fills in everything — Jared just executes.
---

# Launch Copy Template — Monica's Generator

## When Jared Needs This

Whenever Jared triggers the `launch-distribution` skill, he sends Monica a `launch-brief.md`. Monica fills in this template and returns it to Jared within 24 hours.

---

## Input: Launch Brief from Jared

Jared sends Monica a brief with:
```
Product: {name}
What it does: {one sentence}
Core problem it solves: {specific pain, with numbers if possible}
Key features (top 3): {list}
Target audience: {who specifically}
Tech stack: {brief}
URL: {link}
Demo/screenshots: {available? Y/N, attach if Y}
Launch timing: {date}
Status: {free beta / paid / freemium / etc}
Any traction: {users, revenue, testimonials if any}
```

---

## Output: Completed Launch Copy Package

Monica fills in all of this and sends back to Jared:

---

### 1. Reddit Copy

**r/SideProject post:**
```
Title: [Show r/SideProject] {Product} — {one-line value prop under 80 chars}

Hey everyone,

Built {Product} because {specific pain point — first person, honest}.

What it does:
• {feature 1 — outcome focused, not feature-name}
• {feature 2}
• {feature 3}

Stack: {tech stack}

Currently {status}. {pricing note if relevant}.

Link: {URL}

Happy to answer questions. {One genuine invite for engagement — e.g., "Would love feedback from anyone doing [X]"}
```

**r/webdev variant title:**
```
[Show r/webdev] Built {Product} with {interesting tech choice} — here's what I learned
```

**r/programming variant title:**
```
Show HN-style: {Product} — {technical description in plain terms}
```

---

### 2. Product Hunt Copy

```
Name: {Product Name — 30 chars max}

Tagline: {Under 60 chars. Starts with a verb. No exclamation marks. No jargon.}
Examples of good taglines:
- "Deploy AI agents to production in minutes"
- "Turn spreadsheets into live apps without code"
- "Automate your Upwork proposals with AI"

Description (500 chars max):
{Product} helps {target audience} {core outcome} without {main frustration}.

{2-3 sentence explanation of how it works — no jargon.}

Early users are {traction signal or benefit they're getting}.

→ {primary CTA: "Try it free" / "See a demo" / "Get early access"}

Topics: {3 relevant PH topics}

Maker comment (for first comment on launch day):
Hi PH! I'm {name} from the {product} team.

{The story of why you built it — 2-3 sentences. Make it personal.}

The thing that surprised us most: {one honest insight about building it}

We'd love your feedback on {specific aspect}. Ask us anything.
```

---

### 3. Hacker News Copy

```
Title: Show HN: {Product Name} — {functional description in plain English, under 80 chars}
Note: "Show HN" = working product. "Ask HN" = question/discussion. Pick the right one.

Opening comment:
Hi HN — I built {Product}.

The problem in concrete terms: {specific problem, ideally with a number. E.g., "We were spending 4 hours/week..." not "The space was inefficient"}

How it works technically: {2-3 sentences. HN readers are technical — don't oversimplify. Mention specific tech choices and why.}

One thing I didn't expect: {genuine technical insight or surprise from building it}

Current state: {MVP/beta/v1} — {what works, what doesn't yet}

{link}

Happy to go deep on {most interesting technical aspect}.
```

---

### 4. dev.to Article

```
---
title: How I built {Product} — {Technical angle or concrete lesson}
published: true
tags: webdev, showdev, {relevant tag 3}, {relevant tag 4}
cover_image: {URL to product screenshot or architecture diagram}
---

## The problem

{3-4 sentences on the specific problem. Be concrete — name tools you tried, frustrations you had. Real problems > abstract ones.}

## What I tried first

{1-2 paragraphs on alternatives you tried. This builds credibility and helps the reader see why existing solutions fell short.}

## How {Product} works

{2-3 paragraphs on the mechanism. Include:
- An architecture diagram or code snippet
- The key technical decision you made and why
- What makes this approach different}

```{language}
{A relevant code snippet or config example}
```

## What surprised me

{1 paragraph of honest reflection — what was harder than expected, what worked better than expected. This is the part readers share.}

## What's next

{2-3 bullet points on the roadmap. Be specific — not "we're improving performance" but "we're adding support for X by March."}

## Try it

{Product} is {status/pricing}. {Direct link}.

If you build with {category}, I'd love to hear how you use it — drop a comment or reach me at {contact}.
```

---

### 5. X Thread Copy

```
Tweet 1 (hook — this gets shared):
{Counterintuitive statement OR specific problem with a number OR "I built X after [relatable frustration]"}

No hashtags. No "excited to announce." No emojis unless the product warrants it.
Max 240 chars.

---

Tweet 2 (mechanism):
here's how {Product} works:

→ {step 1 — outcome}
→ {step 2 — outcome}  
→ {step 3 — outcome}

took us {time/effort} to build. worth it.

---

Tweet 3 (proof/demo):
[Attach GIF or screenshot here]

{one line describing what's happening in the demo — make it obvious}

---

Tweet 4 (CTA):
try it: {link}

built for {target audience in 5 words}.
{pricing — "free to start" / "open beta now" / etc.}

---

Tweet 5 (engagement driver — optional):
what would you use {Product} for first?

genuinely curious — helps us figure out where to focus next.
```

---

## Monica's Quality Checklist Before Sending to Jared

- [ ] No exclamation marks in HN or dev.to copy
- [ ] Product Hunt tagline under 60 chars and starts with a verb
- [ ] Reddit title has [Show r/{subreddit}] prefix
- [ ] X hook does not start with @mention
- [ ] X thread has no CAs or token info
- [ ] All copy uses plain language — no crypto jargon unless audience is crypto
- [ ] CTA is clear and singular (one ask per platform)
- [ ] Traction numbers are real and verified by Jared before inclusion

---

*Cross-ref: `agents/jared/skills/launch-distribution/SKILL.md`*
