#!/usr/bin/env python3
"""
Generate early-build-categorised.csv matching the sheet column structure
"""
import csv, re, os, json

def load_api_key():
    env_path = os.path.expanduser("~/.config/env/global.env")
    with open(env_path) as f:
        for line in f:
            if line.strip().startswith("KOO_API_KEY="):
                return line.strip().split("=",1)[1].strip()
    return ""

# ── Sheet columns (in order) ──────────────────────────────────────────────────
COLUMNS = [
    "Name", "Email Address", "Telegram", "X Profile Link", "Github",
    "Personal Website / Portfolio", "EVM Wallet Address", "Shipping Address",
    "What best describes you?", "Experience Level",
    "Which protocols have you built on?", "What interests you most?",
    "What are the top products / protocols you want to work with?",
    "Current employment status", "If employed / part-time, where are you currently working?",
    "What's the best project you've built",
    "Describe it in 2-3 sentences",
    "Do you create technical content?", "If yes, what type?",
    "Where do you post most of your content?",
    "Drop your best piece of content you've made.",
    "What are your current work commitments?", "What are you looking for?",
    "Ideal project timeline",
    # Analysis columns
    "Category", "Followers", "Work Ex", "Tier",
    "Content that works for them", "Engagement levels",
    "Audience & Vibe", "Notes + Engagement Drivers"
]

# ── Segment → category/role mappings ─────────────────────────────────────────
SEG_TO_CATEGORY = {
    "Builder in Public":            "BUILDER-IN-PUBLIC",
    "Vibe Coder / AI Builder":      "VIBECODER / BUILDER-IN-PUBLIC",
    "Web3 / Crypto Builder":        "ECOSYSTEM / COMMUNITY",
    "Hackathon Builder":            "BUILDER / CONTRIBUTOR",
    "Indie Hacker / SaaS":          "BUILDER-IN-PUBLIC",
    "Startup Engineer / CTO":       "DEV ADVOCATES / PRODUCT",
    "Solo Founder / Indie Hacker":  "BUILDER-IN-PUBLIC",
    "Mobile Developer":             "BUILDER / CONTRIBUTOR",
    "Weekend / Side Project Builder":"EMERGING BUILDER",
    "Open Source Builder":          "BUILDER / CONTRIBUTOR",
    "DevRel / Ecosystem":           "DEV ADVOCATES / ECOSYSTEM",
}

SEG_TO_ROLE = {
    "Builder in Public":            "Full-stack developer",
    "Vibe Coder / AI Builder":      "Full-stack developer",
    "Web3 / Crypto Builder":        "Smart contract developer",
    "Hackathon Builder":            "Full-stack developer",
    "Indie Hacker / SaaS":          "Full-stack developer",
    "Startup Engineer / CTO":       "Full-stack developer",
    "Solo Founder / Indie Hacker":  "Full-stack developer",
    "Mobile Developer":             "Full-stack developer",
    "Weekend / Side Project Builder":"Full-stack developer",
    "Open Source Builder":          "Full-stack developer",
    "DevRel / Ecosystem":           "DevRel / Developer Advocate",
}

def get_tier(followers):
    if followers >= 10000: return "A"
    if followers >= 2000:  return "B"
    return "C"

def get_engagement(followers):
    if followers >= 100000: return "~200–1K likes / 30–100 replies / 50K–500K views"
    if followers >= 50000:  return "~100–500 likes / 20–60 replies / 20K–200K views"
    if followers >= 20000:  return "~50–200 likes / 10–30 replies / 5K–50K views"
    if followers >= 10000:  return "~20–80 likes / 5–20 replies / 2K–20K views"
    if followers >= 5000:   return "~10–40 likes / 3–10 replies / 1K–5K views"
    if followers >= 2000:   return "~5–20 likes / 2–5 replies / 500–2K views"
    if followers >= 1000:   return "~2–10 likes / 1–3 replies / 100–500 views"
    return "~1–5 likes / 1–2 replies / 50–200 views"

