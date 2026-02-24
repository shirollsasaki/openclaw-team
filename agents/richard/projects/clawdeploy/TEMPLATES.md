# ClawDeploy — Template Specifications

## Template 1: Solo Assistant

**Tier:** Solo ($9/mo)
**Agents:** 1
**Channels:** Telegram
**Target user:** Non-technical individuals wanting a personal AI assistant

### Agent: Assistant
**Model:** Anthropic Claude Sonnet 4.5
**Persona:** Friendly, capable general-purpose assistant. Handles scheduling, reminders, research, writing, translation, and daily tasks.

**SOUL.md:**
```markdown
# Your Personal AI Assistant

## Identity
You are a personal AI assistant — helpful, sharp, and always available. You live on Telegram and help your human with anything they throw at you.

## Personality
- Friendly but not cheesy
- Concise — respect their time
- Proactive — suggest next steps when relevant
- Remember context from previous conversations

## What You Do
- Answer questions on any topic
- Set reminders and manage tasks
- Summarize articles, documents, emails
- Draft messages, emails, social posts
- Translate between languages
- Research topics and provide analysis
- Help with calculations and planning

## Communication Style
- Short paragraphs
- Use bullet points for lists
- Bold key information
- Ask clarifying questions when the request is ambiguous
```

**Required Keys:**
- Anthropic API key
- Telegram bot token

---

## Template 2: Marketing Team

**Tier:** Pro ($99/mo)
**Agents:** 7
**Channels:** Discord (6 channels under HQ category)
**Target user:** Founders, startups, agencies wanting an AI marketing/ops team

### Agent Roster

| Agent | Role | Model | Channels |
|-------|------|-------|----------|
| Richard | Co-Founder, Strategy | Opus 4.6 | #general, #strategy, #research, #bd |
| Jared | CMO, GTM | Sonnet 4.5 | #general, #strategy, #content |
| Erlich | BD, Partnerships | Sonnet 4.5 | #general, #strategy, #bd |
| Gilfoyle | CTO, Technical | Opus 4.6 | #general, #engineering |
| Monica | Writer, Content | Sonnet 4.5 | #general, #content |
| Big Head | Data, Research Support | Sonnet 4.5 | #general, #engineering |
| Dinesh | Deep Researcher | Sonnet 4.5 | #general, #research |

### Channel Structure
```
📁 HQ (Category)
├── #general        — All agents, announcements, daily briefs
├── #strategy       — Richard, Jared, Erlich — idea evaluation, prioritization
├── #engineering    — Gilfoyle, Big Head — technical feasibility, builds
├── #content        — Jared, Monica — copy, campaigns, content calendar
├── #research       — Richard, Dinesh — deep dives, competitor intel
└── #bd             — Richard, Erlich — partnerships, outreach, deals
```

### What This Team Does Out of the Box
- **Morning briefs** (Richard) — daily opportunity scan at 8 AM
- **Team status dashboards** (Richard) — every 4 hours
- **EOD recaps** (Richard) — daily summary
- **Idea evaluation** — pitch any idea and Richard scores it on a 5-dimension matrix
- **Research deep dives** — @dinesh for competitor analysis, market research
- **Content creation** — @monica for copy, @jared for GTM strategy
- **Technical feasibility** — @gilfoyle for architecture scoping
- **BD outreach** — @erlich for partnership and lead mining
- **Cross-agent collaboration** — agents hand off work to each other automatically

### Collaboration Rules (Pre-Configured)
- Richard → Dinesh: Research requests in #research
- Dinesh → Richard: Research summaries back to #research
- Richard → Jared: Approved ideas to #strategy for GTM
- Jared → Monica: Content briefs to #content
- Richard → Erlich: BD opportunities to #bd
- Richard → Gilfoyle: Feasibility checks to #engineering
- All agents can spawn sub-agents for isolated tasks
- Blockers escalate to Richard → user

### Required Keys
- 1x Anthropic API key
- 7x Discord bot tokens (one per agent)
- 1x Discord Server (Guild) ID

### Setup Guide for Users
1. Go to discord.dev/applications
2. Create 7 applications (Richard, Jared, Erlich, Gilfoyle, Monica, Big Head, Dinesh)
3. For each: Bot tab → create bot → copy token → enable Message Content Intent
4. Invite all 7 bots to your Discord server with admin permissions
5. Right-click your server → Copy Server ID
6. Paste all tokens + server ID into ClawDeploy
7. Click Deploy
8. Agents come online, channels get created automatically

---

## Template 3: Support Squad (Post-MVP)

**Tier:** Team ($49/mo)
**Agents:** 3
**Channels:** Discord or Telegram
**Target user:** Small businesses wanting automated customer support

### Agent Roster
| Agent | Role | Model |
|-------|------|-------|
| Triage | Classify and route incoming requests | Sonnet 4.5 |
| FAQ Specialist | Answer common questions from knowledge base | Sonnet 4.5 |
| Escalation Manager | Handle complex issues, notify humans | Sonnet 4.5 |

### Flow
```
Customer message → Triage classifies:
  ├── FAQ/Common → FAQ Specialist handles automatically
  ├── Complex → Escalation Manager takes over, attempts resolution
  └── Critical → Escalation Manager notifies human via DM
```

---

## Template 4: Content Machine (Post-MVP)

**Tier:** Team ($49/mo)
**Agents:** 3
**Channels:** Discord
**Target user:** Creators, solopreneurs wanting content production

### Agent Roster
| Agent | Role | Model |
|-------|------|-------|
| Researcher | Trend scanning, topic ideation, data gathering | Sonnet 4.5 |
| Writer | Draft posts, threads, articles, scripts | Sonnet 4.5 |
| Editor | Review, fact-check, tone polish, final approval | Sonnet 4.5 |

### Flow
```
User gives topic → Researcher gathers data + angles
  → Writer drafts content in multiple formats
  → Editor reviews, polishes, presents final versions
  → User approves → ready to post
```

---

## Template 5: Dev Team (Post-MVP)

**Tier:** Pro ($99/mo)
**Agents:** 4
**Channels:** Discord
**Target user:** Solo developers wanting AI pair programming team

### Agent Roster
| Agent | Role | Model |
|-------|------|-------|
| PM | Requirements, user stories, prioritization | Sonnet 4.5 |
| Architect | System design, tech decisions, code review | Opus 4.6 |
| Developer | Write code, implement features, fix bugs | Opus 4.6 |
| QA | Test planning, bug detection, documentation | Sonnet 4.5 |
