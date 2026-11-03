#!/bin/bash
# Finder does not inherit the interactive shell's PATH.
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
cd -- "$(dirname -- "$0")" || exit 1
if ! command -v node >/dev/null 2>&1; then
  printf '\nFalta Node.js 22 o posterior. Instálalo desde https://nodejs.org/\n'
  read -r -p 'Pulsa Intro para cerrar…'
  exit 1
fi
node scripts/launch.cjs
status=$?
if [ "$status" -ne 0 ]; then read -r -p 'Pulsa Intro para cerrar…'; fi
exit "$status"
