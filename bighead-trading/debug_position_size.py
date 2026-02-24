#!/usr/bin/env python3
"""Debug why position sizing is too small"""

# Simulate the position sizing logic
asset_capital = 10.0  # $10 for ARB
entry = 0.101921
range_low = 0.0964  # From earlier logs

# Calculate SL
sl = range_low if range_low < entry else entry * 0.985
print(f"Entry: ${entry:.6f}")
print(f"Range Low: ${range_low:.6f}")
print(f"SL: ${sl:.6f}")

# Calculate SL distance
sl_distance = abs(entry - sl) / entry
print(f"SL Distance: {sl_distance*100:.2f}%")

# Check if valid
MIN_SL = 0.005  # 0.5%
MAX_SL = 0.05   # 5%

if sl_distance < MIN_SL:
    print(f"❌ SL too tight! {sl_distance*100:.2f}% < {MIN_SL*100}%")
elif sl_distance > MAX_SL:
    print(f"❌ SL too wide! {sl_distance*100:.2f}% > {MAX_SL*100}%")
else:
    print(f"✅ SL distance valid")

# Calculate position size
RISK_PER_TRADE = 0.03
risk_amount = asset_capital * RISK_PER_TRADE
print(f"\nRisk Amount: ${risk_amount:.2f}")

size = risk_amount / sl_distance
print(f"Calculated Size: ${size:.2f}")

# Cap at 50%
max_size = asset_capital * 0.5
size = min(size, max_size)
print(f"After 50% cap: ${size:.2f}")

# Minimum size
if size < 0.1:
    print(f"❌ Size too small: ${size:.2f} < $0.10")
else:
    print(f"✅ Size valid: ${size:.2f}")
