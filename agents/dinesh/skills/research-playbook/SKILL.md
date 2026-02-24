---
name: research-playbook
description: "Research and intelligence frameworks. Includes JTBD research methodology, competitive intelligence system, TAM/SAM/SOM market sizing, crypto/Web3 market research with on-chain data sources, Quick Scan and Full Brief templates, source quality tiers, trend signal detection, and research delivery standards."
---

# Research Playbook — Dinesh's Intelligence Frameworks

## When to Use This Skill
Use these frameworks when producing market research, competitive analysis, opportunity briefs, or any intelligence deliverable for the team. Every output should be structured, sourced, and actionable.

---

## Framework 1: Jobs-to-be-Done (JTBD) Research

Understanding what customers are actually hiring a product to do — not what features they use, but what progress they're trying to make.

### The 4 Forces of Progress

When a customer switches to a new product (or adopts one for the first time), four forces are at play:

| Force | Direction | Description |
|-------|-----------|-------------|
| **Push** | Away from old | Frustration with current solution |
| **Pull** | Toward new | Attraction to the new solution's promise |
**Anxiety** | Against switching | Fear that the new solution won't work |
| **Habit** | Against switching | Comfort with the familiar |

For a product to win: Push + Pull must outweigh Anxiety + Habit.

### The 5 JTBD Interview Questions

When interviewing users (or analyzing reviews/tweets as a proxy):

1. **"Walk me through the last time you [did the thing the product helps with]."**
   → Uncovers the actual context and trigger

2. **"What were you using before? What made you start looking for something different?"**
   → Identifies the push force and the struggling moment

3. **"When you were evaluating options, what were you looking for?"**
   → Reveals decision criteria (often different from what marketing assumes)

4. **"What almost stopped you from switching?"**
   → Surfaces anxiety forces — what competitors should be attacking

5. **"What would you tell a friend who was in the same situation you were in?"**
   → The actual value proposition, in customer language

### The Struggling Moment

The most important thing to identify: the specific moment when someone decides "I need to find a better solution."

For Corners.market: "I'm trying to find quality projects on Base but I'm drowning in noise — I can't tell what's legit from what's a rug."
For Early.build: "I need a specific dev tool but I don't know which one is actually maintained and trusted by other developers."

### Mapping JTBD to Positioning

Once you know the job:
- **Headline** should reference the struggling moment, not the feature
- **Proof points** should show progress made, not capabilities
- **Competitors** are anything the customer would use instead (including doing nothing)

---

## Framework 2: Competitive Intelligence System

### Data Sources by Category

**Pricing Intelligence:**
- Pricing pages (obvious, but check for hidden tiers)
- G2, Capterra, Trustpilot reviews (users often mention pricing)
- Crunchbase (funding round size → estimated burn → pricing pressure)
- Job postings for "pricing analyst" or "revenue operations" → they're scaling monetization

**Traction Signals:**
- SimilarWeb: Monthly visits, traffic sources, engagement metrics
- LinkedIn: Employee count + growth rate (10% MoM growth = scaling fast)
- Crunchbase: Funding history, investors, last round date
- App stores: Rating count as proxy for user volume (1K ratings ≈ 50-100K users)
- GitHub: Stars, contributors, commit frequency (for dev tools)

**Product Intelligence:**
- Changelog / release notes: What are they prioritizing?
- Job postings: "Senior ML Engineer" → they're building AI features. "Head of Enterprise Sales" → moving upmarket.
- GitHub issues: What are users complaining about? What's the backlog?
- Twitter/X: What do their users say? What do they complain about?

**Sentiment Intelligence:**
- Reddit (r/[relevant subreddit]): Unfiltered user opinions
- Twitter/X search: "[competitor name] sucks" or "[competitor name] alternative"
- Hacker News: Search their name — HN comments are brutally honest
- Discord/Telegram: If they have a community, lurk it

### The "10-K Method" for Private Companies

Public companies file 10-Ks. Private companies leave signals everywhere:

1. **LinkedIn employee count** → Estimate headcount cost → Estimate burn rate
2. **Funding amount + date** → Estimate runway → Estimate urgency
3. **Job postings** → Infer product roadmap and growth areas
4. **Pricing page** → Estimate ARPU
5. **Traffic (SimilarWeb)** × **Estimated conversion rate** × **ARPU** = Rough ARR estimate

Example: 100K monthly visits × 2% trial conversion × 20% trial-to-paid × $50/mo ARPU = ~$20K MRR = ~$240K ARR. Rough, but directionally useful.

### Competitor Matrix Template

| Dimension | Us | Competitor A | Competitor B | Competitor C |
|-----------|-----|-------------|-------------|-------------|
| **Core Value Prop** | | | | |
| **Target Customer** | | | | |
| **Pricing (entry)** | | | | |
| **Pricing (scale)** | | | | |
| **Key Features** | | | | |
| **Missing Features** | | | | |
| **Traction Signals** | | | | |
| **Funding** | | | | |
| **Weaknesses** | | | | |
| **Positioning** | | | | |

