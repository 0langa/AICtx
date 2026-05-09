#!/usr/bin/env bash
# AICtx pre-commit hook (optional — opt-in only)
# Verifies AI context is fresh before committing.
#
# Install: ln -s ../../.aictx/hooks/pre-commit.sh .git/hooks/pre-commit
# Or via:  aictx hooks install  (future command)

set -euo pipefail

echo ":: AICtx pre-commit check"

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"

# Run strict verify, capture JSON output
VERIFY_OUTPUT=$(uv run aictx verify --project . --strict --json 2>&1 || true)
RESULT=$(echo "$VERIFY_OUTPUT" | python -c "import sys,json; print(json.load(sys.stdin).get('result','FAIL'))" 2>/dev/null || echo "FAIL")

if [ "$RESULT" = "PASS" ]; then
    echo "   PASS — context is fresh"
    exit 0
fi

NEXT_CMD=$(echo "$VERIFY_OUTPUT" | python -c "import sys,json; print(json.load(sys.stdin).get('next_command',''))" 2>/dev/null || echo "")
echo "   FAIL — $RESULT"
if [ -n "$NEXT_CMD" ]; then
    echo "   Run: $NEXT_CMD"
fi

# Non-blocking by default (opt-in strict mode via AICTX_HOOK_STRICT=1)
if [ "${AICTX_HOOK_STRICT:-}" = "1" ]; then
    exit 1
fi
echo "   (passing — set AICTX_HOOK_STRICT=1 to block on stale context)"
exit 0