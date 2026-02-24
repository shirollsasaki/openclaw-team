#!/bin/bash
# OpenClaw Multi-Agent Local Setup Script
# Run from: $OPENCLAW_HOME/

OPENCLAW_DIR="$OPENCLAW_HOME"

echo "📋 Setting up 7 agents in $OPENCLAW_DIR..."

# Copy SOUL.md and AGENTS.md to each agent dir
for agent in richard jared erlich gilfoyle monica bighead dinesh; do
  if [ -d "$agent" ]; then
    echo "✅ $agent/ — copying files..."
    # Files should already be in place if you extracted the download here
  else
    echo "⚠️  $agent/ not found — creating..."
    mkdir -p "$agent"
  fi
done

# Backup existing openclaw.json
if [ -f "$OPENCLAW_DIR/openclaw.json" ]; then
  cp "$OPENCLAW_DIR/openclaw.json" "$OPENCLAW_DIR/openclaw.json.backup"
  echo "📦 Backed up existing openclaw.json"
fi

# Copy new config
cp openclaw.json "$OPENCLAW_DIR/openclaw.json"
echo "✅ openclaw.json installed"

echo ""
echo "⚠️  IMPORTANT: You still need to:"
echo "1. Replace YOUR_DISCORD_CHANNEL_ID in openclaw.json"
echo "   To get it: Enable Developer Mode in Discord Settings > Advanced"
echo "   Then right-click your channel > Copy Channel ID"
echo ""
echo "2. Restart the gateway:"
echo "   openclaw gateway restart"
echo ""
echo "3. Test with: @richard what's your status?"
