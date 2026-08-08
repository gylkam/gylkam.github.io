#!/usr/bin/env python3
"""
GYLKA Business AI — головний файл запуску.

Запуск:
  python main.py              # інтерактивний режим (запитає параметри)
  python main.py --quick      # швидкий запуск із дефолтними параметрами
  python main.py --demo       # демо-режим без реального LLM
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Кольорові виводи для термінала
# ---------------------------------------------------------------------------

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"


def _c(color: str, text: str) -> str:
    return f"{color}{text}{RESET}"


def _header(title: str) -> None:
    width = 60
    print(f"\n{BOLD}{'═' * width}{RESET}")
    print(f"{BOLD}{title.center(width)}{RESET}")
    print(f"{BOLD}{'═' * width}{RESET}\n")


# ---------------------------------------------------------------------------
# Збір параметрів бізнесу
# ---------------------------------------------------------------------------

DEFAULT_INPUTS = {
    "business_name": "GYLKA",
    "category": "електроніка та побутова техніка",
    "monthly_budget": "50000",
    "sku_count": "100",
    "min_margin": "20",
    "current_margin": "25",
    "weekly_ad_budget": "10000",
    "target_roas": "3",
}


def gather_inputs(quick: bool = False) -> dict:
    """Збирає вхідні параметри від користувача або використовує дефолти."""
    if quick:
        print(_c(YELLOW, "⚡ Швидкий запуск із дефолтними параметрами...\n"))
        return DEFAULT_INPUTS.copy()

    _header("⚙️  Налаштування бізнесу")
    print("Заповни параметри (натисни Enter для значення за замовчуванням):\n")

    fields = [
        ("business_name", "Назва магазину", "GYLKA"),
        ("category", "Категорія товарів", "електроніка та побутова техніка"),
        ("monthly_budget", "Бюджет на місяць (грн)", "50000"),
        ("sku_count", "Кількість активних SKU", "100"),
        ("min_margin", "Мінімальна маржа (%)", "20"),
        ("current_margin", "Поточна середня маржа (%)", "25"),
        ("weekly_ad_budget", "Рекламний бюджет на тиждень (грн)", "10000"),
        ("target_roas", "Цільовий ROAS (наприклад 3)", "3"),
    ]

    inputs = {}
    for key, label, default in fields:
        value = input(f"  {label} [{default}]: ").strip()
        inputs[key] = value if value else default

    return inputs


# ---------------------------------------------------------------------------
# Демо-режим (без LLM)
# ---------------------------------------------------------------------------

DEMO_REPORT = """
# 📊 ДЕМО-звіт GYLKA Business AI
> Це приклад виводу. Для реального запуску потрібен OpenAI API або Ollama.

## Аналіз ринку
- Середня ціна конкурентів у категорії: 2 450 грн
- Ваша позиція: -8% від середньої (конкурентна)
- Топ можливість: SKU "Блендер XL-500" — конкуренти підняли ціну на 15%

## Рекомендації контенту
- 3 картки мають назви без ключових слів → переписати першочергово
- Додати відео-огляд для топ-5 SKU (очікуване зростання CTR +25%)

## Цінова стратегія
- Локомотиви (5 SKU): знизити ціну на 5–8%
- Стандарт (70 SKU): зберегти поточні ціни
- Ретест (25 SKU): підняти ціну на 3–5% після оновлення контенту

## Реклама
- Бюджет 10 000 грн/тиждень → ROAS 3.2x
- Зупинити: 12 оголошень (ROAS < 1.5x)
- Масштабувати: 5 оголошень (ROAS > 4x)

