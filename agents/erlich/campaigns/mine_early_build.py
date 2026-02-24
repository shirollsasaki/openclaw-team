#!/usr/bin/env python3
"""
Mine 200 Early.build builder targets via KooSocial API
"""
import json, os, requests, time
from datetime import datetime

def load_api_key():
    # Try env first
    key = os.environ.get("KOO_API_KEY", "")
    if key:
        return key
    # Fall back to reading global.env file directly
    try:
        env_path = os.path.expanduser("~/.config/env/global.env")
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("KOO_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except:
        pass
    return ""

API_KEY = load_api_key()
BASE = "https://api.koosocial.com/api/v1"
HEADERS = {"x-api-key": API_KEY}

EXISTING_HANDLES = set([
    "wojakcodes","MarcJSchmidt","BenLesh","ibamarief","VicVijayakumar","tekbog",
    "CoastalFuturist","trashh_dev","jamonholmgren","mmt","RaulJuncoV","0xTib3rius",
    "absol_89","siyabuilt","om_patel5","aryanlabde","Rajesh7113","priyhhhhh",
    "alexwtlf","adrien_brbr","sarthaktwtt","justoo_digital","Henrylabss","c_aulli",
    "VladArtym","its_shubho","xxpaat","nihdao","0xCL4R","YashAtreya","aniruddhadak",
    "Jbm_dev","ShrutiSaagar","SeshingPM","tadejstanic","AustinRoy007","Hamzanasirr",
    "kevin_jordan__","rfradin","forgebitz","bpizzacalla","seergioo_gil","thedevchandra",
    "mehulmpt","acdlite","valigo","rutu_3","burakeregar","Anubhavhing","kenwheeler",
    "peach2k2","aarondfrancis","DsMatie","Adriksh","SoftEngineer","martinlasek",
    "donnfelker","_saberamani","Princeflexzy0","mj_cobsa","0xIlyy","guetteman",
])

SEARCHES = [
    ("build in public shipped saas product founder", "Solo Founder / Build-in-Public"),
    ("vibe coding deployed live app indie hacker", "Vibe Coder / AI Builder"),
    ("indie hacker MRR shipped product users", "Indie Hacker / SaaS"),
    ("hackathon built shipped developer project", "Hackathon Builder"),
    ("weekend project shipped launched developer", "Weekend Builder"),
    ("solo founder building saas startup 2025", "Solo Founder"),
    ("cursor supabase vercel built shipped app", "AI Stack Builder"),
    ("building on base solana developer shipped", "Web3 Builder"),
    ("just launched product developer startup", "Early Stage Founder"),
    ("indie dev indiehacker product shipped 2025", "Indie Dev"),
    ("vibe coded app deployed production bugs", "Vibe Coder"),
    ("shipped my app users feedback indie", "Builder in Public"),
    ("built with AI cursor claude deployed", "AI Builder"),
    ("open source shipped product developer", "Open Source Builder"),
    ("side project launched users paying", "Side Project Builder"),
]

def parse_entries(data):
    results = []
    try:
        instructions = data.get("result", {}).get("timeline", {}).get("instructions", [])
        for instr in instructions:
            entries = instr.get("entries", [])
            for e in entries:
                try:
                    content = e.get("content", {})
                    # Handle both TimelineTimelineItem and nested module items
                    items_to_check = []
                    if content.get("__typename") == "TimelineTimelineItem":
                        items_to_check.append(content.get("itemContent", {}))
                    elif content.get("__typename") == "TimelineTimelineModule":
                        for it in content.get("items", []):
                            items_to_check.append(it.get("item", {}).get("itemContent", {}))

                    for item in items_to_check:
                        if item.get("itemType") != "TimelineTweet":
                            continue
                        # Navigate: tweet_results.result (may have nested "tweet" key for visibility results)
                        raw = item.get("tweet_results", {}).get("result", {})
                        tweet = raw.get("tweet", raw)  # TweetWithVisibilityResults wraps in "tweet"

                        user_legacy = tweet.get("core", {}).get("user_results", {}).get("result", {}).get("legacy", {})
                        tweet_legacy = tweet.get("legacy", {})

                        handle = user_legacy.get("screen_name", "")
                        if not handle:
                            continue
                        followers = user_legacy.get("followers_count", 0)
                        text = tweet_legacy.get("full_text", "")
                        likes = tweet_legacy.get("favorite_count", 0)

                        if followers < 200:
                            continue
                        if likes < 2:
                            continue
                        if handle.lower() in [h.lower() for h in EXISTING_HANDLES]:
                            continue

                        results.append({
                            "handle": handle,
                            "followers": followers,
                            "likes": likes,
                            "tweet": text[:200].replace("\n", " ")
                        })
                except:
                    continue
    except Exception as ex:
        print(f"  Parse error: {ex}")
    return results

def search(query, count=20):
    try:
        r = requests.get(
            f"{BASE}/search",
            params={"query": query, "count": count},
            headers=HEADERS,
            timeout=15
        )
        return r.json()
    except Exception as e:
        print(f"  Error: {e}")
        return {}

def classify_segment(tweet_text, default_segment):
    text = tweet_text.lower()
    if any(w in text for w in ["solana", "base", "ethereum", "web3", "defi", "nft", "onchain", "crypto", "dapp"]):
        return "Web3 Builder"
    if any(w in text for w in ["hackathon", "24hr", "48hr", "48 hours", "24 hours"]):
        return "Hackathon Builder"
    if any(w in text for w in ["cursor", "claude", "v0", "replit", "copilot", "vibe cod"]):
        return "Vibe Coder / AI Builder"
    if any(w in text for w in ["mrr", "revenue", "customers", "paying users", "arr"]):
        return "Indie Hacker / SaaS"
    if any(w in text for w in ["weekend", "side project", "nights and weekends"]):
        return "Weekend Builder"
    return default_segment

all_targets = {}  # handle -> {handle, followers, tweet, segment}

print(f"🚀 Mining Early.build targets via KooSocial API")
print(f"   Existing handles excluded: {len(EXISTING_HANDLES)}")
print(f"   Searches planned: {len(SEARCHES)}")
print()

for query, segment in SEARCHES:
    print(f"🔍 Searching: \"{query[:50]}...\"")
    data = search(query, count=20)
    entries = parse_entries(data)
    new = 0
    for e in entries:
        h = e["handle"].lower()
        if h not in all_targets and h not in [x.lower() for x in EXISTING_HANDLES]:
            all_targets[h] = {**e, "segment": classify_segment(e["tweet"], segment)}
            new += 1
    print(f"   Found {new} new targets (total: {len(all_targets)})")
    time.sleep(0.5)  # small delay between requests

print(f"\n✅ Total unique targets: {len(all_targets)}")

# Sort by followers desc
targets_list = sorted(all_targets.values(), key=lambda x: x["followers"], reverse=True)

# Group by segment
segments = {}
for t in targets_list:
    seg = t["segment"]
    if seg not in segments:
        segments[seg] = []
    segments[seg].append(t)

# Write output
now = datetime.now().strftime("%Y-%m-%d")
out = f"""# Early.build — Builder Targets
## Mined: {now}
## Total: {len(targets_list)} unique builders

## Summary
| Segment | Count |
|---------|-------|
"""
for seg, items in segments.items():
    out += f"| {seg} | {len(items)} |\n"

out += f"\n---\n\n"

for seg, items in segments.items():
    out += f"## {seg} ({len(items)} builders)\n\n"
    out += "| # | Handle | Followers | Likes | Signal Tweet |\n"
    out += "|---|--------|-----------|-------|--------------|\n"
    for i, t in enumerate(items, 1):
        tweet_short = t['tweet'][:120].replace("|", "/")
        out += f"| {i} | @{t['handle']} | {t['followers']:,} | {t['likes']} | {tweet_short} |\n"
    out += "\n"

outpath = "$OPENCLAW_HOME/erlich/campaigns/early-build-200-targets.md"
with open(outpath, "w") as f:
    f.write(out)

print(f"\n📄 Saved to: {outpath}")
print(f"Total builders: {len(targets_list)}")
