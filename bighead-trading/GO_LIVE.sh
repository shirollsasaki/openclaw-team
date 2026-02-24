#!/bin/bash
# GO LIVE - Instant deployment script
# Run when user says "go live"

cd $OPENCLAW_HOME/bighead

echo "=========================================="
echo "🚀 GOING LIVE - AVANTIS REAL TRADING"
echo "=========================================="
echo ""

# Which bot to go live with?
echo "Choose bot to go live:"
echo "1. V2 Enhanced (Best performer: +19.3%)"
echo "2. V2+Squeeze (Conservative: +18.7%)"
echo "3. V2+Squeeze+All3 (Ultra selective)"
echo "4. V1 Baseline (Most trades)"
echo ""
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        BOT_FILE="avantis_bot_v2.py"
        BOT_NAME="V2 Enhanced"
        ;;
    2)
        BOT_FILE="avantis_bot_v2_squeeze.py"
        BOT_NAME="V2+Squeeze"
        ;;
    3)
        BOT_FILE="avantis_bot_v2_squeeze_all3.py"
        BOT_NAME="V2+Squeeze+All3"
        ;;
    4)
        BOT_FILE="avantis_bot.py"
        BOT_NAME="V1 Baseline"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Selected: $BOT_NAME"
echo ""

# Confirm
read -p "⚠️  GO LIVE WITH REAL MONEY? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Cancelled"
    exit 0
fi

echo ""
echo "🔧 Step 1: Setting SIMULATION_MODE = False..."

# Create backup
cp "$BOT_FILE" "${BOT_FILE}.backup"

# Replace SIMULATION_MODE
# (This is a placeholder - actual implementation needs Python script to properly edit)
echo "   ⚠️  Manual step required:"
echo "   Edit $BOT_FILE"
echo "   Find: SIMULATION_MODE = True"
echo "   Change to: SIMULATION_MODE = False"
echo ""

read -p "Press ENTER when done..."

echo ""
echo "🔧 Step 2: Stopping simulation bot..."
pkill -f "$BOT_FILE"
sleep 2

echo ""
echo "🚀 Step 3: Starting LIVE bot..."
python3 "$BOT_FILE" > "live_${BOT_FILE}.log" 2>&1 &
LIVE_PID=$!

echo ""
echo "=========================================="
echo "✅ LIVE TRADING ACTIVATED!"
echo "=========================================="
echo ""
echo "Bot: $BOT_NAME"
echo "PID: $LIVE_PID"
echo "Log: live_${BOT_FILE}.log"
echo ""
echo "🔴 THIS IS REAL MONEY NOW!"
echo ""
echo "Monitor: tail -f live_${BOT_FILE}.log"
echo "Stop: kill $LIVE_PID"
echo ""
echo "=========================================="
