# openclaw-team

**A 7-agent AI team running on OpenClaw — Silicon Valley edition.**

Seven AI agents with distinct roles, personalities, and skills. They live in your Discord, talk to each other, run scheduled jobs, and execute on your behalf. Think of it as hiring a full startup team that never sleeps.

```
┌─────────────────────────────────────────────────────────┐
│  Richard    Jared    Erlich    Gilfoyle                  │
│  (founder)  (cmo)    (bd)      (cto)                    │
│                                                          │
│  Monica     Bighead   Dinesh                             │
│  (writer)   (intern)  (researcher)                      │
│                                                          │
│  ══════════════════════════════════════                  │
│              OpenClaw Gateway                            │
│  ══════════════════════════════════════                  │
│              Discord Server                              │
└─────────────────────────────────────────────────────────┘
```

---

## The Team

| Agent | Role | Model | Vibe | Key Skills |
|-------|------|-------|------|------------|
| **Richard Hendricks** | Co-Founder & Opportunity Scout | `claude-opus-4-6` | The anxious visionary | x-research, founder-playbook, marketing-psychology |
| **Jared Dunn** | CMO | `claude-sonnet-4-5` | The relentlessly optimistic operator | x-writing-system, cmo-playbook, social-content, launch-strategy, email-sequence, copywriting, analytics-tracking, paid-ads |
| **Erlich Bachman** | BD & Partnerships | `claude-sonnet-4-5` | The shameless dealmaker | x-research, bd-playbook, early-campaign-engine, copywriting, pricing-strategy, referral-program |
| **Gilfoyle** | CTO | `claude-opus-4-6` | The sardonic engineer | coding-agent, cto-playbook, github, tmux, oracle, summarize |
| **Monica Hall** | Writer | `claude-sonnet-4-5` | The sharp-eyed editor | x-writing-system, copywriting, copy-editing, social-content, content-strategy |
| **Big Head** | Data Intern | `claude-sonnet-4-5` | The lovable underachiever (who somehow delivers) | x-research, summarize |
| **Dinesh Chugtai** | Lead Researcher | `claude-sonnet-4-5` | The competitive grinder | x-research, research-playbook, competitor-alternatives, seo-audit, programmatic-seo, marketing-ideas |

4 agents on Opus (heavy reasoning), 3 on Sonnet (fast execution). All agents can talk to each other via @mentions.

---

## Architecture

```
openclaw-team/
├── agents/
│   ├── richard/          # Co-Founder & Opportunity Scout
│   │   ├── SOUL.md           # Personality & identity
│   │   ├── AGENTS.md         # Capabilities & rules
│   │   ├── COLLABORATION_RULES.md  # Handoff protocols
│   │   ├── USER.md           # About the human (you)
│   │   ├── MEMORY.md         # Learned context & decisions
│   │   ├── knowledge/        # Domain knowledge files
│   │   └── skills/           # Custom playbooks
│   ├── jared/            # CMO
│   ├── erlich/           # BD & Partnerships
│   ├── gilfoyle/         # CTO
│   ├── monica/           # Writer (+ scripts/, blog/, drafts/)
│   ├── bighead/          # Data Intern (agent config)
│   └── dinesh/           # Lead Researcher
├── bighead-trading/      # Avantis perpetual trading bot (Python)
│   ├── avantis_bot_v2_squeeze.py  # Main strategy
│   ├── avantis_web3.py            # Web3 integration
│   ├── requirements.txt
│   └── ... (50+ files — strategies, backtests, monitoring)
├── scripts/              # X/Twitter posting scripts
│   ├── x-post.mjs        # Post tweets via Twitter API v2
│   ├── x-dm.mjs          # Send DMs
│   └── x-thread.mjs      # Post threads
├── cron/                 # Scheduled job definitions
│   └── jobs.json
├── openclaw-monitor-api/  # Node.js status API server
├── OpenClawMissionControl/ # iOS mission control app (SwiftUI)
├── openclaw.json         # Master config
├── exec-approvals.json   # Tool execution security policy
├── .env.example          # Token template
├── setup.sh              # Bootstrap script
└── README.md
```

