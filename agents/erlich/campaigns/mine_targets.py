#!/usr/bin/env python3
import urllib.request
import urllib.parse
import json
import sys
import time

API_KEY = "ks_4f504de0b636ac8f442c4bc0ab35e6763f72f16a22451abb88bebae4714fc29d"
BASE_URL = "https://api.koosocial.com/api/v1/search"

CORNERS_EXISTING = set([
    "__proper","AvgJoesCrypto","capradavis","blockchainzilla","munchPRMR",
    "696_eth","LukasMikelionis","xdthesmiley","panik_eth","0xvedang",
    "LinasLekavicius","FamKien","lexonthechain","toastonbase","KienNguyen",
    "jacek0x","redhairshanks86","ruggedpikachu","MoneyLord","CyberShakti",
    "KateVassGalerie","UncleHODL","PopPunkOnChain","dippy_eth","acidmandoteth"
])

RANGER_EXISTING = set([
    "wojakcodes","MarcJSchmidt","BenLesh","ibamarief","VicVijayakumar",
    "tekbog","CoastalFuturist","trashh_dev","jamonholmgren","mmt",
    "RaulJuncoV","0xTib3rius","alexwtlf","adrien_brbr","sarthaktwtt",
    "justoo_digital","Henrylabss","c_aulli","nihdao","xxpaat",
    "siyabuilt","om_patel5","aryanlabde","priyhhhhh","0xCL4R",
    "YashAtreya","aniruddhadak","SeshingPM","tadejstanic","AustinRoy007",
    "Hamzanasirr","kevin_jordan__","rfradin","forgebitz","Jbm_dev",
    "absol_89","bpizzacalla","seergioo_gil","thedevchandra","ShrutiSaagar",
    "mehulmpt","acdlite","valigo","rutu_3","burakeregar",
    "Anubhavhing","kenwheeler","peach2k2","aarondfrancis","DsMatie",
    "Adriksh","SoftEngineer","martinlasek","donnfelker","_saberamani",
    "Princeflexzy0","mj_cobsa","0xIlyy"
])

def search(query, count=20):
    params = urllib.parse.urlencode({"query": query, "count": count})
    url = f"{BASE_URL}?{params}"
    req = urllib.request.Request(url, headers={"x-api-key": API_KEY})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return []
    
    results = []
    try:
        instructions = data["result"]["timeline"]["instructions"]
        for inst in instructions:
            entries = inst.get("entries", [])
            for entry in entries:
                content = entry.get("content", {})
                item_content = content.get("itemContent", {})
                tweet_results = item_content.get("tweet_results", {}).get("result", {})
                if not tweet_results:
                    continue
                user = tweet_results.get("core", {}).get("user_results", {}).get("result", {}).get("legacy", {})
                tweet = tweet_results.get("legacy", {})
                if not user or not tweet:
                    continue
                screen_name = user.get("screen_name","")
                followers = user.get("followers_count", 0)
                full_text = tweet.get("full_text","")
                results.append({
                    "handle": screen_name,
                    "followers": followers,
                    "tweet": full_text[:280]
                })
    except Exception as e:
        print(f"  Parse error: {e}", file=sys.stderr)
    return results

CORNERS_QUERIES = [
    "onchain social curation community Base",
    "web3 community content discovery",
    "Base ecosystem building community",
    "creator monetization onchain content",
    "Farcaster community curation",
    "crypto content discovery curators",
    "community token Base builders",
    "onchain curation platform",
    "Base builder community token rewards",
    "web3 creator economy community rewards",
    "Farcaster Base community token",
    "onchain content creator rewards Base",
    "community curation crypto rewards",
    "Base social community launch",
    "web3 community voting content",
]

RANGER_QUERIES = [
    "SaaS founder shipped product users found bugs",
    "indie hacker launched app first bug report",
    "build in public week deploy shipped feature",
    "playwright tests too hard to write give up",
    "cypress tests brittle slow hate testing",
    "unit tests not enough integration tests missing",
    "deployed prod something broke hotfix",
    "vibe coding shipped app needs testing",
    "solo developer no QA just ship it",
    "hackathon project deployed real users",
    "indiehacker MRR shipped bug users complain",
    "SaaS no QA team testing ourselves",
    "shipped feature production bug regression",
    "solo founder launched app bug production",
    "ship fast break prod fix later",
    "e2e testing too complex skip it",
    "launched SaaS users reported bug",
    "build in public shipping bugs",
    "deployed to production broke something",
    "vibe code production disaster",
]

print("=== CORNERS SEARCHES ===")
corners_found = {}
for q in CORNERS_QUERIES:
    print(f"\nQuery: {q}")
    results = search(q)
    for r in results:
        h = r["handle"].lower()
        if h in [x.lower() for x in CORNERS_EXISTING]:
            continue
        if r["followers"] < 300 or r["followers"] > 200000:
            continue
        key = r["handle"].lower()
        if key not in corners_found:
            corners_found[key] = r
            print(f"  + @{r['handle']} ({r['followers']:,} followers)")
            print(f"    tweet: {r['tweet'][:120]}")
    time.sleep(0.5)

print("\n\n=== RANGER SEARCHES ===")
ranger_found = {}
for q in RANGER_QUERIES:
    print(f"\nQuery: {q}")
    results = search(q)
    for r in results:
        h = r["handle"].lower()
        if h in [x.lower() for x in RANGER_EXISTING]:
            continue
        if r["followers"] < 300 or r["followers"] > 200000:
            continue
        key = r["handle"].lower()
        if key not in ranger_found:
            ranger_found[key] = r
            print(f"  + @{r['handle']} ({r['followers']:,} followers)")
            print(f"    tweet: {r['tweet'][:120]}")
    time.sleep(0.5)

print(f"\n\nSUMMARY:")
print(f"Corners new candidates: {len(corners_found)}")
print(f"Ranger new candidates: {len(ranger_found)}")

# Save raw results
with open("$OPENCLAW_HOME/erlich/campaigns/corners_raw.json","w") as f:
    json.dump(list(corners_found.values()), f, indent=2)

with open("$OPENCLAW_HOME/erlich/campaigns/ranger_raw.json","w") as f:
    json.dump(list(ranger_found.values()), f, indent=2)

print("Raw results saved.")
