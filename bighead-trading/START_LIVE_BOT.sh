#!/bin/bash
# Start live bot with keepalive (auto-restart on crash)

echo "========================================================================"
echo "🚀 STARTING LIVE BOT WITH AUTO-RESTART"
echo "========================================================================"
echo ""

# Check if bot is already running
if pgrep -f "avantis_bot_v2_squeeze.py" > /dev/null; then
    echo "⚠️  Bot already running!"
    echo ""
    echo "Current bot PIDs:"
    ps aux | grep "avantis_bot_v2_squeeze.py" | grep -v grep
    echo ""
    read -p "Kill existing bots and restart? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        echo "🛑 Stopping existing bots..."
        pkill -f "avantis_bot_v2_squeeze.py"
        pkill -f "keepalive_bot.sh"
        sleep 2
        echo "✅ Stopped"
    else
        echo "❌ Cancelled"
        exit 0
    fi
fi

echo ""
echo "Starting bot with auto-restart protection..."
echo ""
echo "📊 Monitor:"
echo "   tail -f strategy1_v2_squeeze.log  (bot activity)"
echo "   tail -f bot_keepalive.log         (restart events)"
echo ""
echo "🛑 Stop:"
echo "   bash STOP_LIVE_BOT.sh"
echo "   or: kill \$KEEPALIVE_PID"
echo ""
echo "🚨 Emergency:"
echo "   python3 EMERGENCY_CLOSE_ALL.py"
echo ""

# Start in background
nohup bash keepalive_bot.sh > /dev/null 2>&1 &
KEEPALIVE_PID=$!

sleep 3

if ps -p $KEEPALIVE_PID > /dev/null; then
    echo "✅ Keepalive started (PID: $KEEPALIVE_PID)"
    
    # Wait for bot to start
    sleep 2
    
    BOT_PID=$(pgrep -f "avantis_bot_v2_squeeze.py")
    if [ -n "$BOT_PID" ]; then
        echo "✅ Bot started (PID: $BOT_PID)"
        echo ""
        echo "========================================================================"
        echo "🔴 LIVE TRADING ACTIVE"
        echo "========================================================================"
        echo ""
        echo "Keepalive PID: $KEEPALIVE_PID"
        echo "Bot PID: $BOT_PID"
        echo ""
        echo "Bot will automatically restart if it crashes!"
        echo ""
        
        # Save PIDs
        echo "$KEEPALIVE_PID" > .keepalive_pid
        echo "$BOT_PID" > .bot_pid
    else
        echo "❌ Bot failed to start!"
        echo "Check: tail -20 bot_keepalive.log"
        kill $KEEPALIVE_PID
        exit 1
    fi
else
    echo "❌ Keepalive failed to start!"
    exit 1
fi
