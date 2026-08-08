"""
Бізнес-інструменти для GYLKA AI агентів.
Містить функції для аналізу цін, пошуку конкурентів та генерації контенту.
"""

import json
import re
import urllib.parse
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from typing import Optional

from crewai.tools import tool


_ALLOWED_ROZETKA_HOSTS = {"rozetka.com.ua", "www.rozetka.com.ua"}


class _JsonLdParser(HTMLParser):
    """Collect JSON-LD bodies so each name stays paired with its price."""

    def __init__(self) -> None:
        super().__init__()
        self._in_json_ld = False
        self._parts: list[str] = []
        self.documents: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag.lower() != "script":
            return
        attributes = {key.lower(): value for key, value in attrs}
        script_type = attributes.get("type") or ""
        self._in_json_ld = script_type.lower() == "application/ld+json"
        if self._in_json_ld:
            self._parts = []

    def handle_data(self, data: str) -> None:
        if self._in_json_ld:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._in_json_ld:
            self.documents.append("".join(self._parts))
            self._in_json_ld = False
            self._parts = []


def _walk_json(value: object):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _extract_products(html: str, limit: int = 10) -> list[tuple[str, float]]:
    """Extract name/price pairs from the same structured product object."""
    parser = _JsonLdParser()
    parser.feed(html)
    products: list[tuple[str, float]] = []
    for document in parser.documents:
        try:
            payload = json.loads(document)
        except json.JSONDecodeError:
            continue
        for item in _walk_json(payload):
            name = item.get("name") or item.get("title")
            offers = item.get("offers", item)
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            price = offers.get("price") if isinstance(offers, dict) else None
            if not name or price is None:
                continue
            try:
                numeric_price = float(str(price).replace(" ", "").replace(",", "."))
            except ValueError:
                continue
            if numeric_price < 0:
                continue
            products.append((str(name).strip(), numeric_price))
            if len(products) >= limit:
                return products
    return products


def _validate_rozetka_url(category_url: str) -> str:
    parsed = urllib.parse.urlparse(category_url)
    hostname = (parsed.hostname or "").lower()
    if (
        parsed.scheme != "https"
        or hostname not in _ALLOWED_ROZETKA_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
    ):
        raise ValueError("дозволені лише HTTPS-посилання на rozetka.com.ua")
    return category_url


# ---------------------------------------------------------------------------
# Інструменти пошуку та аналізу ринку
# ---------------------------------------------------------------------------

@tool("Пошук цін на Prom.ua")
def search_prom_prices(query: str) -> str:
    """
    Шукає ціни на товари на Prom.ua за пошуковим запитом.
    Повертає список товарів з цінами та назвами продавців.
    Вхідний параметр: назва товару або модель (рядок).
    """
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://prom.ua/search?search_term={encoded}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; GylkaBot/1.0; "
                    "+https://gylkam.github.io)"
                )
            },
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8", errors="ignore")

        products = _extract_products(html)
        results = [f"- {name}: {price:g} грн" for name, price in products]

        if not results:
            return (
                f"Не вдалося знайти ціни для '{query}' на Prom.ua. "
                "Можливо, потрібен ручний перегляд."
            )

        return (
            f"Результати пошуку '{query}' на Prom.ua:\n"
            + "\n".join(results)
        )

    except Exception as exc:  # noqa: BLE001
        return f"Помилка при пошуку '{query}' на Prom.ua: {exc}"


@tool("Аналіз конкурентів на Rozetka")
def analyze_rozetka_competitors(category_url: str) -> str:
    """
    Аналізує топ товари за посиланням на категорію Rozetka.
    Повертає список товарів з цінами та рейтингами.
    Вхідний параметр: URL категорії або пошукового запиту на Rozetka (рядок).
    """
    try:
        if not category_url.startswith("http"):
            query = urllib.parse.quote(category_url)
            category_url = f"https://rozetka.com.ua/ua/search/?text={query}"

        category_url = _validate_rozetka_url(category_url)

        req = urllib.request.Request(
            category_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; GylkaBot/1.0; "
                    "+https://gylkam.github.io)"
                )
            },
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8", errors="ignore")

        products = _extract_products(html)
        results = [f"- {name}: {price:g} грн" for name, price in products]

        if not results:
            return (
                f"Не вдалося отримати дані з Rozetka для '{category_url}'. "
                "Спробуй ввести конкретний запит або перевір URL."
            )

        avg = sum(price for _, price in products) / len(products)
        return (
            f"Топ товари на Rozetka:\n"
            + "\n".join(results)
            + f"\n\nСередня ціна: {avg:.0f} грн"
        )

    except Exception as exc:  # noqa: BLE001
        return f"Помилка при аналізі Rozetka для '{category_url}': {exc}"


