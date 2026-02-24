#!/bin/bash
# Keepalive wrapper - automatically restarts bot if it crashes
# This prevents "zsh: terminated" issues

BOT_SCRIPT="avantis_bot_v2_squeeze.py"
LOG_FILE="bot_keepalive.log"
MAX_RESTARTS=10
RESTART_COUNT=0

echo "======================================================================" | tee -a $LOG_FILE
echo "🔴 KEEPALIVE BOT STARTING - $(date)" | tee -a $LOG_FILE
echo "======================================================================" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE
echo "This wrapper will automatically restart the bot if it crashes." | tee -a $LOG_FILE
echo "Log: $LOG_FILE" | tee -a $LOG_FILE
echo "Stop: kill $$" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# Function to cleanup on exit
cleanup() {
    echo "" | tee -a $LOG_FILE
    echo "🛑 Keepalive stopped by user - $(date)" | tee -a $LOG_FILE
    pkill -P $$  # Kill child processes
    exit 0
}

trap cleanup SIGINT SIGTERM

while [ $RESTART_COUNT -lt $MAX_RESTARTS ]; do
    echo "======================================================================" | tee -a $LOG_FILE
    echo "🚀 Starting bot (attempt $((RESTART_COUNT + 1))/$MAX_RESTARTS) - $(date)" | tee -a $LOG_FILE
    echo "======================================================================" | tee -a $LOG_FILE
    
    # Start bot and capture exit code
    python3 $BOT_SCRIPT
    EXIT_CODE=$?
    
    echo "" | tee -a $LOG_FILE
    echo "⚠️  Bot exited with code $EXIT_CODE - $(date)" | tee -a $LOG_FILE
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "✅ Bot exited cleanly (code 0)" | tee -a $LOG_FILE
        break
    elif [ $EXIT_CODE -eq 137 ]; then
        echo "❌ Bot was KILLED (SIGKILL - code 137)" | tee -a $LOG_FILE
        echo "   Possible causes: Out of memory, manual kill -9" | tee -a $LOG_FILE
    elif [ $EXIT_CODE -eq 143 ]; then
        echo "🛑 Bot was TERMINATED (SIGTERM - code 143)" | tee -a $LOG_FILE
        echo "   Caused by: manual kill command or system shutdown" | tee -a $LOG_FILE
        break  # Don't restart on manual termination
    else
        echo "❌ Bot crashed (code $EXIT_CODE)" | tee -a $LOG_FILE
    fi
    
    RESTART_COUNT=$((RESTART_COUNT + 1))
    
    if [ $RESTART_COUNT -lt $MAX_RESTARTS ]; then
        echo "🔄 Restarting in 5 seconds..." | tee -a $LOG_FILE
        echo "" | tee -a $LOG_FILE
        sleep 5
    fi
done

if [ $RESTART_COUNT -ge $MAX_RESTARTS ]; then
    echo "" | tee -a $LOG_FILE
    echo "======================================================================" | tee -a $LOG_FILE
    echo "🚨 MAX RESTARTS REACHED ($MAX_RESTARTS)" | tee -a $LOG_FILE
    echo "======================================================================" | tee -a $LOG_FILE
    echo "" | tee -a $LOG_FILE
    echo "Bot crashed too many times. Manual intervention needed." | tee -a $LOG_FILE
    echo "" | tee -a $LOG_FILE
    echo "Check logs:" | tee -a $LOG_FILE
    echo "  - tail -100 strategy1_v2_squeeze.log" | tee -a $LOG_FILE
    echo "  - cat bot_keepalive.log" | tee -a $LOG_FILE
    echo "" | tee -a $LOG_FILE
fi

echo "Keepalive wrapper exited - $(date)" | tee -a $LOG_FILE
