#!/usr/bin/env python3
"""
Analyse builder profiles from pre-fetched CSV files (no API calls needed).
Maps them to Early.build / Ranger campaign targets.
Output: campaigns/BobbyTwitter-RangerMapping.csv
"""
import csv, re, os
from collections import Counter

# ── Same category logic as analyse_builders.py ────────────────────────────────
def get_category(bio, label=""):
    b = (bio + " " + label).lower()
    if any(w in b for w in ["devrel","developer relations","developer advocate","ecosystem"]):
        return "DEV ADVOCATES / ECOSYSTEM"
    if any(w in b for w in ["ai agent","agents","building agents","agent framework","autonomous"]):
        return "AI + CRYPTO / AGENTS"
    if any(w in b for w in ["game studio","game dev","onchain game","gaming","nft game"]):
        return "BUILDER / GAMING"
    if any(w in b for w in ["product manager","pm @","product @","head of product","cto","chief technology"]):
        return "PRODUCT / CTO"
    if any(w in b for w in ["marketing","growth","gtm","brand","content creator","kol"]):
        return "MARKETING / BUILDER"
    if any(w in b for w in ["vibe cod","vibecod","vibe-cod"]):
        return "VIBECODER / BUILDER-IN-PUBLIC"
    if any(w in b for w in ["founder","ceo","co-founder","cofounder","building","indie hacker","indie dev","indiehacker"]):
        return "BUILDER-IN-PUBLIC"
    if any(w in b for w in ["smart contract","solidity","move dev","rust","protocol","blockchain dev","web3 dev"]):
        return "BUILDER / CONTRIBUTOR"
    if any(w in b for w in ["defi","onchain","web3","crypto","blockchain","dapp","base ","solana","monad","ethereum","arbitrum"]):
        return "ECOSYSTEM / COMMUNITY"
    if any(w in b for w in ["engineer","developer","dev @","fullstack","full-stack","backend","frontend","software"]):
        return "BUILDER-IN-PUBLIC"
    return "EMERGING BUILDER"

# ── Tier from followers (no tweet data available) ─────────────────────────────
def get_tier_from_followers(followers, bio_score):
    if followers >= 50000 and bio_score >= 3:  return "A"
    if followers >= 10000 and bio_score >= 2:  return "A"
    if followers >= 5000  and bio_score >= 3:  return "A"
    if followers >= 10000:                      return "B"
    if followers >= 2000  and bio_score >= 2:  return "B"
    if followers >= 1000  and bio_score >= 3:  return "B"
    if followers >= 500   and bio_score >= 4:  return "B"
    return "C"

# ── Ranger relevance score (0-5, higher = better fit) ─────────────────────────
def ranger_score(bio, followers, tweets_count):
    b = bio.lower()
    score = 0
    # Strong builder signals
    if any(w in b for w in ["building","built","shipped","launched","app","product","saas","startup"]):
        score += 1
    # Shipping/solo/fast signals (ideal for Ranger)
    if any(w in b for w in ["solo","indie","bootstrapping","zero to","0 to","mvp","ship fast"]):
        score += 1
    # Hackathon or achievement (Ranger appeals to competitive builders)
    if any(w in b for w in ["hackathon","winner","yc","y combinator","techstars","antler"]):
        score += 1
    # AI or modern stack signals
    if any(w in b for w in ["ai","ml","llm","claude","gpt","vibecod","cursor","claude code"]):
        score += 1
    # QA/testing pain signals (directly relevant to Ranger)
    if any(w in b for w in ["qa","testing","test","quality","debug","bugs"]):
        score += 2  # double points for direct relevance
    # Follower credibility
    if followers >= 5000:   score += 1
    if followers >= 20000:  score += 1
    # Active poster
    if tweets_count >= 1000: score += 1
    # Negative signals (remove noisy accounts)
    if any(w in b for w in ["airdrop","kol manager","ambassador","moderator","community manager","reply guy","cm @","not financial advice"]):
        score -= 2
    if any(w in b for w in ["nft collector","nft enthusiast","nft holder","nft lover","hodl","moon","gem","shilling"]):
        score -= 1
    return max(score, 0)

# ── Ranger DM angle ────────────────────────────────────────────────────────────
def get_dm_angle(bio, name, category):
    b = bio.lower()
    if any(w in b for w in ["solo","zero employees","no team","one-person"]):
        return "Solo builder angle — QA without a team"
    if any(w in b for w in ["vibecod","vibe cod","claude code","cursor","ai"]):
        return "AI vibe coder angle — ship fast, break less"
    if any(w in b for w in ["hackathon","winner","hacks"]):
        return "Hackathon winner — ship & verify fast"
    if any(w in b for w in ["bootstrap","bootstrapping","mrr","arr","revenue"]):
        return "Bootstrapper angle — protect revenue with QA"
    if any(w in b for w in ["founder","ceo","cofounder"]):
        return "Founder angle — scale without bugs"
    if any(w in b for w in ["engineer","developer","fullstack","backend","frontend"]):
        return "Dev angle — automate your QA workflow"
    return "Builder angle — general outreach"

