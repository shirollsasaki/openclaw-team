# ClawDeploy — Technical Scope

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   FRONTEND (Vercel)                   │
│              Next.js 14+ / App Router                 │
│                                                       │
│  Landing Page → Auth (Clerk) → Dashboard → Deploy     │
└──────────────────────┬──────────────────────────────┘
                       │ API calls
                       ▼
┌─────────────────────────────────────────────────────┐
│                 BACKEND API (Railway)                  │
│              Node.js / Express or Hono                 │
│                                                       │
│  /api/deploy    — provision new instance               │
│  /api/status    — check instance health                │
│  /api/restart   — restart user's instance              │
│  /api/delete    — tear down instance                   │
│  /api/templates — list available templates             │
│  /api/billing   — Stripe webhook handler               │
│                                                       │
│  Services:                                            │
│  - ProvisioningService (Railway API)                  │
│  - TemplateService (config injection)                 │
│  - BillingService (Stripe)                            │
│  - HealthService (instance monitoring)                │
└──────────────────────┬──────────────────────────────┘
                       │ Railway API
                       ▼
┌─────────────────────────────────────────────────────┐
│            USER INSTANCES (Railway Services)           │
│                                                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │
│  │  User A      │ │  User B      │ │  User C      │   │
│  │  Solo (1 bot)│ │  Team (3)    │ │  Pro (7)     │   │
│  │  Docker      │ │  Docker      │ │  Docker      │   │
│  │  OpenClaw    │ │  OpenClaw    │ │  OpenClaw    │   │
│  └─────────────┘ └─────────────┘ └─────────────┘    │
│                                                       │
│  Each container:                                      │
│  - OpenClaw gateway running                           │
│  - Template configs mounted                           │
│  - User API keys as encrypted env vars                │
│  - Channel tokens as encrypted env vars               │
└─────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Tech | Why |
|-------|------|-----|
| Frontend | Next.js 14, Tailwind, shadcn/ui | Fast to build, great DX |
| Auth | Clerk | Social login, user management, free tier |
| Backend | Node.js + Hono (or Express) | Lightweight, Railway-native |
| Database | PostgreSQL (Railway) | Users, instances, billing state |
| Provisioning | Railway API | Programmatic service creation, env injection |
| Containers | Docker | OpenClaw runs in isolated containers |
| Billing | Stripe | Subscriptions, webhooks, customer portal |
| Hosting (frontend) | Vercel | Free tier, edge functions |
| Hosting (backend + DB) | Railway | Already where user instances live |
| Monitoring | Uptime Kuma or custom | Health checks on user instances |

## Database Schema

```sql
-- Users
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_id VARCHAR(255) UNIQUE NOT NULL,
  email VARCHAR(255) NOT NULL,
  stripe_customer_id VARCHAR(255),
  plan VARCHAR(20) DEFAULT 'free', -- free, solo, team, pro
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Instances (one per user, or multiple for pro)
CREATE TABLE instances (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  template_id VARCHAR(50) NOT NULL, -- 'solo-assistant', 'marketing-team', etc.
  railway_service_id VARCHAR(255), -- Railway service ID
  railway_environment_id VARCHAR(255),
  status VARCHAR(20) DEFAULT 'provisioning', -- provisioning, running, stopped, error
  region VARCHAR(20) DEFAULT 'us-west-1',
  plan VARCHAR(20) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Secure key storage (encrypted at rest)
CREATE TABLE user_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  instance_id UUID REFERENCES instances(id),
  key_type VARCHAR(50) NOT NULL, -- 'anthropic', 'openai', 'discord_bot_richard', 'telegram'
  encrypted_value TEXT NOT NULL, -- AES-256-GCM encrypted
  created_at TIMESTAMP DEFAULT NOW()
);
```

## Template System

### Template Structure

Each template is a directory in the repo:

