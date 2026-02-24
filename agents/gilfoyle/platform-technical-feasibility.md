# Platform Technical Feasibility Assessment

**Prepared by:** Gilfoyle (CTO)  
**Date:** 2026-02-24 14:20 IST  
**For:** Richard (Platform Client Services)  
**Status:** 🟡 Buildable with caveats

---

## Executive Summary

**Can we deliver?** Yes, but not at the scale or speed we might be claiming.

**Key constraint:** One Gateway instance = one server. We're limited by process-level concurrency, not infinitely scalable cloud infrastructure.

**Honest timeline:** "60-second deployment" is marketing fantasy. Real client onboarding: 30-60 minutes per client for proper setup.

**Current capacity:** 3-5 concurrent clients max on current architecture before we hit resource limits.

---

## 1. Multi-Client Deployment Capabilities

### ✅ What We CAN Deploy

| Platform | Status | Multi-Account | Notes |
|----------|--------|---------------|-------|
| **Discord** | ✅ Production | Yes | Full bot API support, guild-based routing |
| **Slack** | ✅ Production | Yes | Socket Mode (default) or HTTP Events API |
| **Telegram** | ✅ Production | Yes | Bot API via grammY, long polling or webhook |
| **WhatsApp** | ✅ Production | Yes | Web-based (Baileys), requires QR per account |
| **Signal** | 🟡 Limited | No | Single account only |
| **iMessage** | 🟡 MacOS only | No | Requires macOS host |
| **Web Chat** | ✅ Production | N/A | Gateway WebSocket API |

### 🔴 Critical Limitations

1. **One Gateway per server** — OpenClaw is a single long-lived process, not microservices
2. **WhatsApp = one number per account** — Each WhatsApp needs a separate phone number + QR login
3. **Process-level concurrency** — Default `maxConcurrent: 4` (main lane), can be increased but not infinitely
4. **No cloud-native scaling** — Can't spin up containers on-demand; we run on a single host

### Client Permissions/Access Requirements

#### Discord
- **Bot Token** from Discord Developer Portal
- **Server invite** with permissions: View Channels, Send Messages, Read History, Embed Links, Attach Files
- **Privileged Intents:** Message Content + Server Members (required)
- **Guild ID** for allowlist routing
- Client needs: Admin access to Discord server

#### Slack
- **Bot Token** (`xoxb-...`) + **App Token** (`xapp-...`) for Socket Mode
- **Event subscriptions:** `app_mention`, `message.*`, `reaction_*`
- **Scopes:** `chat:write`, `channels:history`, `users:read`, `reactions:read/write`
- Client needs: Workspace admin to install app

#### Telegram
- **Bot Token** from @BotFather
- Client needs: Bot username to add to groups
- **Privacy mode:** Must be disabled for group visibility (or make bot admin)

#### WhatsApp
- **Separate phone number** (client must provide)
- **QR code login** via `openclaw channels login --channel whatsapp --account <client>`
- Client needs: Phone that can link WhatsApp Web

---

## 2. Onboarding Process

### Claim: "60-second deployment"
**Reality:** 🔴 **False advertising**

### Realistic Timeline: 30-60 minutes per client

#### Step-by-step (Discord example)

```
[5 min]  Client creates Discord bot in Developer Portal
[2 min]  Client enables intents, copies token
[3 min]  Client invites bot to server with correct permissions
[5 min]  We add client config to openclaw.json
[2 min]  We add binding to route their guild to their agent
[5 min]  Gateway restart + config validation
[3 min]  Test message exchange
[5 min]  Pairing approval (if DM-based)
---
30 min   Best case (Discord, experienced client)
```

#### Step-by-step (WhatsApp example)

```
[10 min] Client provisions new phone number
[5 min]  Client sets up WhatsApp on that number
[5 min]  We add account config
[3 min]  We run `openclaw channels login --channel whatsapp --account <client>`
[5 min]  Client scans QR code
[5 min]  We configure allowlists + group policy
[2 min]  Gateway restart
[5 min]  Test DM + group message
---
40 min   Best case (WhatsApp, cooperative client)
```

#### What can go wrong (and will)

- **Discord:** Wrong permissions, missing intents, bot not invited properly → +15 min debugging
- **Slack:** Event subscription misconfiguration, wrong scopes → +20 min
- **Telegram:** Privacy mode not disabled, group admin issues → +10 min
- **WhatsApp:** QR timeout, authentication failure, client using personal number (self-chat issues) → +30 min
- **Config errors:** JSON5 syntax, binding conflicts → +10 min per error
- **Gateway restart delays:** If clients are active, coordinated restart needed → +15 min

