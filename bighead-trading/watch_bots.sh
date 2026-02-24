#!/bin/bash
# Continuous bot monitoring - runs check_bots_now.py every 60 seconds

cd $OPENCLAW_HOME/bighead

echo "🤖 Starting continuous bot monitoring..."
echo "📊 Updates every 60 seconds"
echo "🛑 Press Ctrl+C to stop"
echo ""

while true; do
    clear
    python3 check_bots_now.py
    echo ""
    echo "⏳ Next update in 60 seconds... (Ctrl+C to stop)"
    sleep 60
done