```
templates/
├── solo-assistant/
│   ├── manifest.json
│   ├── openclaw.json
│   └── agents/
│       └── assistant/
│           ├── SOUL.md
│           ├── AGENTS.md
│           └── TOOLS.md
│
├── marketing-team/
│   ├── manifest.json
│   ├── openclaw.json
│   └── agents/
│       ├── richard/
│       │   ├── SOUL.md
│       │   ├── AGENTS.md
│       │   ├── COLLABORATION_RULES.md
│       │   └── TASKS.md
│       ├── jared/
│       │   ├── SOUL.md
│       │   ├── AGENTS.md
│       │   ├── COLLABORATION_RULES.md
│       │   └── TASKS.md
│       ├── erlich/
│       ├── gilfoyle/
│       ├── monica/
│       ├── bighead/
│       └── dinesh/
│
├── support-squad/
│   ├── manifest.json
│   ├── openclaw.json
│   └── agents/
│       ├── triage/
│       ├── faq-specialist/
│       └── escalation-manager/
│
└── content-machine/
    ├── manifest.json
    ├── openclaw.json
    └── agents/
        ├── researcher/
        ├── writer/
        └── editor/
```

### manifest.json Example

```json
{
  "id": "marketing-team",
  "name": "Marketing Team",
  "description": "7-agent marketing & ops team. Strategy, content, research, BD, engineering — all pre-wired with collaboration rules.",
  "version": "1.0.0",
  "tier": "pro",
  "agents": 7,
  "channels": ["discord"],
  "requiredKeys": [
    { "id": "anthropic", "label": "Anthropic API Key", "hint": "Get from console.anthropic.com" },
    { "id": "discord_bot_1", "label": "Discord Bot Token (Richard)", "hint": "Create at discord.dev/applications" },
    { "id": "discord_bot_2", "label": "Discord Bot Token (Jared)", "hint": "" },
    { "id": "discord_bot_3", "label": "Discord Bot Token (Erlich)", "hint": "" },
    { "id": "discord_bot_4", "label": "Discord Bot Token (Gilfoyle)", "hint": "" },
    { "id": "discord_bot_5", "label": "Discord Bot Token (Monica)", "hint": "" },
    { "id": "discord_bot_6", "label": "Discord Bot Token (Big Head)", "hint": "" },
    { "id": "discord_bot_7", "label": "Discord Bot Token (Dinesh)", "hint": "" }
  ],
  "requiredInputs": [
    { "id": "guild_id", "label": "Discord Server ID", "hint": "Right-click server → Copy Server ID" }
  ],
  "features": [
    "7 specialized agents with unique personas",
    "Pre-built collaboration rules and handoff protocols",
    "6 dedicated Discord channels (general, strategy, engineering, content, research, bd)",
    "Morning briefs, team dashboards, EOD recaps",
    "X/Twitter research integration ready"
  ]
}
```

### Config Injection (Provisioning)

The `openclaw.json` in each template uses placeholder variables:

```json
{
  "channels": {
    "discord": {
      "accounts": {
        "richard": {
          "token": "{{DISCORD_BOT_1}}",
          "guilds": {
            "{{GUILD_ID}}": {
              "channels": {}
            }
          }
        }
      }
    }
  }
}
```

**Provisioning script** replaces `{{VAR}}` placeholders with user-provided values, writes the final config, and starts the gateway.

```javascript
// pseudocode: provision.js
async function provision(templateId, userKeys, userInputs) {
  // 1. Copy template directory to workspace
  const workspace = `/openclaw/workspace`;
  await copyTemplate(templateId, workspace);
  
  // 2. Replace placeholders in openclaw.json
  let config = await readFile(`${workspace}/openclaw.json`, 'utf8');
  for (const [key, value] of Object.entries(userKeys)) {
    config = config.replaceAll(`{{${key.toUpperCase()}}}`, value);
  }
  for (const [key, value] of Object.entries(userInputs)) {
    config = config.replaceAll(`{{${key.toUpperCase()}}}`, value);
  }
  await writeFile(`${workspace}/openclaw.json`, config);
  
  // 3. Start OpenClaw gateway
  exec('openclaw gateway start');
}
```

## Provisioning Flow (Railway API)

```javascript
// Backend: /api/deploy
async function deployInstance(userId, templateId, keys) {
  // 1. Create Railway project for user (if first instance)
  const project = await railway.createProject({
    name: `clawdeploy-${userId}`,
  });
  
  // 2. Create service from our Docker image
  const service = await railway.createService({
    projectId: project.id,
    name: templateId,
    source: {
      image: 'ghcr.io/clawdeploy/openclaw-runtime:latest'
    }
  });
  
  // 3. Set environment variables (user keys, encrypted)
  await railway.setVariables(service.id, {
    ANTHROPIC_API_KEY: keys.anthropic,
    DISCORD_TOKEN_1: keys.discord_bot_1,
    DISCORD_TOKEN_2: keys.discord_bot_2,
    // ... etc
    TEMPLATE_ID: templateId,
    GUILD_ID: keys.guild_id,
  });
  
  // 4. Deploy
  await railway.deploy(service.id);
  
  // 5. Save to DB
  await db.instances.create({
    userId,
    templateId,
    railwayServiceId: service.id,
    status: 'provisioning'
  });
  
  // 6. Poll until healthy
  await pollHealth(service.id);
}
```

