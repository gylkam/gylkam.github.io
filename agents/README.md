# 🤖 GYLKA Business AI — Мультиагентна система для маркетплейсів

> Локальна AI-система з 7 спеціалізованими агентами для автоматичного
> аналізу, оптимізації та зростання продажів на **Rozetka, Prom і EpicentrK**.

---

## 🧠 Що робить система

| Агент | Роль |
|---|---|
| **Business Strategist** | Координує всіх агентів, бачить загальну картину P&L |
| **Market Researcher** | Моніторить ціни конкурентів на Rozetka та Prom |
| **Content Creator** | Пише SEO-назви та описи товарів українською |
| **Pricing Analyst** | Оптимізує ціни, розраховує маржу, знаходить локомотиви |
| **Customer Relations** | Аналізує відгуки, дає шаблони відповідей |
| **Analytics Expert** | Розраховує KPI: CTR, конверсія, ROAS, маржа |
| **Advertising Manager** | Планує рекламний бюджет за стратегією 60/25/15 |

На виході — **тижневий markdown-звіт** з конкретними діями на наступний тиждень.

---

## 🚀 Швидкий старт

### Крок 1 — Клонуй репозиторій

```bash
git clone https://github.com/gylkam/gylkam.github.io.git
cd gylkam.github.io/agents
```

### Крок 2 — Встанови залежності

```bash
# Рекомендовано: створи virtualenv
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
# або
.venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

### Крок 3 — Налаштуй AI-модель

Скопіюй `.env.example` у `.env` і заповни:

```bash
cp .env.example .env
```

**Варіант A — OpenAI API** (платний, найточніший):
```env
OPENAI_API_KEY=sk-твій_ключ_з_platform.openai.com
OPENAI_MODEL_NAME=gpt-4o-mini
```

**Варіант B — Ollama** (безкоштовний, повністю локальний):
1. Встанови Ollama: [ollama.com](https://ollama.com)
2. Завантаж модель: `ollama pull llama3`
3. У `.env`:
```env
OPENAI_API_BASE=http://localhost:11434/v1
OPENAI_API_KEY=ollama
OPENAI_MODEL_NAME=ollama/llama3
```

### Крок 4 — Запуск

```bash
# Інтерактивний режим (система запитає параметри бізнесу)
python main.py

# Швидкий запуск з дефолтними параметрами
python main.py --quick

# Демо без LLM (щоб побачити приклад виводу)
python main.py --demo

# З параметрами через JSON
python main.py --inputs '{"business_name":"Мій магазин","category":"меблі","monthly_budget":"80000","sku_count":"200"}'
```

---

## 📋 Параметри запуску

| Параметр | Опис | Дефолт |
|---|---|---|
| `business_name` | Назва магазину | GYLKA |
| `category` | Категорія товарів | електроніка |
| `monthly_budget` | Бюджет на місяць (грн) | 50000 |
| `sku_count` | Кількість активних SKU | 100 |
| `min_margin` | Мінімальна маржа (%) | 20 |
| `current_margin` | Поточна середня маржа (%) | 25 |
| `weekly_ad_budget` | Рекламний бюджет/тиждень (грн) | 10000 |
| `target_roas` | Цільовий ROAS | 3 |

---

## 📁 Структура файлів

```
agents/
├── main.py                  # ← Точка входу (запускай тут)
├── crew.py                  # Визначення команди агентів
├── requirements.txt         # Залежності Python
├── .env.example             # Шаблон конфігурації
├── .gitignore
│
├── config/
│   ├── agents.yaml          # Ролі та характеристики агентів
│   └── tasks.yaml           # Завдання для кожного агента
│
├── tools/
│   └── marketplace_tools.py # Інструменти: пошук цін, аналітика, контент
│
└── data/
    └── weekly_report.md     # ← Тут з'явиться звіт після запуску
```

---

## 🔧 Інструменти агентів

| Інструмент | Опис |
|---|---|
| `search_prom_prices` | Пошук цін на Prom.ua за запитом |
| `analyze_rozetka_competitors` | Аналіз топ-товарів у категорії Rozetka |
| `generate_seo_title` | SEO-оптимізована назва товару |
| `generate_product_description` | Готовий опис за шаблоном маркетплейсу |
| `calculate_margin` | Маржинальність з урахуванням комісії |
| `generate_weekly_report` | KPI-звіт (CTR, конверсія, ROAS, маржа) |
| `analyze_reviews` | Аналіз відгуків + шаблони відповідей |
| `generate_ad_budget_plan` | Розподіл бюджету за стратегією 60/25/15 |

---

## 💡 Часті питання

**Q: Чи потрібен інтернет?**
Для пошуку цін на Rozetka/Prom — так. Для роботи з Ollama — ні (після завантаження моделі).

**Q: Яка модель краща?**
- `gpt-4o` — найрозумніша, але дорожча (~$0.01 за запит)
- `gpt-4o-mini` — оптимальна (~$0.0002 за запит)
- `ollama/llama3` — безкоштовна локальна, трохи менш точна

**Q: Як часто запускати?**
Рекомендовано щодня зранку. Звіт оновлюється в `data/weekly_report.md`.

**Q: Як додати власний агент?**
1. Додай роль у `config/agents.yaml`
2. Додай завдання в `config/tasks.yaml`
3. Зареєструй агент та завдання в `crew.py`

---

## 🛠️ Вимоги до системи

- Python 3.10+
- 4 GB RAM (8 GB з Ollama)
- Ollama (опціонально, для локального LLM)

---

*GYLKA Business AI — автоматизуй рутину, фокусуйся на зростанні.*
