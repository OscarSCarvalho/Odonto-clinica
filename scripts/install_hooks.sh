#!/usr/bin/env bash
# Instala os Git hooks do projeto.
# Execute uma vez após clonar o repositório: bash scripts/install_hooks.sh

set -e

HOOKS_DIR="$(git rev-parse --git-dir)/hooks"
SCRIPTS_DIR="$(dirname "$0")"

echo ""
echo "Instalando Git hooks..."

cp "$SCRIPTS_DIR/pre-commit" "$HOOKS_DIR/pre-commit"
chmod +x "$HOOKS_DIR/pre-commit"

echo "✔  pre-commit instalado em $HOOKS_DIR/pre-commit"
echo ""
echo "A partir de agora o lint roda automaticamente antes de cada commit."
echo ""
