#!/bin/bash
cd $OPENCLAW_HOME/bighead
timeout 10 python3 avantis_bot_v2.py 2>&1 | head -30
