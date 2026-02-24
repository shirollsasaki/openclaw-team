# Memory

## My Role
CTO. I own technical feasibility checks, architecture decisions, build estimates, and MVP scoping. I answer "Can we build X in Y weeks?"

## Team
- Boss: Naman (@shirollsasaki) — Discord
- Reports to: Richard (Co-Founder)
- Works with: Bighead (data/scripts), Dinesh (technical research)

## Products & Portfolio
- Corners.market — crypto curation marketplace on Base chain (Base ecosystem)
- Early.build — dev tools marketplace connecting devs with early access + paid work

## Key Decisions

### 2026-02-24: Platform Client Services Feasibility
- **Decision:** Can deploy multi-client platform, but with hard constraints
- **Capacity:** 3-5 clients current, 10-15 clients optimized single Gateway
- **Onboarding:** 30-60 min realistic (not 60 seconds)
- **Scaling:** Need multi-Gateway architecture at 20+ clients (8-12 week build)
- **Cost model:** Sub-linear scaling with step functions at 10, 20, 50, 100 clients
- **Margins:** 60-70% at scale ($50/client pricing)
- **Priorities:** (1) Onboarding wizard, (2) Tool policy templates, (3) GDPR tooling

## Architecture Notes

### OpenClaw Multi-Client Architecture
- **One Gateway = One Process** — not microservices, not cloud-native
- **Concurrency:** `maxConcurrent` default 4, can push to 10-15 before degradation
- **Rate limits:** Anthropic Tier 1 (50 req/min) breaks at 10 clients
- **Session store:** File-based (no shared DB) — bottleneck for horizontal scaling
- **Per-agent isolation:** Workspace, auth, sessions keyed by agentId
- **No session metadata privacy** without tool policy deny (`sessions_list`)
- **Channels:** Discord, Slack, Telegram, WhatsApp all production-ready
- **WhatsApp constraint:** One number per account, QR login per Gateway instance

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
