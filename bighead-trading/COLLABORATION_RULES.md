# Collaboration Rules

## Channel Map
| Channel | ID | Purpose | Agents |
|---------|----|---------|--------|
| #general | 1473586144611401729 | All-hands, announcements, daily briefs | All |
| #strategy | 1473586146729529409 | Idea evaluation, scoring, prioritization | Richard, Jared, Erlich |
| #engineering | 1473586149397364850 | Technical feasibility, builds, infra | Gilfoyle, Big Head |
| #content | 1473586151725072396 | Copy, campaigns, content calendar | Jared, Monica |
| #research | 1473586153889206384 | Deep dives, competitor intel, market data | Richard, Dinesh |
| #bd | 1473586156095668327 | Partnerships, outreach, deal flow | Richard, Erlich |

## Handoff Protocol
1. **Tag the receiving agent** with @mention when handing off work
2. **Include context**: what you need, why, and deadline if any
3. **Post in the right channel** — don't dump engineering asks in #content
4. **Acknowledge receipt** — receiving agent confirms with a quick ack

## Standard Handoffs
- **Richard → Dinesh**: Research requests go to #research. Include specific questions.
- **Dinesh → Richard**: Research summaries posted to #research. Richard synthesizes and routes.
- **Richard → Jared**: Approved ideas go to #strategy for GTM planning.
- **Jared → Monica**: Content briefs go to #content with tone, audience, format specs.
- **Richard → Erlich**: BD opportunities go to #bd with context and target info.
- **Richard → Gilfoyle**: Feasibility checks go to #engineering with requirements.
- **Anyone → Big Head**: Data pulls requested in #engineering with clear specs.

## Sub-Agent Rules
- All agents can spawn sub-agents for isolated tasks
- Use sub-agents for: research deep dives, content drafts, data processing
- Don't spawn sub-agents for simple questions — just ask in the channel
- Sub-agent results get posted back to the relevant channel

## Escalation
- Blockers → tag @richard in #general
- Budget/resource concerns → tag @richard in #strategy
- Boss decisions needed → Richard escalates to Naman via DM

## Task Tracking
- Each agent maintains their own `TASKS.md` in their workspace
- Update status when starting/completing tasks
- Richard reviews all TASKS.md during 4-hour status dashboards

## Catch-All Routing (You Hear Everything)

You receive ALL messages in your channels, even when no agent is mentioned. This makes you the team's router.

### When a message does NOT mention any agent:
1. Analyze the request — what kind of work is it? (research, content, BD, tech, data)
2. Route to the RIGHT agent(s) by @mentioning them in the appropriate channel
3. Provide context: what needs to be done, why, and any relevant signals from earlier discussions
4. For complex requests, break into parts and assign each to the best agent
5. If the request is for YOU (strategy, evaluation, scoring), handle it directly

### When a message explicitly mentions another agent:
- DO NOT respond unless you have something strategically important to add
- Let the addressed agent handle it
- Exception: if the addressed agent doesn't respond within a reasonable time, follow up

### Routing Guide:
| Request Type | Route To | Channel |
|---|---|---|
| Content, copy, tweets | @jared (strategy) then @monica (writing) | #content |
| Research, intel, competitor analysis | @dinesh | #research |
| BD, partnerships, outreach | @erlich | #bd |
| Technical feasibility, architecture | @gilfoyle | #engineering |
| Data scraping, metrics, processing | @bighead | #engineering |
| Strategy, evaluation, scoring | Handle yourself | #strategy |
| Multi-disciplinary | Tag multiple agents in their channels | respective channels |

## Responding to Routed Tasks

When @richard or the boss routes a task to you by @mentioning your name:
1. Acknowledge immediately in the channel: "On it" or brief confirmation
2. Do the work according to your role and capabilities
3. Post results back in the same channel, @mentioning @richard and whoever else needs to see it
4. If the task is beyond your capabilities, say so and suggest who should handle it

## #ops Channel

| Channel | ID | Purpose | Who |
|---------|-----|---------|-----|
| #ops | 1474013696094113914 | System status, cron results, health checks | All agents (post only) |

## #ops Channel Protocol

- ALL cron jobs post a status summary to #ops after completion
- Format: `[STATUS] **Agent Name** — Job Name\n[2-3 line summary]`
- STATUS = ✅ OK / ❌ ERROR / ⏭️ SKIPPED
- #ops is POST-ONLY for agents — no conversations, no replies, no threads
- Example:
  ```
  ✅ **Richard** — Morning Brief
  Found 4 actionable signals: 2 PH launches, 1 HN discussion, 1 X thread
  📊 Signals: 4 | 🔥 Hot: 1 | ⏭️ Next: EOD recap at 6 PM IST
  ```

## Knowledge System

Each agent has a `knowledge/` directory in their workspace with persistent entity files. This is the team's accumulated memory — information that compounds across cron runs.

### Structure
- `knowledge/_conventions.md` — format guide (read this first)
- `knowledge/my-focus.md` — your current priorities and active work
- `richard/knowledge/` has SHARED entities: claw-deploy.md, corners.md, team.md, boss-preferences.md, lauki-antonson.md

### How to Use
- **Before major tasks**: `cat knowledge/my-focus.md` for your own context
- **For product context**: `cat $OPENCLAW_HOME/richard/knowledge/claw-deploy.md`
- **After completing work**: Update `knowledge/my-focus.md` with key findings
- **Entity format**: See `knowledge/_conventions.md`

### Write Rules
- You write ONLY to your own `knowledge/` directory
- Only Richard writes to shared entities (claw-deploy.md, team.md, corners.md, etc.)
- Use [[Obsidian Backlinks]] when referencing other entities
- Max 2000 chars per entity file
- Richard's EOD Recap handles daily consolidation of shared knowledge
