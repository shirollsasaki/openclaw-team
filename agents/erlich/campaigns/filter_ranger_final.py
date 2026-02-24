#!/usr/bin/env python3
"""
Re-score profiles from BobbyTwitter-RangerMapping.csv using the ACTUAL Ranger ICP:
  → Background coding agent users who need to verify agent work
  → Vibe coders, solo founders, small teams shipping fast with AI
  → People who use Claude Code / Cursor / Windsurf / OpenCode / background agents

Filter: ≥500 followers only
Output: campaigns/Ranger-BobbyFinal.csv
"""
import csv
from collections import Counter

def parse_followers(s):
    s = str(s).strip()
    if 'M' in s: return float(s.replace('M','')) * 1_000_000
    if 'K' in s: return float(s.replace('K','')) * 1_000
    try: return float(s)
    except: return 0

def ranger_icp_score(bio, followers, name):
    """Score specifically for Ranger's ICP: background agent users."""
    b = bio.lower()
    score = 0

    # 🔥 Tier-1 signals: directly using agent coding tools
    tier1 = ['claude code', 'cursor', 'windsurf', 'copilot', 'opencode', 'background agent',
             'coding agent', 'ai agent', 'vibe cod', 'vibecod', 'vibe-cod', 'agentic', 'ai-assisted',
             'ai coding', 'llm coding', 'agent workflow', 'devin', 'lovable', 'bolt.new', 'replit agent']
    if any(w in b for w in tier1):
        score += 3

    # ✅ Tier-2 signals: solo/indie shipping fast (will feel Ranger's value)
    tier2 = ['indie hacker', 'indiehacker', 'indie dev', 'solo founder', 'bootstrapping',
             'ship fast', 'building in public', 'build in public', 'shipped', 'launched my',
             '0 to', 'zero to', 'saas', 'mrr', 'arr', 'side project', 'my app', 'my product',
             'solo dev', 'one-person', 'one person team']
    if any(w in b for w in tier2):
        score += 2

    # ✅ Tier-2 signals: AI product builders (will get the AI-verification loop)
    ai_build = ['building with ai', 'ai builder', 'building ai', 'ai startup', 'llm', 'gpt', 'claude',
                'ai app', 'ai product', 'ai tools', 'automating', 'automation', 'ai founder',
                'building agents', 'agents', 'ai engineer', 'ml engineer']
    if any(w in b for w in ai_build):
        score += 2

    # ✅ Tier-2 signals: founder/builder broadly
    builder = ['founder', 'ceo', 'cofounder', 'co-founder', 'building', 'engineer', 'developer',
               'fullstack', 'full-stack', 'backend', 'frontend', 'dev @', 'software', 'product manager']
    if any(w in b for w in builder):
        score += 1

    # 🎯 Direct QA/testing pain signals (HIGHEST value — feels the exact pain)
    qa_pain = ['qa', 'testing', 'test', 'quality assurance', 'debug', 'bugs', 'verify', 'verification',
               'e2e', 'end to end', 'unit test', 'integration test', 'pr review', 'code review']
    if any(w in b for w in qa_pain):
        score += 3  # triple points — this is THE person

    # ✅ Hackathon/fast shipper (Ranger for demo-day verification)
    if any(w in b for w in ['hackathon', 'hacks', 'winner', 'yc', 'y combinator', 'techstars', 'antler']):
        score += 1

    # Follower credibility bonus
    if followers >= 10000: score += 1
    if followers >= 50000: score += 1

    # ❌ Negative signals: not builders, or wrong persona
    if any(w in b for w in ['airdrop', 'kol manager', 'ambassador', 'moderator', 'not financial advice',
                             'nft collector', 'nft holder', 'hodl', 'moonshot', 'gem hunter',
                             'community manager', 'cm @', 'shilling', 'nfa', 'influencer']):
        score -= 3

    if any(w in b for w in ['journalist', 'reporter', 'newsletter writer', 'media', 'podcast host',
                             'investor only', 'vc only', 'angel only']):
        score -= 1

    return max(score, 0)

