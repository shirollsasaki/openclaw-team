#!/bin/bash
# EMERGENCY STOP - Kill bot immediately
# Stops bot but LEAVES POSITIONS OPEN on Avantis

echo "=========================================="
echo "🛑 EMERGENCY STOP"
echo "=========================================="
echo ""
echo "This will:"
echo "  ✅ Stop the bot immediately"
echo "  ✅ Prevent new trades"
echo "  ⚠️  LEAVE existing positions open"
echo ""
echo "To close positions too, use:"
echo "  python3 EMERGENCY_CLOSE_ALL.py"
echo ""

read -p "Stop bot? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Cancelled"
    exit 0
fi

echo ""
echo "🛑 Stopping V2+Squeeze bot..."

# Kill by PID if known
if pgrep -f "avantis_bot_v2_squeeze.py" > /dev/null; then
    pkill -f "avantis_bot_v2_squeeze.py"
    echo "✅ Bot stopped"
    echo ""
    echo "Check stopped:"
    sleep 1
    if pgrep -f "avantis_bot_v2_squeeze.py" > /dev/null; then
        echo "⚠️  Bot still running, trying force kill..."
        pkill -9 -f "avantis_bot_v2_squeeze.py"
    else
        echo "✅ Bot confirmed stopped"
    fi
else
    echo "⚠️  Bot not running"
fi

echo ""
echo "=========================================="
echo "BOT STOPPED"
echo "=========================================="
echo ""
echo "⚠️  Any open positions are STILL ACTIVE on Avantis"
echo ""
echo "To close all positions:"
echo "  python3 EMERGENCY_CLOSE_ALL.py"
echo ""
echo "To check positions:"
echo "  https://avantisfi.com"
echo ""
