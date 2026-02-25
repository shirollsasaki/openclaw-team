"""
Monica Twitter Automation — CLIRichard Growth Engine
Agent: Monica (Content Lead, Claude-powered)
Target: @CLIRichard Twitter account
Strategy: 2x/day, product demos + build-in-public + AI dev engagement
Last updated: C4092 (Feb 25, 2026)
"""

import os
import json
import time
import hmac
import hashlib
import base64
import urllib.parse
import urllib.request
import anthropic
from datetime import datetime, timezone
from pathlib import Path

# ─────────────────────────────────────────────
# CONFIG — fill in @CLIRichard's Twitter API keys
# Store in environment or agent secrets
# ─────────────────────────────────────────────
TWITTER_API_KEY    = os.environ.get('CLIRICHARD_TWITTER_API_KEY', '')
TWITTER_API_SECRET = os.environ.get('CLIRICHARD_TWITTER_API_SECRET', '')
TWITTER_ACCESS_TOKEN   = os.environ.get('CLIRICHARD_ACCESS_TOKEN', '')
TWITTER_ACCESS_SECRET  = os.environ.get('CLIRICHARD_ACCESS_SECRET', '')
ANTHROPIC_API_KEY  = os.environ.get('ANTHROPIC_API_KEY', '')

# Content schedule: 2 posts/day
DAILY_POST_TIMES = ["09:00", "18:00"]  # UTC

# ─────────────────────────────────────────────
# MONICA'S CONTENT IDENTITY (CLIRichard voice)
# ─────────────────────────────────────────────
MONICA_SYSTEM_PROMPT = """You are Monica, the content strategy brain behind @CLIRichard.

@CLIRichard is a developer agent account focused on Claude Code, AI-assisted development, and building autonomous agent workflows. Current: 155 followers. Goal: 1,000.

Your job: Generate high-impact tweets that grow the account.

CONTENT PILLARS (rotate through these):
1. Product demos — "deployed [feature] in [X seconds] using agent + claude code"
2. Build-in-public — "what shipped today / what broke / what's next"  
3. Dev workflow tips — "before/after using agents for [task]"
4. Use-case spotlights — real scenarios where agent deploys saved hours
5. Reactions to AI dev news — add POV to cursor/anthropic/vercel threads

VOICE: Concise, technical, practitioner. No fluff. Developers respect brevity + specificity.

FORMAT RULES:
- Max 250 characters (leave room for engagement)
- No hashtags unless genuinely relevant
- Lead with the outcome/hook, not "i"
- No emojis unless they add meaning
- 2-3 sentences max for single tweets

OUTPUT: Return ONLY the tweet text, nothing else."""

# ─────────────────────────────────────────────
# CONTENT QUEUE (seed with pillar-based prompts)
# ─────────────────────────────────────────────
CONTENT_PROMPTS = [
    "Generate a tweet about a recent win building with Claude Code. Specific, concrete, ~30 words.",
    "Generate a build-in-public tweet about what shipped this week on ClawDeploy. Technical, honest.",
    "Generate a tweet about how AI agents change dev workflow. Practitioner perspective.",
    "Generate a tweet about deploying something with ClawDeploy that would have taken hours manually.",
    "Generate a reaction tweet to the AI coding tools trend (cursor, claude, anthropic). Take a stance.",
    "Generate a tweet about what most dev tools get wrong about agent workflows.",
    "Generate a tweet showcasing a specific ClawDeploy use case. Output-focused.",
]

# ─────────────────────────────────────────────
# TWITTER OAUTH 1.0a
# ─────────────────────────────────────────────
def twitter_oauth(method, url, params={}):
    op = {
        'oauth_consumer_key': TWITTER_API_KEY,
        'oauth_nonce': str(int(time.time() * 1000)),
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': str(int(time.time())),
        'oauth_token': TWITTER_ACCESS_TOKEN,
        'oauth_version': '1.0'
    }
    ap = {**op, **params}
    sp = '&'.join(f'{urllib.parse.quote(k,"~")}={urllib.parse.quote(str(v),"~")}' for k,v in sorted(ap.items()))
    bs = f"{method}&{urllib.parse.quote(url,'~')}&{urllib.parse.quote(sp,'~')}"
    sk = f"{urllib.parse.quote(TWITTER_API_SECRET,'~')}&{urllib.parse.quote(TWITTER_ACCESS_SECRET,'~')}"
    sig = base64.b64encode(hmac.new(sk.encode(), bs.encode(), hashlib.sha1).digest()).decode()
    op['oauth_signature'] = sig
    return 'OAuth ' + ', '.join(f'{k}="{urllib.parse.quote(str(v),"~")}"' for k,v in sorted(op.items()))