# ---------------------------------------------------------------------------
# Інструменти контент-генерації
# ---------------------------------------------------------------------------

@tool("Генератор SEO-назви товару")
def generate_seo_title(product_info: str) -> str:
    """
    Генерує SEO-оптимізовану назву товару для маркетплейсів.
    Вхідний параметр: опис товару або технічні характеристики (рядок).
    Повертає назву до 150 символів з ключовими словами на початку.
    """
    info = product_info.strip()

    keywords = []
    brand_match = re.search(
        r'\b(samsung|apple|lg|xiaomi|bosch|philips|gorenje|'
        r'electrolux|whirlpool|ariston)\b',
        info,
        re.IGNORECASE,
    )
    if brand_match:
        keywords.append(brand_match.group(0).title())

    model_match = re.search(r'\b([A-Z0-9]{3,}[-/][A-Z0-9]+)\b', info)
    if model_match:
        keywords.append(model_match.group(0))

    first_words = " ".join(info.split()[:8])
    # Уникаємо дублювання бренду у назві
    remaining = " ".join(
        w for w in first_words.split()
        if not any(k.lower() == w.lower() for k in keywords)
    )
    title = " ".join(keywords + [remaining]) if keywords else first_words

    if len(title) > 150:
        title = title[:147] + "..."

    return (
        f"SEO-назва (рекомендована):\n{title}\n\n"
        f"Довжина: {len(title)} символів\n"
        "Порада: розмістіть бренд і ключовий запит на початку."
    )


@tool("Генератор опису товару для маркетплейсу")
def generate_product_description(product_name: str, features: str) -> str:
    """
    Створює структурований опис товару за шаблоном маркетплейсу.
    Вхідні параметри: назва товару та список характеристик (через кому).
    Повертає готовий опис українською мовою.
    """
    feature_list = [f.strip() for f in features.split(",") if f.strip()]
    bullets = "\n".join(f"✅ {feat}" for feat in feature_list[:8])

    description = f"""**{product_name}** — ваш надійний вибір!

**Переваги:**
{bullets}

**Чому обирають нас:**
🚚 Швидка доставка по всій Україні
📦 Надійна упаковка, безпечна при транспортуванні
✅ Офіційна гарантія від виробника
🔄 Простий обмін і повернення протягом 14 днів

Замовляйте зараз — і отримайте свій товар вже завтра!"""

    return description


# ---------------------------------------------------------------------------
# Інструменти аналітики та звітності
# ---------------------------------------------------------------------------

@tool("Калькулятор маржинальності SKU")
def calculate_margin(
    selling_price: str,
    purchase_price: str,
    marketplace_fee_percent: Optional[str] = "15",
) -> str:
    """
    Розраховує маржинальність товару з урахуванням комісії маркетплейсу.
    Вхідні параметри:
      - selling_price: ціна продажу (грн)
      - purchase_price: ціна закупівлі (грн)
      - marketplace_fee_percent: комісія маркетплейсу % (за замовчуванням 15)
    """
    try:
        sell = float(selling_price)
        buy = float(purchase_price)
        fee_pct = float(marketplace_fee_percent or 15)

        if sell <= 0:
            raise ValueError("ціна продажу має бути більшою за нуль")
        if buy < 0:
            raise ValueError("ціна закупівлі не може бути від’ємною")
        if not 0 <= fee_pct <= 100:
            raise ValueError("комісія має бути в межах від 0 до 100%")

        fee_amount = sell * fee_pct / 100
        profit = sell - buy - fee_amount
        margin_pct = profit / sell * 100

        status = (
            "🟢 Прибутковий" if margin_pct >= 20
            else "🟡 Прийнятний" if margin_pct >= 10
            else "🔴 Збитковий або занадто низька маржа"
        )

        return (
            f"Аналіз маржинальності:\n"
            f"  Ціна продажу:     {sell:.2f} грн\n"
            f"  Ціна закупівлі:   {buy:.2f} грн\n"
            f"  Комісія ({fee_pct:.0f}%):    {fee_amount:.2f} грн\n"
            f"  Чистий прибуток:  {profit:.2f} грн\n"
            f"  Маржа:            {margin_pct:.1f}%\n"
            f"  Статус:           {status}"
        )
    except ValueError as exc:
        return f"Помилка вводу: {exc}. Введіть числові значення."