def infer_content(tweet, segment):
    t = tweet.lower()
    formats = []
    if any(w in t for w in ["thread", "🧵", "1/", "/10", "/15"]):
        formats.append("🧵 threads")
    if any(w in t for w in ["video", "watch", "youtube", "reel", "loom"]):
        formats.append("📹 videos")
    if any(w in t for w in ["day ", "week ", "building", "shipped", "launched", "just "]):
        formats.append("💬 build logs")
    if any(w in t for w in ["lol", "😭", "😂", "💀", "meme", "classic", "relatable"]):
        formats.append("😂 memes/relatable")
    if any(w in t for w in ["mrr", "$", "revenue", "users", "milestone"]):
        formats.append("📊 milestone posts")
    if any(w in t for w in ["how to", "guide", "tutorial", "step", "tips"]):
        formats.append("📝 tutorials/how-to")
    if any(w in t for w in ["open source", "github", "npm", "pr ", "commit"]):
        formats.append("🐙 open source updates")
    if not formats:
        if segment in ["Vibe Coder / AI Builder"]:
            formats = ["💬 short tweets", "😂 vibe/meme posts"]
        elif segment in ["Startup Engineer / CTO"]:
            formats = ["💬 short tweets", "🧵 threads"]
        elif segment in ["Indie Hacker / SaaS"]:
            formats = ["📊 milestone posts", "🧵 threads"]
        elif segment in ["Web3 / Crypto Builder"]:
            formats = ["💬 short tweets", "🧵 ecosystem threads"]
        elif segment in ["Hackathon Builder"]:
            formats = ["💬 short tweets", "📸 demo screenshots"]
        else:
            formats = ["💬 short tweets", "💬 build logs"]
    return ", ".join(formats[:3])

def infer_audience(segment, followers, tweet):
    t = tweet.lower()
    parts = []
    if any(w in t for w in ["india", "indian", "delhi", "mumbai", "bangalore", "bengaluru"]):
        parts.append("Indian builders")
    if any(w in t for w in ["solana", "sol"]):
        parts.append("Solana devs")
    if any(w in t for w in ["base", "coinbase"]):
        parts.append("Base ecosystem")
    if any(w in t for w in ["monad"]):
        parts.append("Monad community")
    if any(w in t for w in ["web3", "onchain", "defi", "nft", "crypto"]):
        parts.append("web3 builders")
    if any(w in t for w in ["cursor", "vibe", "claude", "ai", "agent"]):
        parts.append("AI/vibe coders")
    if any(w in t for w in ["hackathon", "hack"]):
        parts.append("hackathon crowd")
    if not parts:
        seg_audiences = {
            "Builder in Public": "indie hackers + startup devs",
            "Vibe Coder / AI Builder": "AI builders + vibe coders",
            "Indie Hacker / SaaS": "SaaS founders + indie hackers",
            "Startup Engineer / CTO": "engineering teams + senior devs",
            "Hackathon Builder": "hackathon community + event builders",
            "Mobile Developer": "mobile devs + app builders",
            "Web3 / Crypto Builder": "web3 devs + ecosystem builders",
            "Open Source Builder": "open-source devs + contributors",
            "Weekend / Side Project Builder": "side project builders + indie devs",
            "DevRel / Ecosystem": "ecosystem builders + devrel crowd",
            "Solo Founder / Indie Hacker": "solo founders + indie hackers",
        }
        parts.append(seg_audiences.get(segment, "developer community"))
    vibe_map = {
        "Builder in Public": "build-in-public energy",
        "Vibe Coder / AI Builder": "casual vibe coder",
        "Indie Hacker / SaaS": "product-focused, revenue-minded",
        "Startup Engineer / CTO": "technical, senior",
        "Hackathon Builder": "energetic, ships fast",
        "Mobile Developer": "pragmatic, ships clean",
        "Web3 / Crypto Builder": "ecosystem-native",
        "Open Source Builder": "open-source community",
        "Weekend / Side Project Builder": "side project hustle",
        "DevRel / Ecosystem": "community-first",
        "Solo Founder / Indie Hacker": "scrappy, self-sufficient",
    }
    vibe = vibe_map.get(segment, "developer community")
    return f"{' + '.join(parts[:2])} — {vibe}"