## Docker Image

```dockerfile
# Dockerfile: openclaw-runtime
FROM node:22-slim

# Install OpenClaw globally
RUN npm install -g openclaw@latest

# Create workspace
RUN mkdir -p /openclaw/workspace

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy all templates
COPY templates/ /openclaw/templates/

WORKDIR /openclaw/workspace

EXPOSE 18789

ENTRYPOINT ["/entrypoint.sh"]
```

```bash
#!/bin/bash
# entrypoint.sh

TEMPLATE_ID=${TEMPLATE_ID:-solo-assistant}
WORKSPACE=/openclaw/workspace

# 1. Copy template to workspace (if fresh deploy)
if [ ! -f "$WORKSPACE/openclaw.json" ]; then
  cp -r /openclaw/templates/$TEMPLATE_ID/* $WORKSPACE/
fi

# 2. Run config injection (replace {{PLACEHOLDERS}} with env vars)
node /openclaw/inject-config.js

# 3. Start OpenClaw gateway
cd $WORKSPACE
exec openclaw gateway --port 18789
```

## Frontend Pages

```
/                    — Landing page (hero, comparison table, templates showcase, pricing)
/login               — Clerk auth (Google, GitHub, email)
/dashboard           — User's instances list, status, quick actions
/deploy              — Template picker → key input → deploy button
/deploy/[templateId] — Template detail + configuration form
/instance/[id]       — Instance detail: status, logs, restart, delete
/billing             — Stripe customer portal, plan management
/docs                — Setup guides (how to create Discord bots, get API keys)
```

## API Routes

```
POST   /api/deploy              — Deploy new instance
GET    /api/instances            — List user's instances
GET    /api/instances/:id        — Instance status + details
POST   /api/instances/:id/restart — Restart instance
DELETE /api/instances/:id        — Delete instance + Railway service
GET    /api/templates            — List available templates
GET    /api/templates/:id        — Template detail + manifest
POST   /api/billing/checkout     — Create Stripe checkout session
POST   /api/billing/webhook      — Stripe webhook handler
POST   /api/billing/portal       — Create Stripe billing portal session
GET    /api/health               — API health check
```

## Security

1. **User API keys** — encrypted with AES-256-GCM before storing in DB. Decrypted only at injection time. Never logged.
2. **Railway env vars** — Railway encrypts environment variables at rest.
3. **Isolation** — each user gets their own Docker container. No shared processes.
4. **Auth** — Clerk handles auth. All API routes require valid session token.
5. **Rate limiting** — deploy endpoint rate-limited to prevent abuse.
6. **No LLM proxying** — we never see user prompts or AI responses. BYOK only.

## Monitoring & Health

```javascript
// Health check: runs every 5 minutes per instance
async function healthCheck(instance) {
  try {
    const res = await fetch(`${instance.url}:18789/health`, { timeout: 10000 });
    if (res.ok) {
      await db.instances.update(instance.id, { status: 'running', lastHealthy: new Date() });
    } else {
      await handleUnhealthy(instance);
    }
  } catch {
    await handleUnhealthy(instance);
  }
}

async function handleUnhealthy(instance) {
  const failCount = instance.consecutiveFailures + 1;
  await db.instances.update(instance.id, { 
    status: failCount > 3 ? 'error' : 'degraded',
    consecutiveFailures: failCount 
  });
  if (failCount === 3) {
    await notifyUser(instance.userId, 'Your instance is unhealthy. We\'re investigating.');
  }
  if (failCount > 5) {
    await railway.restart(instance.railwayServiceId);
  }
}
```

## Error Handling

| Error | Response |
|-------|----------|
| Invalid API key | Validate key format before deploy. Show clear error. |
| Railway provisioning fails | Retry once. If fails again, refund and notify. |
| Instance OOM | Auto-restart. If recurring, suggest upgrading tier. |
| User hits plan limit | Block deploy with upgrade CTA. |
| Stripe payment fails | Grace period (3 days), then pause instance. |