@tool("Генератор щотижневого KPI-звіту")
def generate_weekly_report(metrics_json: str) -> str:
    """
    Генерує тижневий KPI-звіт на основі метрик.
    Вхідний параметр: JSON з полями impressions, clicks, orders, revenue,
    ad_spend, purchase_cost (всі числові).
    Повертає форматований звіт з висновками.
    """
    try:
        m = json.loads(metrics_json)
        impressions = float(m.get("impressions", 0))
        clicks = float(m.get("clicks", 0))
        orders = float(m.get("orders", 0))
        revenue = float(m.get("revenue", 0))
        ad_spend = float(m.get("ad_spend", 0))
        purchase_cost = float(m.get("purchase_cost", 0))

        ctr = clicks / impressions * 100 if impressions else 0
        conversion = orders / clicks * 100 if clicks else 0
        roas = revenue / ad_spend if ad_spend else 0
        gross_profit = revenue - purchase_cost - ad_spend
        gross_margin = gross_profit / revenue * 100 if revenue else 0

        now = datetime.now().strftime("%d.%m.%Y")
        return f"""# 📊 KPI-Звіт за тиждень (станом на {now})

## Основні метрики
| Показник        | Значення         |
|-----------------|-----------------|
| Покази          | {impressions:,.0f}       |
| Кліки           | {clicks:,.0f}           |
| CTR             | {ctr:.2f}%           |
| Замовлення      | {orders:,.0f}           |
| Конверсія       | {conversion:.2f}%        |
| Оборот          | {revenue:,.0f} грн      |
| Рекламний бюджет| {ad_spend:,.0f} грн      |
| ROAS            | {roas:.2f}x             |
| Валовий прибуток| {gross_profit:,.0f} грн  |
| Маржа           | {gross_margin:.1f}%      |

## Оцінка результатів
{'✅ CTR відмінний (>2%)' if ctr > 2 else '⚠️ CTR потребує уваги (<2%)'}
{'✅ Конверсія добра (>1%)' if conversion > 1 else '⚠️ Конверсія низька (<1%)'}
{'✅ ROAS прибутковий (>2x)' if roas > 2 else '⚠️ ROAS низький (<2x)'}
{'✅ Маржа здорова (>15%)' if gross_margin > 15 else '🔴 Маржа критично низька!'}
"""
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        return (
            f"Помилка парсингу метрик: {exc}\n"
            "Приклад JSON: "
            '{"impressions":10000,"clicks":300,"orders":15,'
            '"revenue":22500,"ad_spend":3000,"purchase_cost":12000}'
        )


# ---------------------------------------------------------------------------
# Допоміжні інструменти
# ---------------------------------------------------------------------------