def post_tweet(text: str) -> dict:
    """Post tweet via Twitter API v2."""
    url = 'https://api.twitter.com/2/tweets'
    body = json.dumps({"text": text}).encode()
    headers = {
        'Authorization': twitter_oauth('POST', url),
        'Content-Type': 'application/json'
    }
    req = urllib.request.Request(url, body, headers)
    try:
        r = urllib.request.urlopen(req)
        return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode()}

def get_recent_tweets(count=5) -> list:
    """Fetch @CLIRichard's recent tweets to avoid duplicates."""
    user_id = os.environ.get('CLIRICHARD_TWITTER_USER_ID', '')
    if not user_id:
        return []
    url = f'https://api.twitter.com/2/users/{user_id}/tweets'
    params = {'max_results': str(count), 'tweet.fields': 'text,created_at'}
    req = urllib.request.Request(
        f"{url}?{urllib.parse.urlencode(params)}",
        headers={'Authorization': twitter_oauth('GET', url, params)}
    )
    try:
        r = urllib.request.urlopen(req)
        data = json.loads(r.read())
        return [t['text'] for t in data.get('data', [])]
    except:
        return []

# ─────────────────────────────────────────────
# MONICA — GENERATE TWEET
# ─────────────────────────────────────────────
def monica_generate_tweet(prompt: str, recent_tweets: list = []) -> str:
    """Use Claude to generate a tweet as Monica."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    context = ""
    if recent_tweets:
        context = f"\n\nRecent tweets (avoid repeating themes):\n" + "\n".join(f"- {t[:80]}" for t in recent_tweets[:3])
    
    full_prompt = prompt + context
    
    message = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=200,
        system=MONICA_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": full_prompt}]
    )
    
    return message.content[0].text.strip()

# ─────────────────────────────────────────────
# CONTENT QUEUE MANAGER
# ─────────────────────────────────────────────
QUEUE_FILE = Path(__file__).parent / "content_queue.json"

def get_next_prompt() -> str:
    """Rotate through content prompts, track which was used last."""
    if QUEUE_FILE.exists():
        state = json.loads(QUEUE_FILE.read_text())
        idx = (state.get('last_idx', -1) + 1) % len(CONTENT_PROMPTS)
    else:
        idx = 0
    
    QUEUE_FILE.write_text(json.dumps({'last_idx': idx, 'updated': datetime.now(timezone.utc).isoformat()}))
    return CONTENT_PROMPTS[idx]

def log_post(tweet_id: str, text: str):
    """Log posted tweet for record-keeping."""
    log_file = Path(__file__).parent / "posts_log.jsonl"
    entry = {
        "tweet_id": tweet_id,
        "text": text,
        "posted_at": datetime.now(timezone.utc).isoformat()
    }
    with open(log_file, 'a') as f:
        f.write(json.dumps(entry) + '\n')

# ─────────────────────────────────────────────
# MAIN — run Monica's posting cycle
# ─────────────────────────────────────────────
def run_monica_cycle():
    """Monica's tweet generation + posting cycle."""
    print(f"[Monica] {datetime.now(timezone.utc).isoformat()} — starting cycle")
    
    if not TWITTER_API_KEY or not ANTHROPIC_API_KEY:
        print("[Monica] ERROR: Missing API keys. Set CLIRICHARD_TWITTER_API_KEY and ANTHROPIC_API_KEY")
        return
    
    # Get recent tweets to avoid repeating
    recent = get_recent_tweets(5)
    print(f"[Monica] Fetched {len(recent)} recent tweets for context")
    
    # Generate tweet
    prompt = get_next_prompt()
    tweet_text = monica_generate_tweet(prompt, recent)
    print(f"[Monica] Generated tweet: {tweet_text}")
    
    if len(tweet_text) > 280:
        tweet_text = tweet_text[:277] + "..."
    
    # Post
    result = post_tweet(tweet_text)
    if "data" in result:
        tweet_id = result["data"]["id"]
        log_post(tweet_id, tweet_text)
        print(f"[Monica] Posted successfully: {tweet_id}")
    else:
        print(f"[Monica] ERROR posting: {result}")

if __name__ == "__main__":
    run_monica_cycle()
