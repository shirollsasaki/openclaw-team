#!/usr/bin/env python3
"""
Pull real KooSocial profile + recent tweet data for each builder
and generate the Grok-style analysis table as CSV.
"""
import csv, re, os, json, requests, time
from collections import defaultdict

# ── API setup ─────────────────────────────────────────────────────────────────
def load_key():
    with open(os.path.expanduser("~/.config/env/global.env")) as f:
        for line in f:
            if line.strip().startswith("KOO_API_KEY="):
                return line.strip().split("=",1)[1].strip()
    return ""

API_KEY = load_key()
BASE    = "https://api.koosocial.com/api/v1"
HEADERS = {"x-api-key": API_KEY}

def koo_get(endpoint, params, retries=2):
    for attempt in range(retries + 1):
        try:
            r = requests.get(f"{BASE}/{endpoint}", params=params, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                return r.json()
            time.sleep(1)
        except Exception as e:
            time.sleep(2)
    return {}

# ── Parse user profile ────────────────────────────────────────────────────────
def parse_user(data):
    try:
        u = data["result"]["data"]["user"]["result"]
        core   = u.get("core", {})
        legacy = u.get("legacy", {})
        loc    = u.get("location", {}).get("location", "")
        return {
            "name":      core.get("name", "—").split("(")[0].strip().split("\u200b")[0].strip(),
            "bio":       legacy.get("description", ""),
            "followers": legacy.get("followers_count", 0),
            "following": legacy.get("friends_count", 0),
            "tweets":    legacy.get("statuses_count", 0),
            "media":     legacy.get("media_count", 0),
            "location":  loc,
            "verified":  u.get("is_blue_verified", False),
            "label":     u.get("affiliates_highlighted_label", {}).get("label", {}).get("description", ""),
        }
    except:
        return None

# ── Parse recent tweets for engagement ───────────────────────────────────────
def parse_tweets(data):
    tweets = []
    try:
        instructions = data.get("result", {}).get("timeline", {}).get("instructions", [])
        for instr in instructions:
            for e in instr.get("entries", []):
                content = e.get("content", {})
                items_to_check = []
                if content.get("__typename") == "TimelineTimelineItem":
                    items_to_check.append(content.get("itemContent", {}))
                elif content.get("__typename") == "TimelineTimelineModule":
                    for it in content.get("items", []):
                        items_to_check.append(it.get("item", {}).get("itemContent", {}))
                for item in items_to_check:
                    if item.get("itemType") != "TimelineTweet":
                        continue
                    raw   = item.get("tweet_results", {}).get("result", {})
                    tweet = raw.get("tweet", raw)
                    tl    = tweet.get("legacy", {})
                    if not tl:
                        continue
                    tweets.append({
                        "text":       tl.get("full_text", ""),
                        "likes":      tl.get("favorite_count", 0),
                        "replies":    tl.get("reply_count", 0),
                        "retweets":   tl.get("retweet_count", 0),
                        "views":      int(tweet.get("views", {}).get("count", 0) or 0),
                        "has_media":  bool(tl.get("entities", {}).get("media")),
                        "is_reply":   bool(tl.get("in_reply_to_status_id_str")),
                        "is_retweet": tl.get("full_text","").startswith("RT @"),
                    })
    except:
        pass
    return tweets

# ── Determine category from bio + tweets ─────────────────────────────────────
def get_category(bio, tweets_text, label):
    b = (bio + " " + tweets_text + " " + label).lower()
    if any(w in b for w in ["devrel","developer relations","developer advocate","ecosystem"]):
        return "DEV ADVOCATES / ECOSYSTEM"
    if any(w in b for w in ["ai agent","agents","building agents","agent framework"]):
        return "AI + CRYPTO / AGENTS"
    if any(w in b for w in ["game studio","game dev","onchain game","gaming","nft game"]):
        return "BUILDER / GAMING"
    if any(w in b for w in ["product manager","pm @","product @","head of product"]):
        return "PRODUCT / COMMUNITY"
    if any(w in b for w in ["marketing","growth","gtm","brand","content creator"]):
        return "MARKETING / BUILDER"
    if any(w in b for w in ["vibe cod","vibecod","vibe-cod"]):
        return "VIBECODER / BUILDER-IN-PUBLIC"
    if any(w in b for w in ["founder","ceo","co-founder","cofounder","building","indie hacker","indie dev","indiehacker"]):
        return "BUILDER-IN-PUBLIC"
    if any(w in b for w in ["smart contract","solidity","move dev","rust","protocol"]):
        return "BUILDER / CONTRIBUTOR"
    if any(w in b for w in ["defi","onchain","web3","crypto","blockchain","dapp","base ","solana","monad","ethereum","arbitrum"]):
        return "ECOSYSTEM / COMMUNITY"
    if any(w in b for w in ["engineer","developer","dev @","fullstack","full-stack","backend","frontend"]):
        return "BUILDER-IN-PUBLIC"
    return "EMERGING BUILDER"

# ── Infer content strengths ───────────────────────────────────────────────────
def get_content_strengths(tweets, media_count):
    if not tweets:
        return "💬"
    
    has_media   = sum(1 for t in tweets if t["has_media"])
    is_reply    = sum(1 for t in tweets if t["is_reply"] and not t["is_retweet"])
    long_tweets = sum(1 for t in tweets if len(t["text"]) > 180 and not t["is_retweet"])
    meme_words  = sum(1 for t in tweets if any(w in t["text"].lower() for w in ["lol","😭","💀","😂","lmao","bruh","💀","🤣","ngl","fr fr","imo","rn"]))
    thread_hints= sum(1 for t in tweets if "1/" in t["text"] or "🧵" in t["text"] or "/10" in t["text"] or "thread" in t["text"].lower())
    
    total = len([t for t in tweets if not t["is_retweet"]]) or 1
    
    strengths = []
    if thread_hints > 1:           strengths.append("🧵 threads")
    if has_media / total > 0.25:   strengths.append("📹 videos/media" if media_count > 200 else "📸 images")
    if meme_words / total > 0.15:  strengths.append("😂 memes/shitposts")
    if long_tweets / total > 0.2:  strengths.append("📝 long-form")
    if is_reply / total > 0.4:     strengths.append("💬 reply-heavy")
    if not strengths:              strengths.append("💬 short tweets")
    
    # Add ⭐ if any tweet gets >50 likes
    top_likes = max((t["likes"] for t in tweets), default=0)
    if top_likes > 50:             strengths.append("⭐ high-engagement")
    
    return ", ".join(strengths[:3])

# ── Tier from engagement rate ─────────────────────────────────────────────────
def get_tier(followers, avg_likes, avg_views):
    if followers == 0:
        return "C"
    eng_rate = avg_likes / followers if followers > 0 else 0
    if followers >= 50000 and avg_likes >= 100:  return "A"
    if followers >= 10000 and avg_likes >= 30:   return "A"
    if followers >= 5000  and avg_likes >= 15:   return "A"
    if followers >= 10000:                        return "B"
    if followers >= 2000  and avg_likes >= 5:    return "B"
    if followers >= 2000:                         return "B"
    if avg_likes >= 10:                           return "B"
    return "C"

# ── Audience & Vibe ───────────────────────────────────────────────────────────
def get_audience(bio, location, category, tweets):
    b   = bio.lower()
    loc = location.lower()
    
    ecosystems = []
    if any(w in b for w in ["monad"]): ecosystems.append("Monad")
    if any(w in b for w in ["base ","@base","coinbase"]): ecosystems.append("Base")
    if any(w in b for w in ["solana","sol"]): ecosystems.append("Solana")
    if any(w in b for w in ["arbitrum","optimism","scroll"]): ecosystems.append("L2")
    if any(w in b for w in ["ethereum","eth ","evm"]): ecosystems.append("Ethereum")
    
    geo = ""
    if any(w in loc for w in ["india","delhi","mumbai","bangalore","bengaluru","pune","hyderabad","india"]):
        geo = "Indian "
    elif any(w in loc for w in ["us","new york","san francisco","london","berlin","singapore"]):
        geo = ""
    
    vibe_map = {
        "DEV ADVOCATES / ECOSYSTEM": "professional DevRel energy",
        "AI + CRYPTO / AGENTS":      "AI-native, agent-first energy",
        "BUILDER / GAMING":          "game studio founder energy",
        "PRODUCT / COMMUNITY":       "product-minded, community-first",
        "MARKETING / BUILDER":       "growth-focused, strategic",
        "VIBECODER / BUILDER-IN-PUBLIC": "casual vibe coder",
        "BUILDER-IN-PUBLIC":         "build-in-public hustle",
        "BUILDER / CONTRIBUTOR":     "technical, open-source energy",
        "ECOSYSTEM / COMMUNITY":     "ecosystem-native",
        "EMERGING BUILDER":          "early-stage, learning-in-public",
        "CONTENT CREATOR":           "content-first builder",
    }
    vibe = vibe_map.get(category, "developer energy")
    
    eco_str = "/".join(ecosystems[:2]) + " devs" if ecosystems else "developer community"
    return f"{geo}{eco_str} + {'hackathon' if 'hackathon' in b else 'builder'} crowd — {vibe}"

# ── Description from bio ──────────────────────────────────────────────────────
def get_description(bio, label, name):
    # Prefer affiliation label over bio
    if label:
        return label[:80]
    # Clean and shorten bio
    bio_clean = re.sub(r'https?://\S+', '', bio).strip()
    bio_clean = re.sub(r'\s+', ' ', bio_clean)
    # Remove emojis roughly
    bio_clean = re.sub(r'[^\x00-\x7F]+', ' ', bio_clean).strip()
    words = bio_clean.split()
    return " ".join(words[:12]) if words else "Builder"

# ── Engagement notes ──────────────────────────────────────────────────────────
def get_notes(tweets, category, bio):
    if not tweets:
        return "Low activity — limited data"
    
    orig = [t for t in tweets if not t["is_retweet"]]
    if not orig:
        return "Mostly retweets — low original content"
    
    # Find top performing tweet
    top = max(orig, key=lambda t: t["likes"] + t["replies"]*2)
    top_text = top["text"][:80].replace("\n"," ")
    
    avg_likes   = sum(t["likes"]   for t in orig) / len(orig)
    avg_replies = sum(t["replies"] for t in orig) / len(orig)
    
    notes = []
    
    media_tweets = [t for t in orig if t["has_media"]]
    media_likes  = sum(t["likes"] for t in media_tweets) / len(media_tweets) if media_tweets else 0
    text_likes   = sum(t["likes"] for t in orig if not t["has_media"]) / max(len([t for t in orig if not t["has_media"]]),1)
    
    if media_likes > text_likes * 1.5:
        notes.append("Media posts outperform text")
    
    reply_tweets = [t for t in orig if t["is_reply"]]
    if len(reply_tweets) > len(orig) * 0.5:
        notes.append("Reply-heavy account — conversation driver")
    
    if avg_likes < 3:
        notes.append("Low engagement — early/casual account")
    elif avg_likes > 50:
        notes.append("High engagement — established voice")
    
    meme_tweets = [t for t in orig if any(w in t["text"].lower() for w in ["lol","😭","💀","😂","lmao"])]
    if meme_tweets:
        ml = sum(t["likes"] for t in meme_tweets) / len(meme_tweets)
        if ml > avg_likes * 1.3:
            notes.append("Meme/relatable posts outperform")
    
    if not notes:
        notes.append(f"Top post: \"{top_text[:60]}...\"")
    
    return ". ".join(notes[:2])

# ── Load all handles ──────────────────────────────────────────────────────────
handles_segments = {}

# From early-build-200-targets.md
current_seg = "Builder in Public"
with open("early-build-200-targets.md") as f:
    for line in f:
        m = re.match(r'^## (.+?) \(\d+', line)
        if m: current_seg = m.group(1)
        m2 = re.match(r'\|\s*\d+\s*\|\s*@(\w+)\s*\|\s*([\d,]+)', line)
        if m2:
            h = m2.group(1)
            if h.lower() not in handles_segments:
                handles_segments[h.lower()] = (h, current_seg)

# From ranger-dms.md
with open("ranger-dms.md") as f:
    for line in f:
        m = re.match(r'\*\*\d+\.\s+@(\w+)\s+—', line)
        if m:
            h = m.group(1)
            if h.lower() not in handles_segments:
                handles_segments[h.lower()] = (h, "Startup Engineer / CTO")

all_handles = list(handles_segments.values())
print(f"Total handles to analyse: {len(all_handles)}")

# ── Run analysis ──────────────────────────────────────────────────────────────
COLUMNS = [
    "Name", "Handle", "Category", "Followers",
    "Content Strengths", "Description", "Tier",
    "Avg Engagement (Likes / Replies / Views)",
    "Audience & Vibe", "Notes + Engagement Drivers"
]

outpath = "early-build-analysed.csv"

# Support resume: check which handles already done
done_handles = set()
if os.path.exists(outpath):
    with open(outpath, newline="", encoding="utf-8") as _f:
        for _row in csv.DictReader(_f):
            h = _row.get("Handle", "").lstrip("@").lower()
            if h:
                done_handles.add(h)
    print(f"Resuming — {len(done_handles)} handles already in CSV")

# Open CSV in append mode (write header only if new file)
_csv_file = open(outpath, "a", newline="", encoding="utf-8")
_writer = csv.DictWriter(_csv_file, fieldnames=COLUMNS)
if not done_handles:  # new file
    _writer.writeheader()
    _csv_file.flush()

rows = []
errors = []

for i, (handle, default_seg) in enumerate(all_handles):
    if handle.lower() in done_handles:
        print(f"[{i+1}/{len(all_handles)}] @{handle}... ⏭️  already done")
        continue
    print(f"[{i+1}/{len(all_handles)}] @{handle}...", end=" ", flush=True)
    
    # 1. Get profile
    user_data  = koo_get("user", {"username": handle})
    profile    = parse_user(user_data)
    
    if not profile:
        print("❌ no profile")
        errors.append(handle)
        _row = {
            "Name": "—", "Handle": f"@{handle}",
            "Category": "EMERGING BUILDER", "Followers": "?",
            "Content Strengths": "—", "Description": "Profile not found",
            "Tier": "C", "Avg Engagement (Likes / Replies / Views)": "—",
            "Audience & Vibe": "—", "Notes + Engagement Drivers": "Could not fetch profile"
        }
        rows.append(_row)
        _writer.writerow(_row)
        _csv_file.flush()
        time.sleep(0.3)
        continue
    
    # 2. Get recent tweets
    tweet_data = koo_get("search", {"query": f"from:{handle} -is:retweet", "count": 20})
    tweets     = parse_tweets(tweet_data)
    
    # 3. Compute metrics
    orig_tweets = [t for t in tweets if not t["is_retweet"]]
    avg_likes   = sum(t["likes"]   for t in orig_tweets) / len(orig_tweets) if orig_tweets else 0
    avg_replies = sum(t["replies"] for t in orig_tweets) / len(orig_tweets) if orig_tweets else 0
    avg_views   = sum(t["views"]   for t in orig_tweets) / len(orig_tweets) if orig_tweets else 0
    
    tweets_text = " ".join(t["text"][:100] for t in orig_tweets[:10])
    
    # 4. Build row
    followers  = profile["followers"]
    category   = get_category(profile["bio"], tweets_text, profile["label"])
    content    = get_content_strengths(orig_tweets, profile["media"])
    tier       = get_tier(followers, avg_likes, avg_views)
    audience   = get_audience(profile["bio"], profile["location"], category, orig_tweets)
    description= get_description(profile["bio"], profile["label"], profile["name"])
    notes      = get_notes(orig_tweets, category, profile["bio"])
    
    # Format engagement
    if orig_tweets:
        eng = f"~{int(avg_likes)} likes / {int(avg_replies)} replies / {int(avg_views/1000)}K views"
    else:
        eng = "No recent posts"
    
    # Format followers
    if followers >= 1000000:
        fol_str = f"{followers/1000000:.1f}M"
    elif followers >= 1000:
        fol_str = f"{followers/1000:.0f}K"
    else:
        fol_str = str(followers)
    
    name = profile["name"] or "—"
    # Clean emoji from name for CSV
    name_clean = re.sub(r'[^\x00-\x7F]+', '', name).strip() or handle
    
    _row = {
        "Name":         name_clean,
        "Handle":       f"@{handle}",
        "Category":     category,
        "Followers":    fol_str,
        "Content Strengths": content,
        "Description":  description[:100],
        "Tier":         tier,
        "Avg Engagement (Likes / Replies / Views)": eng,
        "Audience & Vibe": audience,
        "Notes + Engagement Drivers": notes,
    }
    rows.append(_row)
    _writer.writerow(_row)
    _csv_file.flush()
    
    print(f"✅ {fol_str} followers | Tier {tier} | {category}")
    time.sleep(0.35)  # rate limit safety

_csv_file.close()

# ── Final summary ─────────────────────────────────────────────────────────────
total_in_csv = len(done_handles) + len(rows)
print(f"\n✅ Saved {total_in_csv} rows → {outpath} ({len(rows)} new this run)")
print(f"Errors this run: {len(errors)} handles could not be fetched: {errors[:10]}")

from collections import Counter
tiers = Counter(r["Tier"] for r in rows)
cats  = Counter(r["Category"] for r in rows)
print(f"Tier A={tiers['A']} B={tiers['B']} C={tiers['C']}")
print("Categories:", dict(cats.most_common(5)))
print(f"DONE")

from collections import Counter
tiers = Counter(r["Tier"] for r in rows)
cats  = Counter(r["Category"] for r in rows)
print(f"Tier A={tiers['A']} B={tiers['B']} C={tiers['C']}")
print("Categories:", dict(cats.most_common(5)))