@tool("Аналізатор відгуків клієнтів")
def analyze_reviews(reviews_text: str) -> str:
    """
    Аналізує список відгуків клієнтів і виявляє основні теми.
    Вхідний параметр: відгуки через крапку з комою або новий рядок.
    Повертає класифіковані проблеми та рекомендовані відповіді.
    """
    separator = "\n" if "\n" in reviews_text else ";"
    reviews = [r.strip() for r in reviews_text.split(separator) if r.strip()]

    negative_keywords = {
        "доставка": ["довго", "не прийшло", "затримка", "тиждень", "місяць"],
        "якість": ["зламаний", "бракований", "не працює", "тріщина", "підробка"],
        "відповідність": ["не те", "інший", "не відповідає", "опис"],
        "сервіс": ["не відповіли", "ігнорують", "грубо", "відмовили"],
    }

    found_issues: dict[str, int] = {k: 0 for k in negative_keywords}

    for review in reviews:
        review_lower = review.lower()
        for category, words in negative_keywords.items():
            if any(word in review_lower for word in words):
                found_issues[category] += 1

    top_issues = sorted(found_issues.items(), key=lambda x: x[1], reverse=True)
    issues_text = "\n".join(
        f"  - {cat}: {cnt} відгуків" for cat, cnt in top_issues if cnt > 0
    ) or "  Серйозних проблем не виявлено."

    templates = {
        "доставка": (
            "Вибачте за незручності з доставкою. "
            "Ми вже з'ясовуємо ситуацію у службі доставки. "
            "Очікуйте від нас зворотний зв'язок протягом 24 годин."
        ),
        "якість": (
            "Дуже шкода, що товар виявився неякісним. "
            "Просимо надіслати фото браку у повідомленні — "
            "організуємо заміну або повернення коштів."
        ),
        "відповідність": (
            "Перепрошуємо за невідповідність. "
            "Напишіть нам — підберемо правильний варіант "
            "або повернемо кошти без зайвих питань."
        ),
        "сервіс": (
            "Вибачте за некомфортну комунікацію. "
            "Ваш відгук дуже важливий для нас. "
            "Залиште контакт — керівник особисто вирішить питання."
        ),
    }

    active_templates = "\n\n".join(
        f"**Шаблон для '{cat}':**\n> {templates[cat]}"
        for cat, cnt in top_issues
        if cnt > 0 and cat in templates
    ) or "> Відмінно! Більшість відгуків позитивні."

    return f"""## Аналіз відгуків ({len(reviews)} шт.)

### Виявлені проблеми:
{issues_text}

### Готові шаблони відповідей:
{active_templates}

### Рекомендація:
Відповідайте на всі негативні відгуки протягом 24 годин.
Пропонуйте конкретне рішення (заміна / повернення / знижка).
"""


@tool("Генератор плану бюджету на рекламу")
def generate_ad_budget_plan(total_budget: str, sku_count: str) -> str:
    """
    Розподіляє рекламний бюджет між SKU за стратегією 60/25/15.
    Вхідні параметри: загальний бюджет (грн), кількість SKU (число).
    Повертає план розподілу бюджету по групах.
    """
    try:
        budget = float(total_budget)
        skus = int(sku_count)

        if budget < 0:
            raise ValueError("бюджет не може бути від’ємним")
        if skus < 3:
            raise ValueError(
                "для розподілу між трьома групами потрібно щонайменше 3 SKU"
            )

        proven_budget = budget * 0.60
        new_budget = budget * 0.25
        retest_budget = budget * 0.15

        proven_skus = max(1, int(skus * 0.20))
        new_skus = max(1, int(skus * 0.50))
        retest_skus = max(1, skus - proven_skus - new_skus)

        return f"""## 💰 План рекламного бюджету

Загальний бюджет: {budget:,.0f} грн | Кількість SKU: {skus}

| Група                     | SKU  | Бюджет         | На SKU/день |
|---------------------------|------|----------------|-------------|
| 🟢 Перевірені (конверсія) | {proven_skus:4d} | {proven_budget:10,.0f} грн | {proven_budget/proven_skus/7:7.0f} грн |
| 🔵 Новинки (тест)         | {new_skus:4d} | {new_budget:10,.0f} грн | {new_budget/new_skus/7:7.0f} грн |
| 🟡 Ретест (після змін)    | {retest_skus:4d} | {retest_budget:10,.0f} грн | {retest_budget/retest_skus/7:7.0f} грн |

### Правила оптимізації:
- Зупиняти оголошення: ROAS < 1.5x після 3 днів
- Збільшувати бюджет: ROAS > 3x + залишки є
- Переводити до "перевірених": конверсія > 2% за 2 тижні
"""
    except (ValueError, ZeroDivisionError) as exc:
        return f"Помилка вводу: {exc}. Введіть числові значення."


# Список усіх доступних інструментів для використання в crew.py
MARKETPLACE_TOOLS = [
    search_prom_prices,
    analyze_rozetka_competitors,
    generate_seo_title,
    generate_product_description,
    calculate_margin,
    generate_weekly_report,
    analyze_reviews,
    generate_ad_budget_plan,
]
