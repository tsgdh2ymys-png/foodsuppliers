#!/usr/bin/env bash
# Запуск прототипа FoodSuppliers.
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "→ Создаю виртуальное окружение…"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "→ Устанавливаю зависимости…"
pip install -q -r requirements.txt

echo "→ Запускаю сервер на http://127.0.0.1:8000"
uvicorn app.main:app --reload --port 8000
