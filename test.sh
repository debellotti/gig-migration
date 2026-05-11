#!/usr/bin/env bash
set -e

BASE="http://localhost:8080"

echo "--- create accounts ---"
ALICE=$(curl -sf -X POST "$BASE/accounts" \
  -H "Content-Type: application/json" \
  -d '{"ownerName":"Alice","currency":"EUR","initialBalance":1000.00}')
echo "Alice: $ALICE"

BOB=$(curl -sf -X POST "$BASE/accounts" \
  -H "Content-Type: application/json" \
  -d '{"ownerName":"Bob","currency":"EUR","initialBalance":500.00}')
echo "Bob:   $BOB"

ALICE_ID=$(echo "$ALICE" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
BOB_ID=$(echo "$BOB"   | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

echo ""
echo "--- transfer 200 EUR from Alice to Bob ---"
curl -sf -X POST "$BASE/transfers" \
  -H "Content-Type: application/json" \
  -d "{\"fromAccountId\":\"$ALICE_ID\",\"toAccountId\":\"$BOB_ID\",\"amount\":200.00}"
echo ""

echo ""
echo "--- balances (Alice=800, Bob=700) ---"
echo "Alice: $(curl -sf "$BASE/accounts/$ALICE_ID")"
echo "Bob:   $(curl -sf "$BASE/accounts/$BOB_ID")"

echo ""
echo "--- transfer history for Alice ---"
curl -sf "$BASE/accounts/$ALICE_ID/transfers"
echo ""
