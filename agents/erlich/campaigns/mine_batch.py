#!/usr/bin/env python3
import urllib.request
import urllib.parse
import json
import sys
import time

API_KEY = "ks_4f504de0b636ac8f442c4bc0ab35e6763f72f16a22451abb88bebae4714fc29d"
BASE_URL = "https://api.koosocial.com/api/v1/search"

def search(query, count=20):
    params = urllib.parse.urlencode({"query": query, "count": count})
    url = f"{BASE_URL}?{params}"
    req = urllib.request.Request(url, headers={"x-api-key": API_KEY})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
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

campaign = sys.argv[1] if len(sys.argv) > 1 else "corners"

CORNERS_EXISTING = {
    "__proper","AvgJoesCrypto","capradavis","blockchainzilla","munchPRMR",
    "696_eth","LukasMikelionis","xdthesmiley","panik_eth","0xvedang",
    "LinasLekavicius","FamKien","lexonthechain","toastonbase","KienNguyen",
    "jacek0x","redhairshanks86","ruggedpikachu","MoneyLord","CyberShakti",
    "KateVassGalerie","UncleHODL","PopPunkOnChain","dippy_eth","acidmandoteth"
}

RANGER_EXISTING = {
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
}

CORNERS_QUERIES = [
    "onchain social curation community Base",
    "web3 community content discovery",
    "Base ecosystem building community",
    "creator monetization onchain content",
    "Farcaster community curation",
    "crypto content discovery curators",
    "community token Base builders",
    "onchain curation platform",
]

RANGER_QUERIES = [
    "SaaS founder shipped product users found bugs",
    "build in public shipped feature production",
    "playwright tests too complex give up",
    "cypress tests brittle hate testing",
    "deployed prod something broke hotfix",
    "vibe coding shipped app broke",
    "solo developer no QA just ship",
    "launched app users reported bug",
]

if campaign == "corners":
    queries = CORNERS_QUERIES
    existing = {x.lower() for x in CORNERS_EXISTING}
    outfile = "$OPENCLAW_HOME/erlich/campaigns/corners_raw.json"
else:
    queries = RANGER_QUERIES
    existing = {x.lower() for x in RANGER_EXISTING}
    outfile = "$OPENCLAW_HOME/erlich/campaigns/ranger_raw.json"

found = {}
for q in queries:
    print(f"Query: {q}", flush=True)
    results = search(q)
    for r in results:
        h = r["handle"]
        if h.lower() in existing:
            continue
        if r["followers"] < 300 or r["followers"] > 200000:
            continue
        key = h.lower()
        if key not in found:
            found[key] = r
            print(f"  NEW: @{r['handle']} ({r['followers']:,}) | {r['tweet'][:100]}", flush=True)
    time.sleep(0.3)

with open(outfile, "w") as f:
    json.dump(list(found.values()), f, indent=2)

print(f"\nTotal new {campaign}: {len(found)}")
print(f"Saved to {outfile}")
