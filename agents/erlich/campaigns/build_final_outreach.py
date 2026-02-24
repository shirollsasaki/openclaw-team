#!/usr/bin/env python3
"""
Final clean outreach list for Ranger — only real individual builders worth DMing.
Input: Ranger-BobbyFinal.csv (score >=4, >=500 followers)
Output: Ranger-OutreachReady.csv
"""
import csv
from collections import Counter

def parse_followers(s):
    s = str(s).strip()
    if 'M' in s: return float(s.replace('M','')) * 1_000_000
    if 'K' in s: return float(s.replace('K','')) * 1_000
    try: return float(s)
    except: return 0

# ── Hard exclude: company/protocol/crypto noise accounts ──────────────────────
HARD_SKIP = {
    # Protocols / chains / company accounts
    'magicnewton','oneanalog','zkvprotocol','bankrbot','vibecodeapp','stitchbygoogle',
    'bunjavascript','daosdotfun','biconomy','inkfinance','pinecone','glbgpt',
    'tempo','ampcode','relay','automatio_ai','onlookdev',  # product accounts not humans
    'kroma_network','reach_eth','figma',  # slipped through before

    # Crypto degens / narrative accounts / KOLs
    'fomomofosol','888_nfts','3dmax_virtuals','manlynft','diamondweb_3','skylineeth',
    'thedefiedge','cryptoteca__','colinmiles','token_works','hoss_ibc',
    'boz_menzalji','0xfreelunch','0xtechminded','mrweb3king','adjastra','azcrypto7',
    'gskrovina','riceriddler','piratee_king','gavishgoyal','who_anon_','navv96',
    'dumbledyor','jasonyeah0503','amansanduja','giantherios','thewizardofpos',
    'singularityhack','shivamsspirit','jonliver90','zhouyaya','vkpatva',
    '0xabhip','3dblurss','sachink80101150',

    # Media / content only (no product)
    'tweetsbytbi','kpmg_eg_uk','boringmarketer','firstadopter','aaditsh',
    'mytechceoo','fonsmans','dremilyanhalt',

    # NFT / collector accounts
    'pupsclub','2kbricktv','marcecko',

    # Company execs where DM is a stretch
    'dankimxyz',  # Coinbase VP listings — not a builder we'd DM
    'gregisenberg',  # great but more of an ideas media brand

    # Not relevant to Ranger ICP
    'rohindhar','moseskagan','the_adprofessor','wadnr','sbf_ftx',
    'byte__ai','teamlurky','karelvuong','provenauthority',
    'businessbarista','tang','typrompts',
}

# ── Bio-level noise filter ─────────────────────────────────────────────────────
NOISE_BIO = [
    'kol manager','airdrop','not financial advice','hodl','community manager',
    'cm @','moderator','shilling','nft holder','nft collector','nft enthusiast',
    'meme coins','tracking narratives','alpha content','crypto without the noise',
    'web3 educator','simplifying blockchain','narratives and threads',
    'marketing specialist','content creator',
]

# ── Load ───────────────────────────────────────────────────────────────────────
rows = []
with open('$OPENCLAW_HOME/erlich/campaigns/Ranger-BobbyFinal.csv') as f:
    for r in csv.DictReader(f):
        handle    = r['Handle'].lstrip('@').lower()
        bio       = r['Bio'].lower()
        score     = int(r['ICP Score'])
        followers = parse_followers(r['Followers'])

        if handle in HARD_SKIP:
            continue
        if score < 4:
            continue
        if any(w in bio for w in NOISE_BIO):
            continue

        rows.append({**r, '_followers_raw': followers})

# Sort: score desc → followers desc
rows.sort(key=lambda r: (int(r['ICP Score']), r['_followers_raw']), reverse=True)

# ── Write clean output ─────────────────────────────────────────────────────────
OUTPATH = '$OPENCLAW_HOME/erlich/campaigns/Ranger-OutreachReady.csv'
COLUMNS = ['Handle','Name','Followers','Source','ICP Score','Tier','Bio','Verified']

with open(OUTPATH, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=COLUMNS)
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r[k] for k in COLUMNS})

print(f'✅ Saved → {OUTPATH}')
print(f'Total clean targets: {len(rows)}')
print()

score_dist = Counter(int(r['ICP Score']) for r in rows)
src_dist   = Counter(r['Source'] for r in rows)
print(f'Score breakdown: {dict(sorted(score_dist.items(), reverse=True))}')
print(f'By source:       {dict(src_dist)}')
print()
print(f'{"Handle":<28} {"Name":<28} {"Followers":<8} {"Score"}')
print('-'*85)
for r in rows:
    print(f"{r['Handle']:<28} {r['Name'][:27]:<28} {r['Followers']:<8} {r['ICP Score']}")
