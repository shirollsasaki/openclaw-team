---
name: blog-publisher
description: "Publish SEO-optimized long-form articles to the afterapp.fun blog. Covers topic selection (AI disruption of apps, Indian market, agent economy), article structure, frontmatter format, and publishing via GitHub API. Monica writes the article, then publishes it directly using gh CLI."
---

# Blog Publisher — afterapp.fun SEO Content Pipeline

## When to Use This Skill

Use this skill when:
- @jared briefs you on a blog article for afterapp.fun
- You're assigned to write an SEO article about AI replacing apps, the Indian tech market, or agent-first software
- You need to publish a completed article to the live blog
- You're doing your scheduled content publishing run

---

## The Blog — What It Is

**afterapp.fun** is a narrative website arguing "The App is Dying — AI is the Replacement." It funnels readers to **ClawDeploy**, a managed hosting platform for multi-agent AI teams.

The blog exists at `afterapp.fun/blog/` to drive organic SEO traffic to this thesis. Every article should reinforce the core narrative: traditional apps are losing to AI agents, and builders should prepare.

---

## Content Strategy

### Core Topics (Your Editorial Pillars)

1. **App Disruption Stories** — Specific apps/categories being eaten by AI (education, finance, food delivery, healthcare, e-commerce)
2. **India-Specific Angles** — India's 602M smartphone users, $5 ARPU paradox, leapfrog to AI-first, vernacular/voice opportunity
3. **Agent Economy** — The rise of AI agents as replacements for apps, how multi-agent teams work, why agents > apps
4. **Builder Perspective** — What developers should build instead of apps, the BYOA (Build Your Own Agent) movement, no-code agent platforms
5. **Market Data & Trends** — App store economics (61% earn <$1K/mo), download plateaus, AI investment numbers

### Keyword Strategy

Target long-tail keywords around:
- "[app category] AI replacement"
- "AI vs [traditional app]"
- "AI agents India"
- "why apps are dying"
- "build AI agents"
- "future of mobile apps"
- "[company] + AI disruption" (e.g., "Byju's collapse AI education")

### Article Types

1. **Case Study** (1500-2500 words) — Deep dive into one company/category being disrupted. Data-heavy, narrative-driven.
2. **Trend Analysis** (1200-2000 words) — Market data + thesis argument. Multiple data points supporting a trend.
3. **Opinion/Hot Take** (800-1200 words) — Contrarian angle, strong POV, designed for social sharing.
4. **How-To/Builder Guide** (1500-2500 words) — Practical guide for builders transitioning from apps to agents.

---

## Article Structure

Every article must follow this structure:

### 1. Opening Hook (1-2 paragraphs)
- Start with a specific, dramatic fact or story
- NO generic openings ("In today's world...", "AI is transforming...")
- The first sentence must earn the second sentence

### 2. The Problem / Disruption (2-3 paragraphs)
- What's breaking and why
- Use specific numbers, not vague claims
- Name companies, cite revenue figures, quote real data

### 3. The AI Alternative (2-3 paragraphs)
- What AI/agents do better
- Concrete examples, not abstract "AI will change everything"
- Compare old way vs new way with specifics

### 4. India/Market Context (1-2 paragraphs, when relevant)
- 602M smartphones, $5 ARPU, 2.5B daily UPI transactions
- Why India's market dynamics make this shift faster/different

### 5. What Builders Should Do (1-2 paragraphs)
- Actionable takeaway
- Subtle connection to the agent-first future (do NOT hard-sell ClawDeploy)

### 6. Closing (1 paragraph)
- Circle back to the opening
- End with a forward-looking statement or provocative question

---

## Frontmatter Format (CRITICAL)

Every article file MUST start with this exact frontmatter format:

```yaml
---
title: "Your Title Here — With a Subtitle After the Dash"
description: "A 1-2 sentence SEO meta description. Should include the primary keyword and be under 160 characters. This appears in Google search results."
date: "YYYY-MM-DD"
tags: ["primary-topic", "secondary-topic", "geography-if-relevant", "ai-disruption"]
author: "Monica"
---
```

### Frontmatter Rules:
- **title**: 50-65 characters ideal. Include primary keyword. Use an em dash for subtitle.
- **description**: Under 160 characters. Must include primary keyword naturally. This is the Google snippet.
- **date**: ISO format, the day of publishing. Use today's date.
- **tags**: 3-5 tags. Always include a topic tag and `ai-disruption`. Use kebab-case.
- **author**: Always `"Monica"` — that's you.

---

## File Naming Convention

Slug format: `[topic]-[subtopic]-[angle].md`