## KPI
| Покази | CTR  | Конверсія | ROAS | Маржа |
|--------|------|-----------|------|-------|
| 45 000 | 2.1% | 1.8%      | 3.2x | 22%   |
"""


def run_demo(inputs: dict) -> None:
    """Виводить демо-звіт без реального LLM."""
    _header("🤖 GYLKA Business AI — ДЕМО")
    print(_c(CYAN, f"Бізнес: {inputs['business_name']}"))
    print(_c(CYAN, f"Категорія: {inputs['category']}\n"))
    print(DEMO_REPORT)
    print(_c(GREEN, "✅ Демо завершено!"))
    print(
        "\nДля реального запуску:\n"
        "  1. Встанови залежності: pip install -r requirements.txt\n"
        "  2. Додай OPENAI_API_KEY у файл .env (або запусти Ollama)\n"
        "  3. Запусти: python main.py\n"
    )


# ---------------------------------------------------------------------------
# Реальний запуск через CrewAI
# ---------------------------------------------------------------------------

def run_crew(inputs: dict) -> None:
    """Запускає повну команду агентів."""
    _header("🚀 GYLKA Business AI — Запуск агентів")

    # Відкладений імпорт — crewai потрібен лише тут
    try:
        from crew import GylkaBusinessCrew  # noqa: PLC0415
    except ImportError as exc:
        print(
            _c(RED, f"❌ Помилка імпорту: {exc}\n")
            + "Встановіть залежності:\n"
            + "  pip install -r requirements.txt\n"
            + "Або запустіть демо: python main.py --demo"
        )
        sys.exit(1)

    api_key = os.getenv("OPENAI_API_KEY", "")
    ollama_base = os.getenv("OPENAI_API_BASE", "")

    if not api_key and not ollama_base:
        print(
            _c(RED, "❌ Не знайдено API ключ або Ollama.\n")
            + "Встанови одне з двох у файлі .env:\n"
            + "  OPENAI_API_KEY=sk-...\n"
            + "  або\n"
            + "  OPENAI_API_BASE=http://localhost:11434/v1\n"
            + "  OPENAI_MODEL_NAME=ollama/llama3\n\n"
            + "Для демо без LLM: python main.py --demo"
        )
        sys.exit(1)

    print(f"  Бізнес: {_c(CYAN, inputs['business_name'])}")
    print(f"  Категорія: {_c(CYAN, inputs['category'])}")
    print(f"  SKU: {_c(CYAN, inputs['sku_count'])}")
    print(f"  Бюджет/міс: {_c(CYAN, inputs['monthly_budget'])} грн\n")

    start = datetime.now()
    print(_c(YELLOW, "⏳ Агенти почали роботу. Очікуй результатів...\n"))

    try:
        result = GylkaBusinessCrew().crew().kickoff(inputs=inputs)
    except Exception as exc:  # noqa: BLE001
        print(_c(RED, f"\n❌ Помилка виконання: {exc}"))
        sys.exit(1)

    elapsed = (datetime.now() - start).seconds
    _header("✅ Готово!")
    print(f"Час виконання: {elapsed // 60}хв {elapsed % 60}с\n")

    report_path = Path(__file__).parent / "data" / "weekly_report.md"
    if report_path.exists():
        print(_c(GREEN, f"📄 Звіт збережено: {report_path}"))
    else:
        print(result)


# ---------------------------------------------------------------------------
# Точка входу
# ---------------------------------------------------------------------------

def _load_dotenv() -> None:
    """Завантажує .env файл якщо він існує."""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="GYLKA Business AI — мультиагентна система для маркетплейсів"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Швидкий запуск із параметрами за замовчуванням",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Демо-режим без реального LLM (тільки зразки виводу)",
    )
    parser.add_argument(
        "--inputs",
        type=str,
        help='JSON-рядок з параметрами (наприклад \'{"business_name":"Мій магазин"}\')',
    )
    args = parser.parse_args()

    _load_dotenv()

    if args.inputs:
        try:
            override = json.loads(args.inputs)
            inputs = {**DEFAULT_INPUTS, **override}
        except json.JSONDecodeError as exc:
            print(_c(RED, f"❌ Невірний JSON у --inputs: {exc}"))
            sys.exit(1)
    else:
        inputs = gather_inputs(quick=args.quick or args.demo)

    if args.demo:
        run_demo(inputs)
    else:
        run_crew(inputs)


if __name__ == "__main__":
    main()