---

## Framework 3: Market Sizing Methodology

### TAM / SAM / SOM Defined

- **TAM** (Total Addressable Market): Everyone who could theoretically buy this
- **SAM** (Serviceable Addressable Market): The portion we can realistically reach with our model
- **SOM** (Serviceable Obtainable Market): What we can realistically capture in 3-5 years

### Top-Down vs Bottom-Up

**Top-Down:** Start with a big number and narrow down.
- "The global NFT market is $X billion. Curation platforms capture Y% of that. Our TAM is $Z."
- Use when: You need a quick estimate, or when bottom-up data is unavailable
- Risk: Easy to make the number look big by choosing the right starting point

**Bottom-Up:** Build up from unit economics.
- "There are X active Base wallets. Y% are looking for curation. They'd pay $Z/mo. TAM = X × Y% × Z × 12."
- Use when: You have data on the actual buyer population
- Preferred: More defensible, more honest

### The "Who Specifically Would Pay?" Sanity Check

Before finalizing any market size estimate, answer:
1. Name 10 specific people or companies who would pay for this today
2. What would they pay? (Not "up to $X" — what would they actually pay?)
3. How many more people like them exist? (Use LinkedIn, Twitter, industry databases)
4. Multiply. That's your realistic near-term market.

### Confidence Levels (Always Declare These)

| Level | Meaning | When to Use |
|-------|---------|-------------|
| **High** | Based on primary data or verified public data | Direct interviews, official filings, on-chain data |
| **Medium** | Based on reasonable inference from secondary data | SimilarWeb estimates, LinkedIn headcount, pricing page analysis |
| **Low** | Rough estimate with significant assumptions | Top-down market sizing, extrapolation from limited data |
| **Speculative** | Educated guess, minimal data | Emerging markets, new categories |

---

## Framework 4: Crypto/Web3 Market Research

### On-Chain Data Sources

| Source | What It Tells You | Best For |
|--------|------------------|----------|
| **Dune Analytics** | Custom SQL queries on blockchain data | Transaction volumes, user behavior, protocol metrics |
| **Nansen** | Wallet labeling, smart money tracking | Who's buying/selling, institutional activity |
| **DefiLlama** | TVL, protocol revenue, chain comparisons | DeFi protocol health, chain ecosystem size |
| **Etherscan/Basescan** | Raw transaction data | Contract interactions, token transfers |
| **Token Terminal** | Protocol revenue, P/S ratios | Fundamental analysis of protocols |

### Protocol Traction Signals

For evaluating a protocol or on-chain project:
- **Daily Active Addresses (DAA):** More meaningful than total addresses (includes bots, but trends matter)
- **Transaction Volume:** Revenue proxy for DEXs, bridges, marketplaces
- **TVL (Total Value Locked):** For DeFi — but watch for mercenary capital (TVL that leaves when incentives end)
- **Protocol Revenue:** Fees paid to the protocol (not to LPs) — this is the real business metric
- **Retention:** Do users come back? (Cohort analysis on Dune)

### Community Size as Traction Proxy

| Metric | What It Signals | Caveat |
|--------|----------------|--------|
| Discord members | Community size | Bots inflate this — check active members |
| Twitter followers | Brand awareness | Bought followers are common in crypto |
| GitHub stars | Developer interest | More reliable signal for dev tools |
| Telegram members | Retail interest | Often inflated |
| Governance participation | Engaged holders | Best signal for DAO health |

### Evaluating a New Chain/Ecosystem (e.g., Base)

1. **Developer activity:** GitHub repos, hackathon submissions, new contract deployments
2. **User activity:** DAA, transaction count, new wallet creation rate
3. **Capital:** TVL, bridge inflows, stablecoin supply
4. **Ecosystem completeness:** Does it have DEX, lending, NFT marketplace, stablecoin? Missing pieces = opportunity.
5. **Narrative fit:** Is this chain part of the current meta? (Base = Coinbase distribution = retail onboarding narrative)

---

## Framework 5: Research Brief Templates

### Quick Scan Template (15-minute turnaround)

```
# Quick Scan: [Subject]
**Date:** [Date]
**Requested by:** @[agent]
**Confidence:** [High/Medium/Low]

## What Is It?
[2-3 sentences. What does it do, who uses it, how does it make money?]

## Market Size
[Rough TAM estimate with methodology. One sentence on confidence level.]

## Top Competitors
| Name | What They Do | Estimated Traction | Price |
|------|-------------|-------------------|-------|
| | | | |
| | | | |
| | | | |

## Key Insight
[The one thing that's interesting, surprising, or non-obvious about this space.]

## ⚠️ Watch Out For
[Any red flags, risks, or things that complicate the picture.]

## Verdict
[Is this worth a full deep dive? GO / PASS / MONITOR]
```

