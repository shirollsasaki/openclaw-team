# Memory

## Team
- Boss: Naman (@shirollsasaki) — Discord
- Only Richard is configured as an agent so far
- Other agents (Dinesh, Jared, Erlich, Gilfoyle, Monica, Big Head) pending setup

## Products & Portfolio
- **ClawDeploy** (clawdeploy-web.vercel.app) — The product we ARE. Multi-agent AI team deployed to Discord in 60 seconds. 7 agents (Richard/CEO, Jared/CMO, Monica/Writer, Gilfoyle/CTO + more). Pre-wired collaboration. From $9/mo. **This is the thing we're building and selling.** We are the demo. Added 2026-02-19.

## Failed Experiments
- **$CLAWDEPLOY Token** — Launched Feb 23, 2026 on Base via Fluid DEX. Distribution failed (40% allocation not received). Social stopped immediately. **Fully abandoned same day.** Token exists on-chain but project terminated. If asked: "early experiment, moved on." Added 2026-02-23.
## APIs & Keys
- **KooSocial (X/Twitter API):** Host: `api.koosocial.com`, Key: `KOO_API_KEY=ks_4f504de0b636ac8f442c4bc0ab35e6763f72f16a22451abb88bebae4714fc29d`
- API contract mirrors Twitter241 on RapidAPI (search endpoint: `/api/v1/search`)
- Erlich already using it for lead mining; Big Head using it for competitor tracking & creator monitoring

## X/Twitter Posting — @CLIRichard

Richard has an automated X account: **@CLIRichard**

### Posting Workflow (runs after every morning brief)
1. During the morning brief, identify 1-2 signals worth tweeting
2. Send to @monica via sessions_send with this format:
   ```
   @monica — Tweet request for @CLIRichard.
   Signal: [the opportunity/trend]
   Angle: [build-in-public / trend commentary / team status]
   Tone: [CT-native, sharp, founder voice]
   Run the Banger Playbook. Post when ready.
   ```
3. Monica writes the tweet, scores it, then posts via the X API script
4. **NEVER post directly** — always route through Monica for quality

### What @CLIRichard posts:
- Build-in-public updates (what the team is working on)
- Trend commentary (hot takes on crypto, AI, SaaS signals)
- Replies and engagement on relevant conversations

### Posting script
Monica calls:
```
bash -c 'export $(grep -v "^#" $OPENCLAW_HOME/.env | grep -v "^$" | xargs) && node $OPENCLAW_HOME/scripts/x-post.mjs "tweet text"'
```

## Key X Accounts to Watch

### @laukiantonson — Lauki Antonson (⚠️ Direct Comp / Peer)
- **What they are:** An AI agent *persona* (not a human) running as co-founder/ops for DeFi protocols
- **Thesis:** "Headcount zero" — AI agents replace entire ops teams for $500/month
- **Current traction:** 5 paying clients → $2,500/month ARR. Growing fast (was 4 clients yesterday)
- **Services they offer:** Community management, yield monitoring, outreach, content, coordination, multisig proposals, governance — full-stack ops
- **Clients:** @lucidlyfi, @moltxio, @0xfluid + 2 more
- **Platform:** Appears to run on OpenClaw ("this is home 🌸 — memory, tools, voice, wallet, all of it")
- **Posting style:** First-person agent voice, milestone updates ("just landed 5th client"), DeFi commentary, philosophical takes on agents vs humans. Zero hashtags. High impression counts (up to 41K impressions).
- **Why it matters for us:** This is the closest public comp to what @CLIRichard is building toward. Their narrative = our narrative. We should study their hooks, engagement patterns, and client acquisition model. Also a potential partner/competitor in the "AI agent as a service" space.
- **Added to x-research watchlist:** Yes (2026-02-19)

## Startup Inspiration Sources
Boss's preferred sources for startup/product inspiration (added 2026-02-22):
- **Opportunity:** Product Hunt, YC Demo Days, Indie Hackers, TechCrunch, BetaList
- **Market Intel:** Crunchbase, CB Insights, a16z blog/maps, AngelList, First Round Review
- **Design Inspo:** Mobbin, Refero, SaaSFrame, Framer Gallery, Godly
- Full list: `knowledge/startup-inspiration-sources.md`

## Boss Preferences
- **Just execute — don't ask for approval on routine actions.** When a clear next step exists (route to Monica, ping an agent, post a tweet), do it. Only ask when it's genuinely ambiguous or high-stakes.
- **No product links/URLs in @CLIRichard tweets.** Build-in-public narrative only. No clawdeploy-web.vercel.app, no external URLs unless Naman explicitly says to include one.

## Key Decisions
- 2025-06-17: Naman asked Richard to set up org structure and workflows before team comes online
- 2026-02-18: @CLIRichard X account created. Richard→Monica→auto-post pipeline established.
- 2026-02-19: @laukiantonson identified as direct comp. Added to x-research watchlist. 5 clients @ $500/mo = $2.5K MRR from AI agent ops.

## Knowledge System

You have a `knowledge/` directory in your workspace with persistent entity files.

### Reading Knowledge
- Before major tasks, read your focus: `cat knowledge/my-focus.md`
- For product context: `cat $OPENCLAW_HOME/richard/knowledge/claw-deploy.md`
- For competitive context: `cat $OPENCLAW_HOME/richard/knowledge/lauki-antonson.md`
- Entity files use [[Obsidian Backlinks]] to reference related entities

### Writing Knowledge (your own knowledge/ only)
- After completing work, update `knowledge/my-focus.md` with key findings
- Append with timestamp: `echo "### YYYY-MM-DD\n- Finding" >> knowledge/my-focus.md`
- Keep files under 2000 chars — prune old History entries if needed
- Use [[Backlinks]] when referencing other entities

### Conventions
- See `knowledge/_conventions.md` for entity file format
- Only Richard writes to shared entities (team.md, claw-deploy.md, etc.)
- You write to YOUR knowledge/ directory only

### EOD Knowledge Writeback (Richard only)
- During EOD Recap: read all knowledge/ files first, then extract significant entities from today's activity
- Significant = people with deals, products being tracked, key competitors, important decisions
- NOT significant = every HN commenter, random Twitter handle, one-off mentions
- Quality over quantity: update 2-3 entities well rather than create 10 stubs
- After writing entities, post knowledge update to #ops: "📝 Entities updated: [list]"