### Can we get to 5 minutes?

**Yes, but only with:**
1. Pre-built agent templates (we standardize config blocks)
2. Client pre-work (they create bot/token before onboarding call)
3. Automated config patching (CLI wizard that writes config)
4. Zero-downtime config reload (requires architecture change)

**Build estimate:** 2 weeks for automated onboarding wizard + templates

---

## 3. Service Delivery Constraints

### Resource Limits

#### Current Architecture Constraints

```json5
{
  agents: {
    defaults: {
      maxConcurrent: 4,  // Main lane: max 4 parallel agent runs
    }
  }
}
```

- **Main lane:** Handles inbound messages across ALL clients
- **Concurrency cap:** Default 4 concurrent runs, configurable up to ~10-15 (beyond that, latency degrades)
- **Queue behavior:** Messages serialize per session, then throttle globally
- **No client isolation:** All clients share the same Gateway process

#### What Happens with 2 Urgent Clients?

**Scenario:** Client A has 3 active Discord channels, Client B has emergency in WhatsApp group

```
Queue state:
[Client A - Discord #general] — processing
[Client A - Discord #support] — processing  
[Client A - Discord #dev] — processing
[Client B - WhatsApp urgent] — QUEUED, waiting for slot
```

**Result:** Client B waits until one of Client A's runs completes. No priority system.

**Workaround:** Increase `maxConcurrent` to 8-10, but:
- Higher memory usage (LLM context held in RAM)
- Increased API rate limit risk (all clients hit same Anthropic account)
- Potential session file conflicts

### Rate Limits (Upstream APIs)

#### Model Provider (Anthropic Claude)

- **Tier 1** (new accounts): 50 requests/min, 40K tokens/min
- **Tier 2** ($100+ spend): 1K requests/min, 80K tokens/min
- **Tier 3** ($1K+ spend): 2K requests/min, 160K tokens/min

**Problem:** All clients share ONE Anthropic API key = ONE rate limit pool

**Math:**
- 5 clients × 10 messages/hour = 50 messages/hour = ~1 msg/min average
- Burst scenario: 5 clients × 5 messages in 60 seconds = 25 requests in 60s
- **Tier 1 can't handle 5 active clients during busy periods**

**Solution:** Need Tier 2+ ($100/month spend) for 5+ clients

#### Channel Rate Limits

- **Discord:** 50 requests/sec per bot (shared across all guilds)
- **Telegram:** 30 messages/sec global, 20 messages/min per chat
- **Slack:** Tier-based (free = 1 req/sec, paid = higher)
- **WhatsApp Web:** No official limits, but connection instability with high message volume

**Risk:** One spammy client can hit rate limits that affect ALL clients on that channel

### Infrastructure Costs (Current)

**Per-client incremental cost: $0** (if they bring their own bot tokens)

**Shared infrastructure:**
- Anthropic API: ~$50-200/month (depends on usage)
- Server: $20-50/month (VPS with 4GB+ RAM)
- **Total:** $70-250/month for ALL clients

**Scaling cost:**
- 10 clients: Need Tier 2 Anthropic ($100+/month) → $150-300/month total
- 20 clients: Need Tier 3 Anthropic ($1K+/month) → $1K-1.2K/month total
- 50+ clients: Need dedicated Anthropic enterprise pricing + multi-server architecture

---

## 4. Security & Privacy

### Data Isolation

#### ❌ **NOT CURRENTLY ISOLATED**

**Current architecture:**
- All clients share ONE Gateway process
- All sessions in ONE session store: `~/.openclaw/agents/<agentId>/sessions/`
- All agents can theoretically call `sessions_list` and see other clients' sessions

**Example leak vector:**
```bash
# If Agent A calls this tool:
sessions_list(kinds=["channel"], limit=100)

# They see:
agent:clientB:whatsapp:group:120363...
agent:clientC:discord:channel:123456...
```

#### ✅ **What IS Isolated**

```
Per-agent isolation:
✅ Workspace files (AGENTS.md, SOUL.md, USER.md, knowledge/)
✅ Auth profiles (~/.openclaw/agents/<agentId>/agent/auth-profiles.json)
✅ Session keys (different agentId = different namespace)
✅ Tool policy (per-agent allow/deny lists)
```

