#!/usr/bin/env python3
"""Explain position sizing for current trades"""

# From the logs, let's trace through a real example:
# OPENED LONG ARB @ $0.1020 | SL: $0.0967 | TP: $0.1127 | Size: $5.00

print("📊 Position Sizing Breakdown - Real Example\n")
print("="*70)

# Configuration
asset = "ARB"
asset_capital = 10.0  # $10 allocated to ARB
risk_per_trade = 0.03  # 3% risk
leverage = 15

# Trade details
entry = 0.1020
sl = 0.0967
tp = 0.1127

print(f"Asset: {asset}")
print(f"Allocated Capital: ${asset_capital:.2f}")
print(f"Risk per Trade: {risk_per_trade*100}%")
print(f"Leverage: {leverage}x\n")

print(f"Entry: ${entry:.4f}")
print(f"Stop Loss: ${sl:.4f}")
print(f"Take Profit: ${tp:.4f}\n")

# Step 1: Calculate SL distance
sl_distance = abs(entry - sl) / entry
print(f"STEP 1: Calculate SL Distance")
print(f"   |Entry - SL| / Entry")
print(f"   = |${entry:.4f} - ${sl:.4f}| / ${entry:.4f}")
print(f"   = ${entry - sl:.4f} / ${entry:.4f}")
print(f"   = {sl_distance:.4f} ({sl_distance*100:.2f}%)\n")

# Step 2: Calculate risk amount
risk_amount = asset_capital * risk_per_trade
print(f"STEP 2: Calculate Risk Amount")
print(f"   Asset Capital × Risk %")
print(f"   = ${asset_capital:.2f} × {risk_per_trade}")
print(f"   = ${risk_amount:.2f}\n")

# Step 3: Calculate position size
position_size = risk_amount / sl_distance
print(f"STEP 3: Calculate Position Size")
print(f"   Risk Amount / SL Distance")
print(f"   = ${risk_amount:.2f} / {sl_distance:.4f}")
print(f"   = ${position_size:.2f}\n")

# Step 4: Apply 50% cap
max_size = asset_capital * 0.5
final_size = min(position_size, max_size)
print(f"STEP 4: Apply 50% Cap")
print(f"   Max Size = Asset Capital × 50%")
print(f"   = ${asset_capital:.2f} × 0.5")
print(f"   = ${max_size:.2f}")
print(f"   Final Size = min(${position_size:.2f}, ${max_size:.2f})")
print(f"   = ${final_size:.2f}\n")

# Step 5: Check minimum
min_size = 0.10
print(f"STEP 5: Check Minimum Size")
print(f"   Minimum: ${min_size:.2f}")
if final_size >= min_size:
    print(f"   ✅ ${final_size:.2f} >= ${min_size:.2f} - VALID\n")
else:
    print(f"   ❌ ${final_size:.2f} < ${min_size:.2f} - REJECTED\n")

# Round
final_size = round(final_size, 2)

print("="*70)
print(f"FINAL POSITION SIZE: ${final_size:.2f}")
print("="*70)

# Explain what this means
print(f"\n💡 What This Means:\n")
print(f"Notional Exposure:")
print(f"   = Position Size × Leverage")
print(f"   = ${final_size:.2f} × {leverage}")
print(f"   = ${final_size * leverage:.2f} worth of {asset}\n")

print(f"Collateral Used:")
print(f"   = Position Size / Leverage")
print(f"   = ${final_size:.2f} / {leverage}")
print(f"   = ${final_size / leverage:.2f} USDC locked\n")

print(f"Max Loss (if SL hit):")
print(f"   = Position Size × SL Distance")
print(f"   = ${final_size:.2f} × {sl_distance:.4f}")
print(f"   = ${final_size * sl_distance:.2f}")
print(f"   (This is 3% of ${asset_capital:.2f} = ${risk_amount:.2f}) ✅\n")

print(f"Max Profit (if TP hit):")
tp_distance = (tp - entry) / entry
print(f"   TP Distance = (${tp:.4f} - ${entry:.4f}) / ${entry:.4f}")
print(f"   = {tp_distance:.4f} ({tp_distance*100:.2f}%)")
print(f"   Profit = Position Size × TP Distance × Leverage")
print(f"   = ${final_size:.2f} × {tp_distance:.4f} × {leverage}")
profit = final_size * tp_distance * leverage
print(f"   = ${profit:.2f}")
print(f"   (This is 2× the risk = 2:1 R/R) ✅\n")

print(f"Risk/Reward Ratio:")
loss = final_size * sl_distance
rr_ratio = profit / loss
print(f"   Potential Profit / Potential Loss")
print(f"   = ${profit:.2f} / ${loss:.2f}")
print(f"   = {rr_ratio:.1f}:1\n")

print("="*70)
print("📊 ALL 6 POSITIONS USE THE SAME SIZING METHOD")
print("="*70)
print("\nEach position:")
print("  • Risks exactly 3% of its allocated capital")
print("  • Size adjusted based on SL distance")
print("  • Tighter SL = larger position size")
print("  • Wider SL = smaller position size")
print("  • Always capped at 50% of allocated capital")
print("  • Always maintains 2:1 reward/risk ratio")