def infer_notes(tweet, segment):
    t = tweet.lower()
    notes = []
    if any(w in t for w in ["shipped", "launched", "just released", "went live"]):
        notes.append("Launch posts drive engagement")
    if any(w in t for w in ["day ", "week ", "days of"]):
        notes.append("Daily/weekly build logs get consistent engagement")
    if any(w in t for w in ["mrr", "revenue", "$", "users", "paid"]):
        notes.append("Revenue milestones = high engagement")
    if any(w in t for w in ["built in", "hours", "weekend", "48h", "24h"]):
        notes.append("Fast builds resonate with audience")
    if any(w in t for w in ["open source", "github", "repo", "star"]):
        notes.append("Open-source drops get community traction")
    if any(w in t for w in ["hackathon", "hack", "won", "winner"]):
        notes.append("Hackathon wins get community celebration")
    if any(w in t for w in ["cursor", "claude", "vibe", "ai built"]):
        notes.append("AI stack demos perform well")
    if not notes:
        notes.append("Build-in-public posts consistently engage community")
    return ". ".join(notes[:2])

# ── Load all builders ─────────────────────────────────────────────────────────
# Source 1: early-build-200-targets.md (KooSocial mined, 219)
builders = []
current_seg = "Builder in Public"

with open("early-build-200-targets.md") as f:
    content = f.read()

for line in content.split("\n"):
    m = re.match(r'^## (.+?) \(\d+', line)
    if m:
        current_seg = m.group(1)
    m2 = re.match(r'\|\s*\d+\s*\|\s*@(\w+)\s*\|\s*([\d,]+)\s*\|\s*(\d+)\s*\|\s*(.+?)\s*\|', line)
    if m2:
        handle, followers_str, likes_str, tweet = m2.groups()
        builders.append({
            "handle": handle,
            "followers": int(followers_str.replace(",","")),
            "likes": int(likes_str),
            "tweet": tweet.strip(),
            "segment": current_seg,
            "source": "koo-mined"
        })

# Source 2: Ranger campaign targets (with more context from early-build-ranger-targets.md)
RANGER_SEG = {
    "wojakcodes": ("Startup Engineer / CTO", "Senior dev humor, QA pain posts — relatable format dominates"),
    "MarcJSchmidt": ("Startup Engineer / CTO", "Technical takes on AI code quality get high engagement"),
    "BenLesh": ("Startup Engineer / CTO", "Counterintuitive testing opinions get bookmarks + saves"),
    "ibamarief": ("Startup Engineer / CTO", "QA thought leadership gets shared in engineering Slacks"),
    "VicVijayakumar": ("Startup Engineer / CTO", "Engineering process takes engage well with senior devs"),
    "tekbog": ("Startup Engineer / CTO", "Relatable dev memes get high share rate"),
    "CoastalFuturist": ("Startup Engineer / CTO", "Honest dev takes engage technical audience"),
    "trashh_dev": ("Startup Engineer / CTO", "Friday deploy memes = highest engagement format"),
    "jamonholmgren": ("Startup Engineer / CTO", "Long-form founder takes get saves from engineering leads"),
    "mmt": ("Startup Engineer / CTO", "Relatable process observations engage dev teams"),
    "RaulJuncoV": ("Startup Engineer / CTO", "Math-of-engineering format performs well"),
    "0xTib3rius": ("Startup Engineer / CTO", "Security + vibe coding criticism gets strong engagement"),
    "absol_89": ("Startup Engineer / CTO", "QA-specific content resonates with QA community"),
    "alexwtlf": ("Solo Founder / Indie Hacker", "Launch disaster stories get strong community response"),
    "adrien_brbr": ("Solo Founder / Indie Hacker", "Honest founder takes drive engagement"),
    "sarthaktwtt": ("Solo Founder / Indie Hacker", "Competitor + founder struggle posts engage Indian builders"),
    "justoo_digital": ("Solo Founder / Indie Hacker", "Fast-cycle MVP content resonates with indie hackers"),
    "Henrylabss": ("Solo Founder / Indie Hacker", "Build-in-public updates get consistent engagement"),
    "c_aulli": ("Builder in Public", "Daily build logs engage BIP community"),
    "VladArtym": ("Solo Founder / Indie Hacker", "Revenue-focused founder takes perform well"),
    "its_shubho": ("Solo Founder / Indie Hacker", "Time/efficiency content resonates with solo founders"),
    "xxpaat": ("Solo Founder / Indie Hacker", "Debugging war stories get strong engagement"),
    "nihdao": ("Vibe Coder / AI Builder", "AI-shipped-at-3am posts = viral format for vibe coders"),
    "siyabuilt": ("Builder in Public", "Failure-to-success narrative drives high engagement"),
    "om_patel5": ("Builder in Public", "Young builder stories get outsized community engagement"),
    "aryanlabde": ("Builder in Public", "Indian BIP community responds well to relatable takes"),
    "Rajesh7113": ("Builder in Public", "AI MVP content resonates with Indian dev ecosystem"),
    "priyhhhhh": ("Vibe Coder / AI Builder", "Self-deprecating vibe coder humor gets community love"),
    "0xCL4R": ("Hackathon Builder", "Hackathon wins get community celebration"),
    "YashAtreya": ("Hackathon Builder", "Crypto hackathon content engages web3 builder crowd"),
    "aniruddhadak": ("Hackathon Builder", "Technical hackathon builds get niche community traction"),
    "Jbm_dev": ("Vibe Coder / AI Builder", "Live product announcements + AI agent content perform well"),
    "ShrutiSaagar": ("Builder in Public", "Build journey posts engage aspiring builders"),
}

