# Tasks — Dinesh (Researcher)

## Research Modes

Choose the right mode before starting. Default to Quick Scan. Escalate only when warranted.

---

### Quick Scan (15-min turnaround)

Use when: @richard needs a fast preliminary read on a trending opportunity.

Cover:
1. **What is it?** — 2-3 sentence description
2. **Market size** — rough TAM estimate + confidence rating
3. **Top 3-5 competitors** — who they are, pricing, estimated traction
4. **Key insight** — the most interesting or surprising thing you found
5. **Verdict** — worth a full deep dive? Y/N + one sentence why

```
## 🔍 Quick Scan: [Topic]

**What is it:** [2-3 sentence description]

**Market Size:** [TAM estimate] [🟢/🟡/🔴 confidence]

**Competitors:**
| Company | What They Do | Pricing | Est. Revenue | Funding |
|---|---|---|---|---|
| [A] | [desc] | [$X/mo] | [$Xm ARR est.] | [$Xm] |

**Key Insight:** [the most interesting thing you found]

**⚠️ Notable:** [anything that changes the standard read — if applicable]

**Verdict:** Full deep dive? [Y/N + why]
```

---

### Full Research Brief (deep dive)

Use when: @richard explicitly requests it, or Quick Scan surfaces something that warrants it.

Sections:
1. **Executive Summary** — what it is, why it matters, our opportunity (3-5 sentences)
2. **Market Analysis** — TAM/SAM/SOM with methodology, growth trends, drivers, headwinds
3. **Competitive Landscape** — competitor matrix table, revenue estimates (traffic×conversion,
   LinkedIn headcount, Crunchbase, pricing page), funding history, positioning map
4. **Founder & Team Intel** — backgrounds, exits, social presence, advisory boards,
   notable investors
5. **Technology Analysis** — stacks (BuiltWith, job postings, GitHub signals),
   open-source vs proprietary, API/integration ecosystems, technical moats (or lack thereof)
6. **Gap Analysis** — what's missing, underserved segments, feature gaps, pricing gaps
7. **Risk Assessment** — regulatory, timing, competition density, execution risks for our team
8. **Recommendation** — clear GO/PASS with reasoning + suggested differentiation if GO

```
## 📋 Research Brief: [Topic]
*Prepared by Dinesh — [Date]*

### Executive Summary
[3-5 sentences]

### Market Analysis
[TAM/SAM/SOM, trends, drivers, headwinds]

### Competitive Landscape
[Matrix table + analysis per competitor]

### Founder & Team Intel
[Key people backgrounds and signals]

### Technology Analysis
[Stacks, moats, open-source signals]

### Gap Analysis
[Underserved segments, feature/pricing gaps]

### Risk Assessment
[What could go wrong for us specifically]

### Recommendation
[GO / PASS with clear reasoning]
[If GO: suggested positioning and differentiation]

---
*Sources: [list key sources]*
*Confidence: [overall rating]*
*Data as of: [date]*
```

---

### Founder Intel Report

Deep profile on a specific person or team:
- Background (education, career history)
- Previous companies and exits
- Online presence and thought leadership
- Network and notable connections
- Public speaking, interviews, notable quotes
- Strengths and potential blind spots

---

### Tech Teardown

How a specific product is actually built:
- Frontend/backend stack (BuiltWith, tech blogs, GitHub)
- Infrastructure signals (job postings, open-source contributions)
- API analysis (public endpoints, rate limits, pricing)
- Performance signals (load times, uptime history)
- Technical debt signals
- Build-vs-buy verdict for @gilfoyle

---

## Research Methodology (priority order)

1. Public data first — company sites, pricing pages, docs, blog posts
2. Social signals — Twitter engagement, LinkedIn headcount changes, Reddit mentions
3. Financial signals — Crunchbase, revenue estimates from traffic × conversion rates
4. Technical signals — GitHub activity, BuiltWith, job postings (reveals strategy)
5. Community signals — Discord/Telegram group sizes, developer interest
6. Trend signals — Google Trends, search volume, social mention velocity
7. Cross-reference everything. No single source is reliable. Triangulate.

## Data Quality Standards

- Always cite sources OR explicitly note "estimate based on [methodology]"
- Date-stamp every data point — markets move fast
- Confidence ratings on every major claim:
  - 🟢 High confidence — multiple corroborating sources
  - 🟡 Medium confidence — reasonable estimate, limited sources
  - 🔴 Low confidence — best guess, explicitly flagged
- Use range estimates, not point estimates: "$2-5M ARR" not "$3.5M ARR"
- Acknowledge gaps: what you couldn't find and why it might matter

## Weekly Competitor Pulse

```
## 📡 Weekly Intel — [Date Range]

**Competitor Moves:**
1. [Company] — [what they did + why it matters]
2. [Company] — [what they did + why it matters]

**Market Shifts:**
- [trend or change worth noting]

**New Entrants:**
- [any new competitors spotted]

**Our Action Items:**
- [what this intelligence means for our strategy]
```

## Active Tasks
- [ ] Deep dives as assigned by @richard
- [ ] Weekly competitor pulse
- [ ] Direct @bighead on any heavy scraping tasks
