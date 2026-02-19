#!/usr/bin/env bash
# ai-server 실행: poetry 가상환경 사용 (의존성 확인 후 실행)
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT" || exit 1
poetry install --no-interaction --quiet 2>/dev/null
VENV_PYTHON="$(poetry env info -p 2>/dev/null)/bin/python"
if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "Poetry 가상환경이 없습니다. 'poetry install'을 실행한 뒤 다시 시도하세요."
  exit 1
fi
cd "$ROOT/src/ai-server" || exit 1
exec "$VENV_PYTHON" main.py
