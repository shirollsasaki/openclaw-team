# ClawDeploy — MVP Sprint Plan (2 Weeks)

## Guiding Principle
Ship the smallest thing that proves people will pay for pre-configured agent teams. Cut everything else.

## MVP Scope (IN)
- [x] Landing page with template showcase + pricing
- [ ] Auth (Clerk — Google/GitHub login)
- [ ] Template: Solo Assistant (1 agent, Telegram)
- [ ] Template: Marketing Team (7 agents, Discord) — our actual config
- [ ] Deploy flow: pick template → enter keys → click deploy → instance comes online
- [ ] Dashboard: list instances, status indicator, restart button, delete button
- [ ] Stripe billing: checkout, webhooks, plan enforcement
- [ ] Docker image with OpenClaw + config injection
- [ ] Railway API integration for provisioning
- [ ] Basic health monitoring

## MVP Scope (OUT — Post-Launch)
- Custom template builder
- Template marketplace (user-submitted templates)
- Auto Discord bot creation wizard
- Migration/export tools
- Team collaboration (multiple users per instance)
- Usage analytics dashboard
- Instance logs viewer in dashboard
- Custom domain per instance
- Backup/restore
- White-label / reseller

---

## Week 1: Foundation + Solo Template

### Day 1-2: Project Setup + Landing Page
```
Priority: Get something live people can see

Tasks:
- [ ] Init Next.js 14 project (App Router, Tailwind, shadcn/ui)
- [ ] Landing page sections:
      - Hero: "Deploy your AI team in 60 seconds"
      - Comparison: Traditional (60 min) vs ClawDeploy (1 min)
      - Template showcase: cards for each template
      - Pricing table: Solo / Team / Pro
      - FAQ
      - CTA: "Get Started" → /login
- [ ] Deploy to Vercel
- [ ] Set up Clerk auth (Google + GitHub)
- [ ] Set up Railway project for backend API
- [ ] Set up PostgreSQL on Railway
- [ ] Run DB migrations (users, instances, user_keys tables)
```

### Day 3-4: Backend API + Docker Image
```
Priority: Provisioning pipeline works end-to-end

Tasks:
- [ ] Backend API (Hono on Railway):
      - POST /api/deploy
      - GET /api/instances
      - GET /api/instances/:id
      - POST /api/instances/:id/restart
      - DELETE /api/instances/:id
      - GET /api/templates
- [ ] Docker image (openclaw-runtime):
      - Base: node:22-slim
      - OpenClaw pre-installed
      - entrypoint.sh: copy template → inject config → start gateway
      - inject-config.js: replace {{PLACEHOLDERS}} with env vars
      - Push to GitHub Container Registry
- [ ] Template: Solo Assistant
      - openclaw.json (1 agent, Telegram channel)
      - SOUL.md (general purpose assistant)
      - manifest.json (metadata, required keys)
- [ ] Railway API integration:
      - Create service from Docker image
      - Set env vars (user keys)
      - Deploy service
      - Poll until healthy
- [ ] Test: deploy Solo Assistant end-to-end
```

### Day 5: Deploy Flow UI + Integration Test
```
Priority: User can deploy from the website

Tasks:
- [ ] Deploy page UI:
      - Template picker (cards with details)
      - Template detail page with feature list
      - Key input form (dynamic based on manifest.json requiredKeys)
      - "Deploy" button with loading state
      - Success screen with instance URL + status
- [ ] Dashboard page:
      - Instance cards with status badge (provisioning/running/error)
      - Restart button
      - Delete button (with confirmation)
- [ ] End-to-end test:
      - Sign up → pick Solo → paste Anthropic key + Telegram token → deploy
      - Verify agent responds on Telegram
      - Verify dashboard shows running instance
      - Test restart
      - Test delete
```

---

## Week 2: Marketing Team Template + Billing + Launch

### Day 1-2: Marketing Team Template
```
Priority: The differentiator ships

Tasks:
- [ ] Package our actual 7-agent setup:
      - openclaw.json with all 7 agents, bindings, channel configs
      - All SOUL.md files (Richard, Jared, Erlich, Gilfoyle, Monica, Big Head, Dinesh)
      - All AGENTS.md files
      - COLLABORATION_RULES.md (shared)
      - TASKS.md (per agent)
      - Skills references
      - Guild channel auto-creation (or guide)
- [ ] manifest.json:
      - 8 required keys (1 Anthropic + 7 Discord bot tokens)
      - 1 required input (Guild ID)
- [ ] Config injection handles multi-agent setup:
      - All 7 bot tokens injected
      - Guild ID injected
      - Channel creation via Discord API at deploy time (or provide guide)
- [ ] Test: deploy Marketing Team end-to-end
      - All 7 agents come online in Discord
      - Agents respond to @mentions in correct channels
      - Collaboration rules work (handoffs, channel restrictions)
```

### Day 3-4: Billing + Polish
```
Priority: People can pay us

Tasks:
- [ ] Stripe integration:
      - Products: Solo ($9/mo), Team ($49/mo), Pro ($99/mo)
      - Checkout session creation
      - Webhook handler:
        - checkout.session.completed → activate instance
        - invoice.payment_failed → grace period
        - customer.subscription.deleted → pause instance
      - Billing portal (manage subscription, update card)
- [ ] Plan enforcement:
      - Solo: max 1 instance, 1 agent
      - Team: max 1 instance, 3 agents
      - Pro: max 2 instances, 7+ agents
- [ ] Polish:
      - Loading states and error handling
      - Mobile responsive landing page
      - Setup guide page: "How to create Discord bots" with screenshots
      - Setup guide page: "How to get your Anthropic API key"
      - Instance status polling (auto-refresh dashboard)
      - Email notifications (deploy success, instance down)
```

### Day 5: Launch
```
Priority: Get users

Tasks:
- [ ] Soft launch to creator network (55 people)
- [ ] Post on X/Twitter: "We run a 7-agent AI team. Now you can deploy the same setup in 60 seconds."
- [ ] Post on Hacker News: Show HN
- [ ] Post on Product Hunt (schedule for next week if not ready)
- [ ] Monitor deploys, fix issues in real-time
- [ ] Collect feedback from first 10 users
```

---

## Success Metrics (Week 2 End)

| Metric | Target |
|--------|--------|
| Waitlist signups | 200+ |
| Deployed instances | 20+ |
| Paying customers | 5+ |
| MRR | $200+ |
| Instance uptime | >99% |
| Deploy success rate | >90% |

## Post-MVP Roadmap (Weeks 3-8)

1. **More templates:** Support Squad, Content Machine, Dev Team
2. **Template marketplace:** users submit + sell their own templates
3. **Discord bot creation wizard:** OAuth flow to auto-create 7 bots
4. **Usage dashboard:** show per-agent token usage, costs
5. **One-click channel setup:** auto-create Discord channels at deploy
6. **WhatsApp + Slack support:** expand beyond Discord/Telegram
7. **Custom template builder:** visual editor for agent configs
8. **Backup/restore:** export your OpenClaw config anytime
9. **White-label:** agencies resell under their own brand