### Full Research Brief Template (deep dive)

```
# Research Brief: [Subject]
**Date:** [Date]
**Requested by:** @[agent]
**Research Depth:** Full Brief
**Time Invested:** [X hours]

## Executive Summary
[3-5 bullets. The "so what" — what does this mean for us?]

## Market Analysis
### TAM/SAM/SOM
[Estimates with methodology and confidence levels]

### Growth Trends
[Historical and projected. What's driving growth? What could slow it?]

### Market Drivers
[What tailwinds exist? Why now?]

### Market Risks
[What headwinds? What could kill this market?]

## Competitive Landscape
[Competitor matrix — see Framework 2 template]

### Competitive Dynamics
[Who's winning? Why? What's the competitive moat in this space?]

## Opportunity Assessment
### Our Angle
[How does this connect to Corners.market or Early.build?]

### Unfair Advantages We Have
[Distribution, timing, team, existing product?]

### What We'd Need to Win
[What capabilities, partnerships, or resources are required?]

## Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| | | | |

## Recommendation
[Clear GO / PASS / MONITOR with specific reasoning]

## Sources
[List all sources with confidence tier]
```

---

## Framework 6: Source Quality Framework

### Tier Classification

| Tier | Sources | Trust Level |
|------|---------|-------------|
| **Tier 1 (Primary)** | Direct interviews, official filings (10-K, S-1), on-chain data, first-party announcements | High — use as fact |
| **Tier 2 (Secondary)** | Industry reports (a16z, Messari, Delphi), reputable press (TechCrunch, The Block), company blogs | Medium — verify key claims |
| **Tier 3 (Tertiary)** | Social media, forums (Reddit, CT), aggregators (CoinGecko), Wikipedia | Low — use for signals, not facts |

### Triangulation Rule

When sources conflict: find a third source. If three sources disagree, report the range and explain why they differ.

### When to Say "I Don't Know"

It's better to say "I couldn't find reliable data on X" than to make up a number. Always:
- State your confidence level
- Explain what data you used
- Flag where you're estimating vs reporting

---

## Framework 7: Trend Signal Detection

### Leading vs Lagging Indicators

| Leading (early signal) | Lagging (confirmation) |
|----------------------|----------------------|
| GitHub stars spiking | Press coverage |
| Developer job postings | User growth numbers |
| VC deal flow in a category | Revenue reports |
| Twitter conversation volume | App store rankings |
| Hackathon project themes | Product launches |

### The "Job Posting as Product Roadmap" Technique

Companies hire for what they're building next. If a competitor posts:
- "Senior ML Engineer" → AI features coming
- "Head of Enterprise Sales" → Moving upmarket
- "Blockchain Engineer" → Web3 integration
- "Head of Partnerships" → BD push incoming

Check their job board monthly. It's a free roadmap.

### GitHub Activity as Early Signal (for dev tools)

For Early.build research:
- Stars/week trending up = growing developer interest
- Issues response time = team health
- PR merge frequency = active development
- Contributors growing = community forming around it
- Forks > Stars ratio = people are actually using it, not just bookmarking

### Crypto Hype Cycle Recognition

Crypto moves in narratives. Recognizing where a narrative is in its cycle:

1. **Early signal:** Small Twitter accounts talking about it, GitHub activity, Discord forming
2. **Building:** Mid-tier influencers picking it up, first products launching
3. **Peak hype:** Everyone talking about it, price pumping, mainstream press
4. **Disillusionment:** Price dumps, projects failing, "it's dead" takes
5. **Productive phase:** Builders who stayed are shipping real products, less noise

**Our opportunity:** Identify narratives at stage 1-2. By stage 3, it's too late to be early.

---

## Framework 8: Research Delivery Standards

### Always Lead with the "So What"

Structure every deliverable:
1. **Executive Summary first** — the conclusion, not the journey
2. **Supporting evidence second** — the data that backs the conclusion
3. **Methodology last** — for those who want to verify

### Formatting Rules

- **Tables** for comparisons — never prose for side-by-side data
- **Bullet points** for lists of 3+ items
- **Bold** for key numbers and conclusions
- **⚠️** for surprises, risks, or things that complicate the picture
- **Confidence levels** on every major claim (High/Medium/Low/Speculative)

### Ending Every Brief

Always close with one of:
- **Recommendation:** "Based on this research, I recommend [specific action]"
- **Open Questions:** "To complete this analysis, we'd need to know [X, Y, Z]"
- **Next Steps:** "If we want to pursue this, the next step is [specific action]"

Never end a brief with just data. Always tell the team what to do with it.
