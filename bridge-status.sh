#!/bin/bash
echo "🔗 Bridge Status:"
echo "  Session 1: bsnes-plus"
echo "  Session 2: snes-modder"
echo "  Context: We're currently working on figuring out how to reverse engineer The Legend of Zelda: A Link to the Past, a classic Super Nintendo game. Since you both are working on similar projects, combine your efforts to create a single robust solution. Use all available snes and zelda related mcp servers to guide your efforts."
echo "  Coordination Dir: $(pwd)/.ai-coordination"
echo ""
echo "📊 Message Count:"
MSG_COUNT=$(find .ai-coordination/messages -name "*.json" 2>/dev/null | wc -l)
echo "  Total messages: $MSG_COUNT"