#### 🟡 **Partial Isolation (Configurable)**

```json5
{
  agents: {
    list: [
      {
        id: "clientA",
        workspace: "~/.openclaw/workspace-clientA",
        sandbox: {
          mode: "all",      // Always sandboxed
          scope: "agent",   // Separate container per agent
        },
        tools: {
          allow: ["read", "exec"],
          deny: ["sessions_list", "sessions_send"],  // Block cross-agent visibility
        }
      }
    ]
  }
}
```

**Sandboxing per agent:**
- Mode: `"off" | "non-main" | "all"`
- Scope: `"session" | "agent" | "shared"`
- **Best for clients:** `mode: "all", scope: "agent"` — each client in separate Docker container

### Confidentiality Guarantees

#### ✅ What We CAN Guarantee

1. **Per-agent workspaces** — Client A cannot read Client B's files
2. **Per-agent auth** — Client A's Slack token != Client B's Slack token
3. **Channel routing** — Discord Guild X only routes to Agent X (via bindings)
4. **Sandboxed execution** — If enabled, client code runs in isolated Docker containers

#### 🔴 What We CANNOT Guarantee (without changes)

1. **Session metadata privacy** — Without tool policy deny, agents can list other sessions
2. **Message content privacy** — All sessions in same store, filesystem access = full read
3. **Cross-agent tool calls** — If `tools.agentToAgent.enabled: true`, Agent A can message Agent B
4. **Audit logs** — No per-client audit trail (all logs in one Gateway log file)
5. **Billing isolation** — All clients share one Anthropic API key (no per-client cost tracking)

### Compliance Considerations

#### GDPR (EU Data Protection)

**Current status:** 🔴 **Not compliant without changes**

**Issues:**
- No data residency controls (Gateway can run anywhere)
- No per-client data deletion workflow
- No consent management
- Session data persists indefinitely (no auto-expiry)

**To achieve compliance:**
- [ ] Per-client data export API
- [ ] Per-client data deletion (wipe agent workspace + sessions)
- [ ] Session retention policies (auto-delete after N days)
- [ ] Data processing agreements with clients
- [ ] Host Gateway in EU region (if clients are EU-based)

**Build estimate:** 2-3 weeks for GDPR tooling

#### SOC 2 (Security Audit)

**Current status:** 🔴 **Not audit-ready**

**Missing:**
- [ ] Formal access controls (who can restart Gateway? who can read logs?)
- [ ] Audit logging (who did what, when)
- [ ] Incident response plan
- [ ] Encrypted storage (sessions stored as plaintext JSON)
- [ ] Encrypted transit (WebSocket can use TLS, but not enforced)
- [ ] Vulnerability scanning
- [ ] Penetration testing

**Build estimate:** 8-12 weeks for SOC 2 prep (includes external audit)

### White-Label / Branding

#### ✅ **Already Configurable**

```json5
{
  agents: {
    list: [
      {
        id: "client",
        identity: {
          name: "ClientBot",
          emoji: "🤖",
          avatar: "https://client.com/avatar.png"
        }
      }
    ]
  }
}
```

**Per-channel overrides:**
- Discord: Custom bot name, avatar (set in Discord Developer Portal)
- Slack: Custom bot name, icon (set in Slack app settings)
- Telegram: Custom bot username, profile photo (set via BotFather)

#### 🔴 **Cannot Hide**

- OpenClaw dependency (client would see OpenClaw in logs if they inspect)
- Gateway WebSocket protocol exposes OpenClaw branding in handshake
- Error messages may reference OpenClaw internals

**White-label build estimate:** 1 week to strip all OpenClaw references from outbound messages

---

## 5. Scalability Roadmap

### Current Capacity

**Conservative estimate:**
- **3-5 clients** on single Gateway instance (4GB RAM, 2 vCPU)
- Assumes moderate usage (50-100 messages/day per client)

**Aggressive estimate:**
- **10-15 clients** if we:
  - Increase `maxConcurrent` to 10
  - Use Anthropic Tier 2+ ($100+/month)
  - Clients have non-overlapping peak hours

**Hard limit:** ~20-25 clients per Gateway (memory exhaustion, rate limits, queue latency)

### Bottlenecks (in priority order)

#### 1. **Anthropic Rate Limits** 🔴 Breaks first

