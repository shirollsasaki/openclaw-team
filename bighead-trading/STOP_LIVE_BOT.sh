#!/bin/bash
# Stop live bot and keepalive wrapper

echo "========================================================================"
echo "🛑 STOPPING LIVE BOT"
echo "========================================================================"
echo ""

# Kill keepalive wrapper
if [ -f .keepalive_pid ]; then
    KEEPALIVE_PID=$(cat .keepalive_pid)
    if ps -p $KEEPALIVE_PID > /dev/null 2>&1; then
        echo "🛑 Stopping keepalive wrapper (PID: $KEEPALIVE_PID)..."
        kill $KEEPALIVE_PID
        rm .keepalive_pid
    fi
fi

# Kill bot
if [ -f .bot_pid ]; then
    BOT_PID=$(cat .bot_pid)
    if ps -p $BOT_PID > /dev/null 2>&1; then
        echo "🛑 Stopping bot (PID: $BOT_PID)..."
        kill $BOT_PID
        rm .bot_pid
    fi
fi

# Fallback: kill any remaining processes
if pgrep -f "keepalive_bot.sh" > /dev/null; then
    echo "🛑 Killing remaining keepalive processes..."
    pkill -f "keepalive_bot.sh"
fi

if pgrep -f "avantis_bot_v2_squeeze.py" > /dev/null; then
    echo "🛑 Killing remaining bot processes..."
    pkill -f "avantis_bot_v2_squeeze.py"
fi

sleep 2

# Verify stopped
if pgrep -f "avantis_bot_v2_squeeze.py" > /dev/null || pgrep -f "keepalive_bot.sh" > /dev/null; then
    echo ""
    echo "⚠️  Some processes still running! Force killing..."
    pkill -9 -f "avantis_bot_v2_squeeze.py"
    pkill -9 -f "keepalive_bot.sh"
    sleep 1
fi

echo ""
echo "✅ Bot stopped"
echo ""
echo "⚠️  NOTE: Positions on Avantis remain open!"
echo ""
echo "To close all positions:"
echo "   python3 EMERGENCY_CLOSE_ALL.py"
echo ""