existing_handles = {b["handle"].lower() for b in builders}

# Read ranger-dms.md for handles + followers
with open("ranger-dms.md") as f:
    ranger_content = f.read()

ranger_blocks = re.findall(r'\*\*(\d+)\.\s+@(\w+)\s+—\s+([\d,]+)\s+followers\*\*.*?\*(.*?)\*\n(.*?)(?=---|\Z)', ranger_content, re.DOTALL)

for num, handle, followers_str, tweet, dm in ranger_blocks:
    if handle.lower() in existing_handles:
        continue
    seg, notes = RANGER_SEG.get(handle, ("Builder in Public", "Build-in-public posts consistently engage community"))
    builders.append({
        "handle": handle,
        "followers": int(followers_str.replace(",","")),
        "likes": 5,
        "tweet": tweet.strip()[:200],
        "segment": seg,
        "source": "ranger-campaign"
    })
    existing_handles.add(handle.lower())

print(f"Total builders to categorise: {len(builders)}")

# ── Build CSV rows ────────────────────────────────────────────────────────────
rows = []
for b in builders:
    handle = b["handle"]
    followers = b["followers"]
    segment = b["segment"]
    tweet = b["tweet"]

    tier = get_tier(followers)
    category = SEG_TO_CATEGORY.get(segment, "BUILDER-IN-PUBLIC")
    role = SEG_TO_ROLE.get(segment, "Full-stack developer")
    engagement = get_engagement(followers)
    content = infer_content(tweet, segment)
    audience = infer_audience(segment, followers, tweet)

    # Notes: use ranger-specific notes if available, else infer
    if handle in RANGER_SEG:
        notes = RANGER_SEG[handle][1]
    else:
        notes = infer_notes(tweet, segment)

    # Work Ex: infer from tweet / segment
    workex_map = {
        "Startup Engineer / CTO": "Engineer / Dev",
        "Solo Founder / Indie Hacker": "Indie hacker, solo founder",
        "Builder in Public": "Builder, shipping in public",
        "Vibe Coder / AI Builder": "Vibe coder / AI builder",
        "Hackathon Builder": "Hackathon builder",
        "Web3 / Crypto Builder": "Web3 / onchain dev",
        "Indie Hacker / SaaS": "Indie hacker, SaaS founder",
        "Mobile Developer": "Mobile developer",
        "Weekend / Side Project Builder": "Side project builder",
        "Open Source Builder": "Open source contributor",
        "DevRel / Ecosystem": "DevRel / Ecosystem",
    }
    workex = workex_map.get(segment, "Developer")

    row = {col: "" for col in COLUMNS}
    row["X Profile Link"] = f"https://x.com/{handle}"
    row["What best describes you?"] = role
    row["Category"] = category
    row["Followers"] = f"{followers:,}"
    row["Work Ex"] = workex
    row["Tier"] = tier
    row["Content that works for them"] = content
    row["Engagement levels"] = engagement
    row["Audience & Vibe"] = audience
    row["Notes + Engagement Drivers"] = notes
    rows.append(row)

# ── Write CSV ─────────────────────────────────────────────────────────────────
outpath = "early-build-categorised.csv"
with open(outpath, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=COLUMNS)
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ Saved {len(rows)} rows to {outpath}")

# Summary
from collections import Counter
tiers = Counter(r["Tier"] for r in rows)
cats = Counter(r["Category"] for r in rows)
print(f"\nTier breakdown: A={tiers['A']}, B={tiers['B']}, C={tiers['C']}")
print("\nCategory breakdown:")
for cat, count in cats.most_common():
    print(f"  {cat}: {count}")