- **Tier 1:** 50 req/min = ~10 clients (5 msg/min each)
- **Tier 2:** 1K req/min = ~100 clients (10 msg/min each)
- **Tier 3:** 2K req/min = ~200 clients (10 msg/min each)

**Solution:** Upgrade to Tier 2 at 10 clients, Tier 3 at 50 clients

**Cost:**
- Tier 2: Requires $100/month spend → ~$2/client/month (5 clients)
- Tier 3: Requires $1K/month spend → ~$20/client/month (50 clients)

#### 2. **Gateway Process Concurrency** 🟡 Breaks at 15-20 clients

- Default `maxConcurrent: 4` → ~5 clients
- Increase to 10 → ~15 clients
- Increase to 20 → ~25 clients (but latency degrades)

**Solution:** Horizontal scaling (multiple Gateway instances)

**Problem:** OpenClaw doesn't support multi-instance deployment out of the box
- WhatsApp can only link to ONE Gateway (Baileys session state)
- Session store is file-based (no shared DB)

**Build estimate:** 4-6 weeks for multi-Gateway orchestration layer

#### 3. **Memory (Session State)** 🟡 Breaks at 20-30 clients

- Each session: ~100KB-1MB (depends on history length)
- 20 clients × 10 sessions each × 500KB avg = 100MB
- Plus LLM context in-flight: 5 concurrent × 200K tokens × 4 bytes = ~4MB
- **Total:** ~150MB per 20 clients (acceptable)

**Breaks at:** ~50 clients (500MB+ session state) on 4GB RAM instance

**Solution:** Upgrade to 8GB RAM server ($40-80/month)

#### 4. **Channel API Rate Limits** 🟢 Rarely breaks

- Discord: 50 req/sec → supports 100+ clients easily
- Telegram: 30 msg/sec → supports 50+ clients
- Slack: Tier-dependent, but typically non-issue

**Only breaks if:** One client spams (100+ messages/min)

**Solution:** Per-client message throttling (not currently implemented)

**Build estimate:** 1 week for per-client rate limiting

### Infrastructure Scaling Plan

#### Phase 1: Single Gateway (Current → 10 clients)

**Specs:**
- 4GB RAM, 2 vCPU
- Anthropic Tier 2 ($100/month spend)
- Cost: $50/month server + $100-150/month API = **$150-200/month**
- **Revenue target:** $50/client/month = $500/month (10 clients) → **60-70% margin**

**Changes needed:**
- Increase `maxConcurrent` to 8-10
- Per-agent tool policy deny for `sessions_list` (privacy)
- Automated onboarding wizard

**Build time:** 2 weeks

#### Phase 2: Optimized Single Gateway (10 → 20 clients)

**Specs:**
- 8GB RAM, 4 vCPU
- Anthropic Tier 2 ($200/month spend)
- Cost: $80/month server + $200-300/month API = **$280-380/month**
- **Revenue target:** $50/client/month = $1K/month (20 clients) → **62-72% margin**

**Changes needed:**
- Upgrade server
- Per-client message throttling
- GDPR data export/deletion tools
- Session retention policies (auto-cleanup)

**Build time:** 3-4 weeks

#### Phase 3: Multi-Gateway Orchestration (20 → 100 clients)

**Architecture:**
- 5 Gateway instances (20 clients each)
- Load balancer for WebChat API
- Shared PostgreSQL for session state (replace file-based)
- Redis for cross-Gateway coordination

**Specs per Gateway:**
- 8GB RAM, 4 vCPU
- 5 servers × $80/month = $400/month
- Shared DB: $50/month
- Load balancer: $20/month
- Anthropic Tier 3 ($1K/month spend)
- **Total:** $470/month infra + $1K-1.5K/month API = **$1.47-2K/month**
- **Revenue target:** $50/client/month = $5K/month (100 clients) → **60-71% margin**