# Company/protocol filter
COMPANY_BIO = ['official twitter', 'official account', 'official page', 'rt ≠ endorsement',
               'rt != endorsement', 'join our community', 'our team', 'follow us for',
               'we are the', 'we are a', 'backed by', 'learn more at', 'apply now',
               'the official', 'layer 1', 'layer 2', ' l1 ', ' l2 ']

def is_human(name, bio, handle):
    b = bio.lower()
    n = name.lower()
    # Protocol/company name check
    company_suffixes = {'inc','llc','labs','dao','network','protocol','foundation',
                        'capital','ventures','studio','token','nft','app','io','hq','media'}
    name_words = set(n.split())
    if name_words & company_suffixes:
        return False
    if any(sig in b for sig in COMPANY_BIO):
        return False
    # Known company handles to skip
    SKIP = {'therundownai','thehundreds','kindred_ai','fdotinc','cerebras','reach_eth',
            'seinetwork','layer3','sbf_ftx','solana','base','optimism','carv_official',
            'bluwhaleai','moca_network','astra__nova','lumozorg','fuel_network','shardeum',
            'eigencloud','katana','eclipsefnd','stacks','megaeth','restreamio',
            'buildonlumia','fxnction','catwifhatsolana','playhoneyland','goldskyio','mochi_token',
            'wanderers','runwayml','lovable','saharaai'}
    if handle.lower().lstrip('@') in SKIP:
        return False
    return True

# ── Load and filter ────────────────────────────────────────────────────────────
INPUT  = '$OPENCLAW_HOME/erlich/campaigns/BobbyTwitter-RangerMapping.csv'
OUTPUT = '$OPENCLAW_HOME/erlich/campaigns/Ranger-BobbyFinal.csv'

COLUMNS = ['Handle', 'Name', 'Followers', 'Source', 'ICP Score', 'Tier', 'Bio', 'Verified']

rows = []
total_raw = 0
skipped_followers = 0
skipped_company   = 0

with open(INPUT, newline='', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        total_raw += 1
        followers = parse_followers(r['Followers'])

        # Filter 1: min 500 followers
        if followers < 500:
            skipped_followers += 1
            continue

        # Filter 2: humans only
        if not is_human(r['Name'], r['Bio'], r['Handle']):
            skipped_company += 1
            continue

        icp = ranger_icp_score(r['Bio'], followers, r['Name'])

        # Only keep score >=2 (some builder signal)
        if icp < 2:
            continue

        rows.append({
            'Handle':    r['Handle'],
            'Name':      r['Name'],
            'Followers': r['Followers'],
            'Source':    r['Source'],
            'ICP Score': icp,
            'Tier':      r['Tier'],
            'Bio':       r['Bio'],
            'Verified':  r.get('Verified', ''),
            '_followers_raw': followers,
        })

# Sort: ICP Score desc → Followers desc
rows.sort(key=lambda r: (r['ICP Score'], r['_followers_raw']), reverse=True)

with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=COLUMNS)
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r[k] for k in COLUMNS})

print(f'✅ Done → {OUTPUT}')
print(f'Total input:          {total_raw}')
print(f'Skipped <500 followers: {skipped_followers}')
print(f'Skipped companies:      {skipped_company}')
print(f'Final output:           {len(rows)} targets')
print()

score_dist = Counter(r['ICP Score'] for r in rows)
src_dist   = Counter(r['Source'] for r in rows)
tier_dist  = Counter(r['Tier'] for r in rows)
print(f'By ICP Score: {dict(sorted(score_dist.items(), reverse=True))}')
print(f'By Tier:      {dict(tier_dist)}')
print(f'By Source:    {dict(src_dist)}')
print()
print('🔥 TOP 30:')
print(f'{"Handle":<28} {"Name":<25} {"Followers":<8} {"Score":<6} {"Source"}')
print('-'*100)
for r in rows[:30]:
    print(f"{r['Handle']:<28} {r['Name'][:24]:<25} {r['Followers']:<8} {r['ICP Score']:<6} {r['Source']}")
    print(f"  {r['Bio'][:110]}")
    print()
