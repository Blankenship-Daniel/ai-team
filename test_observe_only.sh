#!/bin/bash

# Test script for --observe-only flag
# This script verifies that agents stay in observe mode when the flag is set

echo "==================================="
echo "Testing --observe-only flag"
echo "==================================="

# Test session name
TEST_SESSION="test-observe-only"

# Function to check if session exists
session_exists() {
    tmux has-session -t "$1" 2>/dev/null
}

# Function to capture pane content
capture_pane() {
    tmux capture-pane -t "$1" -p 2>/dev/null
}

# Clean up any existing test session
if session_exists "$TEST_SESSION"; then
    echo "Cleaning up existing test session..."
    tmux kill-session -t "$TEST_SESSION"
fi

echo ""
echo "Test 1: Creating team WITH --observe-only flag"
echo "-----------------------------------------------"

# Create team with observe-only flag
python3 create_ai_team.py --session "$TEST_SESSION" --observe-only --yes

if [ $? -eq 0 ]; then
    echo "✅ Team created successfully with --observe-only"

    # Wait for agents to initialize
    echo "Waiting for agents to initialize..."
    sleep 10

    # Check each agent pane for observe-only behavior
    for pane in 0.1 0.2 0.3; do
        echo ""
        echo "Checking pane $TEST_SESSION:$pane..."
        content=$(capture_pane "$TEST_SESSION:$pane" | tail -20)

        # Check for observe-only indicators
        if echo "$content" | grep -q "OBSERVE-ONLY MODE"; then
            echo "✅ Found OBSERVE-ONLY MODE indicator in pane $pane"
        else
            echo "⚠️  No OBSERVE-ONLY MODE indicator found in pane $pane"
        fi

        # Check that agents aren't starting work
        if echo "$content" | grep -q "introduce myself\|introducing myself\|Hello, I'm\|I am"; then
            echo "✅ Agent appears to be introducing itself"
        fi

        # Check for work indicators (should NOT be present)
        if echo "$content" | grep -q "analyzing\|scanning\|checking\|implementing\|fixing"; then
            echo "❌ WARNING: Agent appears to be starting work!"
        else
            echo "✅ No work activity detected"
        fi
    done

    # Clean up test session
    echo ""
    echo "Cleaning up test session..."
    tmux kill-session -t "$TEST_SESSION"
else
    echo "❌ Failed to create team with --observe-only"
    exit 1
fi

echo ""
echo "==================================="
echo "Test 2: Creating team WITHOUT --observe-only flag"
echo "==================================="

# Create team without observe-only flag
python3 create_ai_team.py --session "$TEST_SESSION" --yes

if [ $? -eq 0 ]; then
    echo "✅ Team created successfully without --observe-only"

    # Wait for agents to initialize
    echo "Waiting for agents to initialize..."
    sleep 10

    # Check that observe-only is NOT active
    for pane in 0.1 0.2 0.3; do
        content=$(capture_pane "$TEST_SESSION:$pane" | tail -20)

        if echo "$content" | grep -q "OBSERVE-ONLY MODE"; then
            echo "❌ Found OBSERVE-ONLY MODE in pane $pane when it shouldn't be there!"
        else
            echo "✅ No OBSERVE-ONLY MODE in pane $pane (expected)"
        fi
    done

    # Clean up test session
    echo ""
    echo "Cleaning up test session..."
    tmux kill-session -t "$TEST_SESSION"
else
    echo "❌ Failed to create team without --observe-only"
    exit 1
fi

echo ""
echo "==================================="
echo "All tests completed!"
echo "==================================="
