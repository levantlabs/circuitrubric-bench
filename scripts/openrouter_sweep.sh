#!/usr/bin/env bash
# Example: reproduce the CircuitRubric open-model baselines through OpenRouter.
#
# OpenRouter is an OpenAI-compatible endpoint, so this uses the shipped `openai` backend
# (no OpenRouter-specific code). See docs/reproducing.md for the full walkthrough.
#
# Prereqs:
#   pip install -e ".[openai]"
#   export OPENROUTER_API_KEY=sk-or-...
#   cp models.example.yaml models.openrouter.yaml   # keep only the OpenRouter rows
#
# Usage:
#   bash scripts/openrouter_sweep.sh
#   # tune via env, e.g.:  TIERS="short verbose spec" SYS_PROMPTS="topology_ports" REPS=3 bash scripts/openrouter_sweep.sh
set -euo pipefail

: "${OPENROUTER_API_KEY:?export OPENROUTER_API_KEY first (get a key at openrouter.ai)}"

MODELS="${MODELS:-models.openrouter.yaml}"     # a models.yaml holding the OpenRouter rows
OUT="${OUT:-results}"
MAXTOK="${MAXTOK:-20000}"                       # reasoning models emit EMPTY at small budgets
TEMP="${TEMP:-0.0}"                            # set TEMP="" to omit (some reasoning models reject it)
REPS="${REPS:-1}"                              # use 3 for error bars (temp=0 is not deterministic)
SYS_PROMPTS="${SYS_PROMPTS:-topology_ports strict_ports}"   # the no-leak design prompts
TIERS="${TIERS:-short}"                        # design tier is the discriminator; add verbose,spec for the full picture

[ -f "$MODELS" ] || { echo "missing $MODELS — copy the OpenRouter rows from models.example.yaml"; exit 1; }

temp_arg=()
[ -n "$TEMP" ] && temp_arg=(--temperature "$TEMP")
tiers_csv="$(echo "$TIERS" | tr ' ' ,)"

for sp in $SYS_PROMPTS; do
  echo ">>> system_prompt=$sp  tiers=$tiers_csv  max_tokens=$MAXTOK  reps=$REPS"
  circuitrubric run-all \
    --models "$MODELS" \
    --prompt-ids "$tiers_csv" \
    --system-prompt-id "$sp" \
    --max-tokens "$MAXTOK" \
    --reps "$REPS" \
    "${temp_arg[@]}" \
    --output-dir "$OUT"
done

echo
echo ">>> credit table per run:"
python3 scripts/aggregate_runs.py "$OUT"/*