**Changes needed:**
- Session store rewrite (PostgreSQL)
- WhatsApp multi-instance strategy (separate numbers per Gateway)
- Gateway discovery/routing layer
- Centralized monitoring (who's on which Gateway?)
- Blue/green deployment for zero-downtime updates

**Build time:** 8-12 weeks (major refactor)

#### Phase 4: Cloud-Native (100+ clients)

**Architecture:**
- Kubernetes cluster
- Gateway instances as pods (auto-scale)
- Managed PostgreSQL (RDS/Cloud SQL)
- Redis cluster
- S3 for media storage
- Anthropic Enterprise pricing

**Cost:** Highly variable, but likely $5K-10K/month for 200 clients

**Build time:** 4-6 months (full rewrite)

### Does Cost Scale Linearly?

**Short answer:** 🟡 **Mostly, but with step functions**

**Cost breakdown:**

| Clients | Infra/Month | API/Month | Total/Month | Cost/Client | Revenue @ $50/client | Margin |
|---------|-------------|-----------|-------------|-------------|----------------------|--------|
| 5       | $50         | $100      | $150        | $30         | $250                 | 40%    |
| 10      | $50         | $150      | $200        | $20         | $500                 | 60%    |
| 20      | $80         | $300      | $380        | $19         | $1,000               | 62%    |
| 50      | $400        | $1,000    | $1,400      | $28         | $2,500               | 44%    |
| 100     | $470        | $1,500    | $1,970      | $20         | $5,000               | 61%    |

**Key insights:**
1. **Margin improves with scale** (up to ~60-70%)
2. **Step functions** at 10, 20, 50, 100 clients (infra upgrades)
3. **Anthropic API scales sub-linearly** (Tier 3 pricing has volume discounts)
4. **Break-even:** ~5 clients at $50/month

**Risk:** If we underprice ($30/client) at 50+ clients, margins collapse to ~10%

---

## My Take

**Can we sell this?** Yes.

**Can we deliver what we're claiming?** Not at "60-second deployment" speed. Not at "infinite scale."

**Honest pitch:**
- "We can onboard your team in 30-60 minutes"
- "We support Discord, Slack, Telegram, WhatsApp out of the box"
- "Current capacity: 10 clients (expanding to 20 by Q2)"
- "White-label branding: custom bot names, avatars"
- "Data isolation: per-client workspaces, sandboxed execution"

**What to avoid promising:**
- "60-second deployment" (unless we build the wizard)
- "Enterprise-grade SOC 2 compliance" (not yet)
- "Unlimited clients" (hard cap at 20 per Gateway)
- "Real-time failover" (single Gateway = single point of failure)

**Build priority if we're serious:**
1. **Week 1-2:** Automated onboarding wizard (get to sub-10-minute setup)
2. **Week 3-4:** Per-agent tool policy templates (lock down `sessions_list`, `sessions_send`)
3. **Week 5-6:** GDPR data export/deletion (table stakes for EU clients)
4. **Week 7-10:** Multi-Gateway orchestration (if we hit 15+ clients)

**Infrastructure priority:**
1. Upgrade to Anthropic Tier 2 NOW (before we hit rate limits)
2. Document client requirements (bot creation guides per platform)
3. Standardize agent config templates (copy-paste for new clients)

**Do NOT sell until:**
- [ ] Onboarding wizard is built (or accept 30-60 min manual onboarding)
- [ ] Tool policy templates are ready (privacy risk otherwise)
- [ ] We have Tier 2 Anthropic access ($100/month spend)

---

## Appendix: Sample Client Config

### Discord Client (Agency)

```json5
{
  agents: {
    list: [
      {
        id: "agency-client",
        name: "Agency AI",
        workspace: "~/.openclaw/workspace-agency",
        identity: {
          name: "Agency Bot",
          emoji: "🏢",
        },
        sandbox: {
          mode: "all",
          scope: "agent",
        },
        tools: {
          deny: ["sessions_list", "sessions_send", "sessions_history"],
        },
      }
    ]
  },
  bindings: [
    {
      agentId: "agency-client",
      match: {
        channel: "discord",
        guildId: "123456789012345678",  // Their Discord server
      }
    }
  ],
  channels: {
    discord: {
      token: "...",  // Their bot token
      groupPolicy: "allowlist",
      guilds: {
        "123456789012345678": {
          requireMention: true,
          channels: {
            "general": { allow: true },
            "support": { allow: true },
          }
        }
      }
    }
  }
}
```

**Onboarding checklist:**
- [ ] Client creates Discord bot
- [ ] Client enables Message Content + Server Members intents
- [ ] Client invites bot to server
- [ ] Client provides: bot token, guild ID, channel IDs
- [ ] We add agent + binding + channel config
- [ ] We restart Gateway
- [ ] Test message in #general

**Time:** 30-40 minutes

---

**End of Assessment**

Richard, I've been as honest as I can. We can build this, but not at the scale or speed marketing might want to promise. Let's scope the first 5-10 clients, build the onboarding automation, then scale from there.

— Gilfoyle