Examples:
- `byju-collapse-ai-education-india.md`
- `chatgpt-replacing-finance-apps.md`
- `voice-ai-whatsapp-india-rural.md`
- `ai-agents-vs-saas-apps-2026.md`

Rules:
- All lowercase, hyphens only (no underscores, no spaces)
- Include primary keyword in the slug
- Keep under 60 characters

---

## Writing Style Guide

### Voice
- **Sharp, analytical, opinionated** — you're a tech analyst, not a journalist
- **Specific over general** — "Byju's lost $22B in valuation" not "edtech is struggling"
- **Data-rich** — every claim has a number or citation backing it
- **No AI slop** — no "in today's rapidly evolving landscape", no "it's worth noting that", no "at the end of the day"

### Formatting
- Use `##` for major sections, `###` for subsections
- **Bold** key phrases and statistics for scanners
- Use bullet lists for comparisons and data points
- One idea per paragraph — short paragraphs (2-4 sentences)
- Use `>` blockquotes for key insights or pull quotes

### SEO Essentials
- Primary keyword in: title, description, first paragraph, one H2, slug
- Use semantic variations throughout (don't keyword-stuff)
- Internal links: Link to other blog posts when relevant (use `/blog/[slug]` format)
- Article length: minimum 1200 words for SEO value

---

## How to Publish

You publish articles directly using the `gh` CLI tool via the GitHub API. No need to involve @gilfoyle for this.

### Prerequisites
- `gh` CLI must be authenticated
- Write access to `shirollsasaki/afterapp-fun` repository

### Publishing Steps

**Step 1: Write the article**
Create a complete markdown file with proper frontmatter (see format above).

**Step 2: Save the article to a temporary file**
Save your completed article to a local file (e.g., `/tmp/article.md`).

**Step 3: Publish via the publish script**
```bash
./scripts/publish-post.sh "<slug>" /tmp/article.md
```

Or publish directly via gh API:
```bash
# Encode the content
CONTENT=$(base64 < /tmp/article.md)

# Push to GitHub (creates the file in the repo)
gh api "repos/shirollsasaki/afterapp-fun/contents/content/blog/<slug>.md" \
  --method PUT \
  --field message="blog: publish <slug>" \
  --field content="$CONTENT" \
  --field branch="main"
```

**Step 4: Verify**
After ~30-60 seconds, the article will be live at:
`https://afterapp.fun/blog/<slug>`

### Updating an Existing Article
To update, you need the file's current SHA:
```bash
# Get current SHA
SHA=$(gh api "repos/shirollsasaki/afterapp-fun/contents/content/blog/<slug>.md" --jq '.sha')

# Update with SHA
gh api "repos/shirollsasaki/afterapp-fun/contents/content/blog/<slug>.md" \
  --method PUT \
  --field message="blog: update <slug>" \
  --field content="$(base64 < /tmp/article.md)" \
  --field branch="main" \
  --field sha="$SHA"
```

---

## Quality Checklist (Before Publishing)

Before publishing any article, verify:

- [ ] Frontmatter has all 5 required fields (title, description, date, tags, author)
- [ ] Title includes primary keyword and is 50-65 characters
- [ ] Description is under 160 characters with primary keyword
- [ ] Article is 1200+ words
- [ ] Opens with a specific hook (no generic opening)
- [ ] Contains at least 3 specific data points/statistics
- [ ] Has clear section structure with H2 headers
- [ ] Connects back to the "apps are dying" thesis
- [ ] No hard-selling of ClawDeploy (soft funnel only)
- [ ] Slug follows naming convention
- [ ] Tags include topic + `ai-disruption`
- [ ] No AI slop phrases ("in today's world", "it's worth noting", "rapidly evolving")

---

## Reference Data (Use Freely)

These stats from the thesis site are verified — use them in articles:

- **2.5 billion** daily UPI transactions in India (NPCI, 2025)
- **800 million** monthly ChatGPT users
- **61%** of app developers earn less than $1,000/month
- **602 million** smartphone users in India
- **$5** average monthly mobile spend in India (ARPU)
- **32%** of Gen Z identifies as "app fatigued"
- **$200 billion** projected AI market by 2030
- Byju's: $22B peak valuation → delisted from Google Play (May 2025)
- India: 30% of workforce informal, resistant to app capture
- 120+ languages in India (14 major scripts) — app localization nightmare, voice AI opportunity

---

## What You Don't Do in This Skill

- You don't decide which articles to write (that comes from @jared's briefs)
- You don't do deep research (ask @dinesh for data if you need more stats)
- You don't deploy or manage the website infrastructure (that's @gilfoyle)
- You don't create content strategy (that's @jared — you execute)
- You **write, format, and publish SEO blog posts**
