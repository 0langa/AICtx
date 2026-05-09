#!/usr/bin/env bash
# AICtx pre-push hook (optional — opt-in only)
# Fails push if AI context is stale.
#
# Install: ln -s ../../.aictx/hooks/pre-push.sh .git/hooks/pre-push

set -euo pipefail

echo ":: AICtx pre-push check"

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"

VERIFY_OUTPUT=$(uv run aictx verify --project . --strict --json 2>&1 || true)
RESULT=$(echo "$VERIFY_OUTPUT" | python -c "import sys,json; print(json.load(sys.stdin).get('result','FAIL'))" 2>/dev/null || echo "FAIL")

if [ "$RESULT" = "PASS" ]; then
    echo "   PASS — context is fresh, pushing"
    exit 0
fi

NEXT_CMD=$(echo "$VERIFY_OUTPUT" | python -c "import sys,json; print(json.load(sys.stdin).get('next_command',''))" 2>/dev/null || echo "")
echo "   FAIL — $RESULT"
echo "   Push blocked. Run: $NEXT_CMD"
exit 1