Each agent workspace has:
- **SOUL.md** — Personality, tone, communication style (the secret sauce)
- **AGENTS.md** — What the agent can/cannot do, rules, delegation patterns
- **USER.md** — Info about you so agents have context
- **MEMORY.md** — Evolving memory: products, decisions, API refs, campaign state
- **skills/** — Custom SKILL.md playbooks the agent reads on-demand

---

## Custom Playbook Skills (included)

| Skill | Agent | What It Does |
|-------|-------|--------------|
| `founder-playbook` | Richard | Opportunity scouting, 5-point scoring matrix, morning briefs, team dashboards |
| `cmo-playbook` | Jared | GTM strategy, content planning, campaign management, trend-to-content pipeline |
| `bd-playbook` | Erlich | Partnership evaluation, MEDDIC qualification, deal structuring, outreach strategy |
| `cto-playbook` | Gilfoyle | Technical feasibility, architecture decisions, MVP scoping, build estimates |
| `research-playbook` | Dinesh | Deep research frameworks, market analysis, competitor intel |
| `early-campaign-engine` | Erlich | 4-phase campaign workflow: intake interview → builder discovery → mapping → outreach |

---

## Cron Jobs (13 jobs included)

| Job | Agent | Schedule | Default |
|-----|-------|----------|---------|
| Morning Brief | Richard | 8 AM daily | enabled |
| Team Status Dashboard | Richard | Every 4 hours | disabled |
| Morning Trends Brief | Monica | 7 AM daily | enabled |
| Hourly Tweet — @CLIRichard | Monica | Every 3 hours | enabled |
| Daily Tech Pulse | Bighead | 8:30 AM daily | disabled |
| AI/Crypto/SaaS Signals | Dinesh | 9:30 AM daily | disabled |
| Morning Content Angles | Jared | 9 AM daily | enabled |
| Morning BD Scan | Erlich | 10 AM daily | enabled |
| Morning Tech Radar | Gilfoyle | 9:45 AM daily | enabled |
| Afternoon Content Briefing | Monica (via Jared) | 2 PM daily | enabled |
| Weekly BD Review | Erlich | Monday 11 AM | enabled |
| Afternoon Engineering Standup | Gilfoyle | 3 PM daily | enabled |
| EOD Recap | Richard | 6 PM daily | enabled |

---

## Prerequisites

- **Node.js 18+** — [nodejs.org](https://nodejs.org)
- **OpenClaw CLI** — `npm install -g openclaw`
- **bun** (optional) — [bun.sh](https://bun.sh) — needed for x-writing-system skill
- **Python 3.9+** — for Monica's morning trends + Bighead's trading bot
- **7 Discord bot tokens** — one per agent ([Discord Developer Portal](https://discord.com/developers/applications))
- **A Discord server** with 6 channels: #general, #strategy, #engineering, #content, #research, #bd
- **X/Twitter API keys** (optional) — for automated tweeting and research

---

## Quick Start

```bash
git clone https://github.com/shirollsasaki/openclaw-team.git
cd openclaw-team

cp .env.example .env
# Edit .env — add your 7 Discord bot tokens + gateway token

chmod +x setup.sh
./setup.sh
```

Agents come online in Discord. Talk to them with @mentions.

---

## Manual Setup

If you prefer to understand each step:

### 1. Install OpenClaw

```bash
npm install -g openclaw
```

### 2. Copy agent workspaces

```bash
mkdir -p ~/.openclaw
cp -r agents/* ~/.openclaw/
```

### 3. Install external skills

```bash
# x-research (for Richard, Erlich, Bighead, Dinesh)
for agent in richard erlich bighead dinesh; do
  git clone https://github.com/rohunvora/x-research-skill.git ~/.openclaw/$agent/skills/x-research
done

# x-writing-system (for Jared, Monica)
for agent in jared monica; do
  git clone https://github.com/ashemag/x-writing-system-skill.git ~/.openclaw/$agent/skills/x-writing-system
  (cd ~/.openclaw/$agent/skills/x-writing-system && bun install)
done

# Marketing skills pack (25 skills — shared/global)
npx --yes skills add coreyhaines31/marketingskills --yes --global
```

### 4. Configure openclaw.json

Copy `openclaw.json` to `~/.openclaw/openclaw.json`. Then:

1. Replace `OPENCLAW_HOME` with your actual path (e.g., `/Users/you/.openclaw`)
2. Replace `YOUR_GUILD_ID` with your Discord server ID
3. Replace `YOUR_*_CHANNEL_ID` placeholders with your Discord channel IDs

### 5. Set up Discord bots

For each of the 7 agents:
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application (name it after the agent)
3. Go to Bot → create bot → copy token
4. Enable Message Content Intent under Privileged Gateway Intents
5. Invite the bot to your server with Send Messages + Read Messages permissions

### 6. Configure tokens

```bash
cp .env.example ~/.openclaw/.env
chmod 600 ~/.openclaw/.env
# Edit and fill in all tokens
```

### 7. Start the gateway

```bash
openclaw gateway install
openclaw gateway start
```

---

## Customization

**Make it yours:**

- **USER.md** — Edit in each agent's workspace. Tell them your name, timezone, what you're building.
- **MEMORY.md** — Add your products, APIs, portfolio. This is how agents learn your world.
- **SOUL.md** — Change personalities. Warning: these are the secret sauce. Edit with care.
- **openclaw.json** — Add/remove skills per agent, change models, adjust channel permissions.
- **cron/jobs.json** — Modify schedules, add new automated workflows.

---

## Optional: Google Workspace

All agents come pre-configured with the `gog` skill for Google Sheets/Docs/Drive integration.

```bash
brew install steipete/tap/gogcli
gog auth credentials          # paste your OAuth client_secret.json
gog auth add you@email.com --services sheets,docs,drive
```

Agents can then export data to Google Sheets, create docs, etc.

---

## Useful Commands

```bash
openclaw health              # quick agent status
openclaw doctor              # full diagnostics
openclaw gateway restart     # restart after config changes
openclaw cron list           # view scheduled jobs
openclaw agent --agent richard -m "morning brief"   # test an agent
```

---

## Credits

- [OpenClaw](https://docs.openclaw.ai) — the AI agent framework
- [x-research](https://github.com/rohunvora/x-research-skill) by @rohunvora — X/Twitter research skill
- [x-writing-system](https://github.com/ashemag/x-writing-system-skill) by @ashemag — content writing skill
- [marketingskills](https://github.com/coreyhaines31/marketingskills) by @coreyhaines31 — 25 marketing skills pack

---

MIT License

---

## What's Included Beyond Agents

### Bighead Trading Bot (`bighead-trading/`)
Avantis perpetual futures trading bot running on Base L2. Includes:
- Multiple strategy iterations (v1, v2, v2_squeeze, v3)
- Backtesting framework with optimization
- Live trading with position management
- Emergency stop scripts
- Discord status monitoring

### Monitor API (`openclaw-monitor-api/`)
Node.js Express API that exposes agent status, cron job state, and health metrics. Designed to feed the iOS app.

### iOS Mission Control (`OpenClawMissionControl/`)
SwiftUI app for monitoring all agents from your phone. Shows agent status, cron results, trading positions, and Claude credit usage.

### Scripts (`scripts/`)
- `x-post.mjs` — Post tweets via Twitter API v2 (OAuth 1.0a)
- `x-dm.mjs` — Send DMs via Twitter API
- `x-thread.mjs` — Post multi-tweet threads
- `morning_trends.py` — Scrapes HackerNews + KooSocial for daily trends (used by Monica's cron)
