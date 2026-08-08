import importlib.util
import sys
import types
import unittest
from pathlib import Path


def _identity_tool(_name):
    return lambda function: function


crewai = types.ModuleType("crewai")
crewai_tools = types.ModuleType("crewai.tools")
crewai_tools.tool = _identity_tool
crewai.tools = crewai_tools
sys.modules.setdefault("crewai", crewai)
sys.modules.setdefault("crewai.tools", crewai_tools)

MODULE_PATH = Path(__file__).parents[1] / "tools" / "marketplace_tools.py"
SPEC = importlib.util.spec_from_file_location("marketplace_tools", MODULE_PATH)
marketplace_tools = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(marketplace_tools)


class ProductExtractionTests(unittest.TestCase):
    def test_extracts_name_and_price_from_same_json_ld_product(self):
        html = """
        <script type="application/ld+json">
        {"@type":"ItemList","itemListElement":[
          {"@type":"Product","name":"Стіл GYLKA","offers":{"price":"1250.50"}},
          {"@type":"Product","name":"Шафа GYLKA","offers":{"price":3400}}
        ]}
        </script>
        """
        self.assertEqual(
            marketplace_tools._extract_products(html),
            [("Стіл GYLKA", 1250.5), ("Шафа GYLKA", 3400.0)],
        )

    def test_does_not_zip_unrelated_name_and_price_fields(self):
        html = '<div>"name":"Товар"</div><div>"price":"999"</div>'
        self.assertEqual(marketplace_tools._extract_products(html), [])


class UrlValidationTests(unittest.TestCase):
    def test_accepts_rozetka_https_url(self):
        url = "https://rozetka.com.ua/ua/search/?text=table"
        self.assertEqual(marketplace_tools._validate_rozetka_url(url), url)

    def test_rejects_non_rozetka_and_local_urls(self):
        for url in (
            "http://rozetka.com.ua/ua/",
            "https://example.com/",
            "https://127.0.0.1/admin",
            "https://rozetka.com.ua@example.com/",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                marketplace_tools._validate_rozetka_url(url)


class FinancialValidationTests(unittest.TestCase):
    def test_margin_rejects_zero_selling_price(self):
        result = marketplace_tools.calculate_margin("0", "10")
        self.assertIn("більшою за нуль", result)

    def test_margin_rejects_negative_purchase_price(self):
        result = marketplace_tools.calculate_margin("100", "-1")
        self.assertIn("не може бути від’ємною", result)

    def test_margin_rejects_invalid_fee(self):
        result = marketplace_tools.calculate_margin("100", "50", "101")
        self.assertIn("від 0 до 100", result)

    def test_budget_requires_three_skus(self):
        result = marketplace_tools.generate_ad_budget_plan("1000", "2")
        self.assertIn("щонайменше 3 SKU", result)


if __name__ == "__main__":
    unittest.main()
