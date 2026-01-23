#!/bin/bash
set -euo pipefail

RULE_SRC="/mnt/pool/scripts/99-esp-fan.rules"
RULE_DST="/etc/udev/rules.d/99-esp-fan.rules"

# 1) Remove incorrect directory if it exists
if [ -d /dev/ttyESP ]; then
  rmdir /dev/ttyESP || true
fi

# 2) Restore udev rule only if destination does NOT exist
if [ -f "$RULE_SRC" ] && [ ! -f "$RULE_DST" ]; then
  cp "$RULE_SRC" "$RULE_DST"
  echo "Copied udev rule from $RULE_SRC to $RULE_DST"
else
  echo "Rule already exists at $RULE_DST, skipping copy"
fi

# 3) Reload udev rules and trigger
udevadm control --reload-rules || true
udevadm trigger || true

# 4) Wait briefly for udev to create the symlink
sleep 2

# 5) Check if udev created /dev/ttyESP
if [ -L /dev/ttyESP ]; then
  echo "udev created symlink: $(ls -l /dev/ttyESP)"
fi