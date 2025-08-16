#!/bin/bash
echo "🔗 Bridge Status:"
echo "  Session 1: bsnes"
echo "  Session 2: snes-modder"
echo "  Context: Since both of these projects are working on similar things. Lets have each Orchestrator review the other Orchestrators code to see how we can learn from each other"
echo "  Coordination Dir: $(pwd)/.ai-coordination"
echo ""
echo "📊 Message Count:"
MSG_COUNT=$(find .ai-coordination/messages -name "*.json" 2>/dev/null | wc -l)
echo "  Total messages: $MSG_COUNT"
