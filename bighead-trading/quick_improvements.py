#!/usr/bin/env python3
"""Quick improvements we can make in 5 minutes each"""

print("🚀 Quick Improvements Available\n")
print("="*70)

improvements = [
    {
        "name": "Increase Position Limits",
        "time": "30 seconds",
        "difficulty": "Easy",
        "impact": "High",
        "code": """
# In avantis_bot.py, change:
MAX_POSITIONS_PER_ASSET = 2  # → 3
MAX_TOTAL_POSITIONS = 6      # → 10

Result: Can take more opportunities, deploy more capital
        """,
        "benefit": "Deploy $28 idle capital, more trades"
    },
    {
        "name": "Enable Discord Notifications",
        "time": "2 minutes",
        "difficulty": "Easy",
        "impact": "Medium",
        "code": """
# Already have webhook in .env
# Notifications already coded
# Just need to verify webhook URL is set

Sends alerts for:
- Positions opened
- TP/SL hit
- Total P&L updates
        """,
        "benefit": "Monitor bot from phone, instant alerts"
    },
    {
        "name": "Increase Max SL Distance",
        "time": "30 seconds",
        "difficulty": "Easy",
        "impact": "Medium",
        "code": """
# Already done! Was 5%, now 10%
# This fixed the 'position size too small' errors

MAX_SL_DISTANCE = 0.10  # ✅ Fixed
        """,
        "benefit": "Already done - bot takes more trades now"
    },
    {
        "name": "Add Breakeven Stop",
        "time": "5 minutes",
        "difficulty": "Medium",
        "impact": "High",
        "code": """
# In Position.check_exit(), add:

# If position is up 50% to TP, move SL to breakeven
if self.direction == 'LONG':
    price_to_tp = (self.tp - self.entry) / (self.tp - self.entry)
    current_progress = (current_price - self.entry) / (self.tp - self.entry)
    
    if current_progress > 0.5 and self.sl < self.entry:
        self.sl = self.entry  # Move to breakeven
        logger.info(f"Moved SL to breakeven: {self.asset}")
        """,
        "benefit": "Protect profits, reduce losing trades"
    },
    {
        "name": "Add Position Count to Status",
        "time": "1 minute",
        "difficulty": "Easy",
        "impact": "Low",
        "code": """
# Already done! ✅
Status | Open: 6 | ...
        """,
        "benefit": "Already done - can see open count"
    }
]

for i, imp in enumerate(improvements, 1):
    print(f"{i}. {imp['name']}")
    print(f"   Time: {imp['time']}")
    print(f"   Difficulty: {imp['difficulty']}")
    print(f"   Impact: {imp['impact']}")
    print(f"   Benefit: {imp['benefit']}")
    print()

print("="*70)
print("🎯 Recommended Order:")
print("="*70)
print("1. Increase position limits (30 sec) ← Do this now")
print("2. Add breakeven stops (5 min)")
print("3. Check Discord webhook (1 min)")
print("\nTotal time: ~7 minutes for big improvements")