# ── Format followers ───────────────────────────────────────────────────────────
def fmt_followers(n):
    if n >= 1000000: return f"{n/1000000:.1f}M"
    if n >= 1000:    return f"{n/1000:.0f}K"
    return str(n)

# ── Load and process CSV files ────────────────────────────────────────────────
CSV_FILES = [
    "$OPENCLAW_HOME/media/inbound/a201b367-ec39-48c3-8d5b-a095730a68a4.csv",
    "$OPENCLAW_HOME/media/inbound/bafdd0a9-7639-4f42-a4c1-f21f82541f7a.csv",
]

SOURCE_LABELS = {
    "$OPENCLAW_HOME/media/inbound/a201b367-ec39-48c3-8d5b-a095730a68a4.csv": "File1-BobbyNetwork",
    "$OPENCLAW_HOME/media/inbound/bafdd0a9-7639-4f42-a4c1-f21f82541f7a.csv": "File2-BobbyFollowers",
}

OUTPATH = "$OPENCLAW_HOME/erlich/campaigns/BobbyTwitter-RangerMapping.csv"

COLUMNS = [
    "Handle", "Name", "Followers", "Source",
    "Category", "Tier", "Ranger Score", "DM Angle",
    "Bio", "Verified"
]

# Deduplicate by handle across both files
seen_handles = set()
all_rows = []

for csv_path in CSV_FILES:
    source = SOURCE_LABELS[csv_path]
    print(f"\n📂 Processing {source}...")
    count = 0
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            handle   = row.get("Username", "").strip().lower()
            if not handle or handle in seen_handles:
                continue
            seen_handles.add(handle)
            
            name      = row.get("Name", "").strip()
            bio       = row.get("Bio", "").strip()
            location  = row.get("Location", "").strip()
            verified  = row.get("Verified", "false").strip().lower() == "true"
            
            try:
                followers = int(row.get("Followers", 0))
            except:
                followers = 0
            try:
                tweets_count = int(row.get("Tweets", 0))
            except:
                tweets_count = 0
            
            # Score
            r_score  = ranger_score(bio, followers, tweets_count)
            category = get_category(bio)
            tier     = get_tier_from_followers(followers, r_score)
            dm_angle = get_dm_angle(bio, name, category)
            
            all_rows.append({
                "Handle":       f"@{handle}",
                "Name":         name,
                "Followers":    fmt_followers(followers),
                "Source":       source,
                "Category":     category,
                "Tier":         tier,
                "Ranger Score": r_score,
                "DM Angle":     dm_angle,
                "Bio":          bio[:150],
                "Verified":     "✓" if verified else "",
                "_followers_raw": followers,
                "_score_raw":     r_score,
            })
            count += 1
    print(f"  → {count} unique profiles loaded")

print(f"\n📊 Total unique profiles: {len(all_rows)}")

# ── Sort: Ranger Score desc, then Followers desc ──────────────────────────────
all_rows.sort(key=lambda r: (r["_score_raw"], r["_followers_raw"]), reverse=True)

# ── Write output ───────────────────────────────────────────────────────────────
with open(OUTPATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=COLUMNS)
    writer.writeheader()
    for row in all_rows:
        writer.writerow({k: row[k] for k in COLUMNS})

print(f"\n✅ Saved → {OUTPATH}")

# ── Summary stats ──────────────────────────────────────────────────────────────
tiers    = Counter(r["Tier"] for r in all_rows)
cats     = Counter(r["Category"] for r in all_rows)
sources  = Counter(r["Source"] for r in all_rows)
score_5p = [r for r in all_rows if r["_score_raw"] >= 5]
score_4p = [r for r in all_rows if 3 <= r["_score_raw"] < 5]
noise    = [r for r in all_rows if r["_score_raw"] <= 1]

print(f"\n📈 Tier breakdown: A={tiers['A']} | B={tiers['B']} | C={tiers['C']}")
print(f"🎯 Ranger Score ≥5 (top targets): {len(score_5p)}")
print(f"✅ Ranger Score 3-4 (good targets): {len(score_4p)}")
print(f"🗑️  Noise (score ≤1): {len(noise)}")
print(f"\n🏷️  Top categories:")
for cat, n in cats.most_common(8):
    print(f"   {cat}: {n}")
print(f"\n📁 By source:")
for src, n in sources.most_common():
    print(f"   {src}: {n}")

print(f"\n🔥 TOP 20 RANGER TARGETS:")
print(f"{'Handle':<25} {'Name':<25} {'Followers':<10} {'Score':<6} {'Tier':<4} {'Angle'}")
print("-" * 100)
for r in all_rows[:20]:
    print(f"{r['Handle']:<25} {r['Name'][:24]:<25} {r['Followers']:<10} {r['_score_raw']:<6} {r['Tier']:<4} {r['DM Angle'][:35]}")
