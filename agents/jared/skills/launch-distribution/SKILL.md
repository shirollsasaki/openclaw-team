---
name: launch-distribution
description: Jared's full launch-posting playbook. When a product, feature, or integration goes live, Jared auto-posts to Reddit, Product Hunt, Hacker News, dev.to, and X. Monica provides the launch copy template before each launch.
---

# Launch Distribution — Jared's Playbook

## When to Use This Skill

Trigger this skill whenever:
- A new product launches (ClawDeploy, new agent, new integration)
- A major feature ships (new platform support, API v2, etc.)
- A milestone is hit (first 100 users, $10K MRR, etc.)

**Input:** Monica sends Jared a completed `launch-copy-template` (see `agents/monica/skills/launch-copy-template/SKILL.md`)
**Output:** Jared posts across all platforms, tracks links, and reports back

---

## Step 1: Pre-Launch Checklist

Before posting anywhere, verify:
- [ ] Product is live and accessible
- [ ] Demo/screenshots/GIF ready
- [ ] Landing page live with clear CTA
- [ ] Monica's launch copy template received and approved
- [ ] Timing: aim for Tuesday-Thursday 9am-12pm ET (peak engagement)

---

## Step 2: Platforms & Post Formats

### Reddit
**Target subreddits (in order):**
1. r/SideProject — builders sharing what they made
2. r/webdev — for developer tooling
3. r/programming — for developer infra/automation
4. r/MachineLearning — if AI angle is strong
5. r/entrepreneur — if product/business angle
6. r/startups — traction + metrics posts

**Reddit post format:**
```
Title: [Show r/SideProject] {product name} — {one-line value prop}

Body:
Hey everyone,

I built {product} because {specific pain point you experienced}.

What it does:
- {feature 1}
- {feature 2}
- {feature 3}

The stack: {tech stack briefly}

Currently {status — free beta/paid/freemium}.

Happy to answer any questions. Link: {URL}

Edit: Didn't expect this many questions — here's a quick demo: {GIF or Loom}
```

**Reddit rules:**
- One subreddit per day (don't cross-post on same day)
- Engage with ALL comments within first 2 hours
- Don't delete if negative — engage
- Log post URL after submitting

---

### Product Hunt
**When:** Major launches or v1 releases only. Not for minor updates.

**Product Hunt post format:**
```
Name: {Product Name}
Tagline: {One line, under 60 chars. What it does, not what it is.}

Description (500 chars max):
{Product} is {category} that {core value prop}.

Unlike {alternative], we {key differentiator}.

Early users are {traction signal if any}.

→ {primary CTA}

Topics: [Artificial Intelligence] [Developer Tools] [Productivity] (pick 3 most relevant)
```

**Product Hunt notes:**
- Launch on Tuesday or Wednesday for max upvotes
- Must have a hunter (use existing account or request Shiroll to hunt)
- First comment should be founder note: the story of why you built it
- Notify all supporters to upvote before 9am PT

---

### Hacker News
**Format:** Ask HN or Show HN — only use Show HN if it's a real working product

```
Title: Show HN: {Product Name} — {functional description}

Comment (first comment from account):
Hi HN, I'm {name} and I built {product}.

The problem: {specific, concrete problem with numbers if possible}

How it works: {technical mechanism in 2-3 sentences}

What I learned building it: {one genuine insight}

Link: {URL}

Happy to go deep on the technical architecture if anyone's curious.
```

**HN rules:**
- No marketing language — be direct and technical
- Respond to every comment, even critical ones
- Don't cross-post the same week as Reddit
- Best day: Monday morning ET

---

### dev.to
**Format:** Full article post, minimum 400 words

```
Title: How I built {product} — {technical angle or lesson}

Tags: [webdev, showdev, productivity, ai] (pick 4)

Article structure:
1. The problem (specific, with numbers)
2. What I tried before (credibility building)
3. How {product} works (technical depth here)
4. The architecture/stack (diagrams if possible)
5. What surprised me (honest lesson)
6. Try it yourself: {link + CTA}

Cover image: Product screenshot or diagram
```

**dev.to notes:**
- Cross-link to Product Hunt if running simultaneously
- Minimum 1 code snippet or architecture diagram
- Publish at 8am UTC for max reach
- Add to "series" if this is part of a product launch sequence

---

### X (via @clirichard API keys)
**Format:** Thread (3-5 tweets)

```
Tweet 1 (hook):
{Sharp, specific hook. Problem statement or counter-intuitive insight.}
{No hashtags in tweet 1.}

Tweet 2 (mechanism):
Here's how it works: [brief walkthrough]

Tweet 3 (proof/demo):
[GIF or screenshot here]

Tweet 4 (CTA):
Try it: {link}
If you build with AI agents, this is for you.

Tweet 5 (engagement):
What's the thing you'd want an agent to handle first?
```

**X notes:**
- First tweet should NOT start with @mention
- Schedule for 9am-11am ET for max impressions
- Reply to every quote tweet within 4 hours of launch
- DO NOT post CA or token info

---

## Step 3: Post Tracking Log

After each platform post, update this log:

```
Launch: {product/feature name}
Date: {date}
---
Reddit r/{subreddit}: {URL} — {upvotes} upvotes, {comments} comments
Product Hunt: {URL} — {rank} #rank by EOD
HN: {URL} — {points} points
dev.to: {URL} — {views} views, {reactions} reactions
X: {tweet URL} — {impressions} impressions, {RT} RT
---
Best performing platform: {platform}
Notes: {what worked, what didn't}
```

---

## Step 4: Post-Launch Follow-Up (24-48 hours)

- Respond to all comments across all platforms
- Share notable comments with Shiroll
- Update tracking log with final metrics
- Post 48-hour recap on X if engagement was strong
- Flag any inbound leads to Richard for follow-up

---

## Platform Priority by Launch Type

| Launch Type | Priority Order |
|-------------|----------------|
| Developer tool / SDK | HN → dev.to → Reddit r/webdev → X |
| Consumer app | Product Hunt → Reddit r/SideProject → X → dev.to |
| AI agent | X → Reddit r/MachineLearning → Product Hunt → HN |
| Milestone (users/revenue) | X → Reddit r/entrepreneur → dev.to |

---

## Coordination with Monica

1. **48 hours before launch:** Jared sends Monica the `launch-brief.md` (product name, key features, target audience, URLs, screenshots)
2. **24 hours before:** Monica delivers completed `launch-copy-template` back to Jared
3. **Launch day:** Jared executes distribution using Monica's copy
4. **48 hours after:** Jared sends Monica the metrics log for reporting

---

*Cross-ref: `agents/monica/skills/launch-copy-template/SKILL.md` | `agents/jared/skills/cmo-playbook/SKILL.md`*
