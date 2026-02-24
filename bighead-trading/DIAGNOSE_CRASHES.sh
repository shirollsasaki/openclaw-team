#!/bin/bash
# Diagnose why the bot keeps crashing

echo "========================================================================"
echo "🔍 BOT CRASH DIAGNOSTICS"
echo "========================================================================"
echo ""

echo "📊 SYSTEM MEMORY:"
echo "----------------------------------------"
vm_stat | head -10
echo ""

echo "📊 PYTHON PROCESSES:"
echo "----------------------------------------"
ps aux | grep python | grep -v grep | head -10
echo ""

echo "📊 BOT PROCESSES:"
echo "----------------------------------------"
if pgrep -f "avantis_bot_v2_squeeze.py" > /dev/null; then
    echo "✅ Bot is running:"
    ps aux | grep "avantis_bot_v2_squeeze.py" | grep -v grep
else
    echo "❌ Bot is NOT running"
fi
echo ""

if pgrep -f "keepalive_bot.sh" > /dev/null; then
    echo "✅ Keepalive is running:"
    ps aux | grep "keepalive_bot.sh" | grep -v grep
else
    echo "❌ Keepalive is NOT running"
fi
echo ""

echo "📊 LAST 20 LINES OF BOT LOG:"
echo "----------------------------------------"
tail -20 strategy1_v2_squeeze.log
echo ""

echo "📊 KEEPALIVE LOG (crashes/restarts):"
echo "----------------------------------------"
if [ -f bot_keepalive.log ]; then
    cat bot_keepalive.log
else
    echo "No keepalive log yet"
fi
echo ""

echo "📊 RECENT ERRORS IN BOT LOG:"
echo "----------------------------------------"
grep -E "ERROR|Exception|Traceback|terminated|killed" strategy1_v2_squeeze.log | tail -10
echo ""

echo "📊 DISK SPACE:"
echo "----------------------------------------"
df -h . | head -2
echo ""

echo "========================================================================"
echo "RECOMMENDATIONS"
echo "========================================================================"
echo ""

# Check memory
FREE_MEM=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
if [ -n "$FREE_MEM" ] && [ "$FREE_MEM" -lt 100000 ]; then
    echo "⚠️  LOW MEMORY - This could cause crashes"
    echo "   Solution: Close other applications"
    echo ""
fi

# Check if bot crashed recently
if grep -q "Bot exited with code" bot_keepalive.log 2>/dev/null; then
    echo "🔴 BOT HAS CRASHED BEFORE"
    echo "   Check bot_keepalive.log for crash codes:"
    echo "   - Code 137 = Killed (out of memory)"
    echo "   - Code 143 = Terminated (manual kill)"
    echo "   - Other = Exception/error"
    echo ""
fi

# Check if running with keepalive
if ! pgrep -f "keepalive_bot.sh" > /dev/null; then
    echo "💡 START WITH KEEPALIVE FOR AUTO-RESTART"
    echo "   bash START_LIVE_BOT.sh"
    echo ""
fi

echo "✅ Diagnostic complete"
echo ""
