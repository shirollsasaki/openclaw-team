#!/bin/bash
# Start V3 Profit Optimized Bot

cd $OPENCLAW_HOME/bighead

echo "🚀 Starting V3 Profit Optimized Bot..."
echo ""
echo "Configuration:"
echo "  Assets: SOL (\$40), ARB (\$20)"
echo "  RR Ratio: 2.5:1"
echo "  Filters: MTF + Momentum + Volume 2.0x"
echo ""

# Stop any existing bots
pkill -f "avantis_bot"
sleep 2

# Start V3
nohup python3 avantis_bot_v2_squeeze.py > v3_output.log 2>&1 &
PID=$!

echo "✅ V3 Bot started (PID: $PID)"
echo ""
echo "Monitor with:"
echo "  tail -f strategy_v3_profit.log"
echo ""
echo "Check status:"
echo "  ps aux | grep avantis_bot"
