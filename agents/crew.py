"""
GYLKA Business AI — визначення Crew (команди агентів).
"""

from pathlib import Path

import yaml
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from tools.marketplace_tools import (
    analyze_reviews,
    analyze_rozetka_competitors,
    calculate_margin,
    generate_ad_budget_plan,
    generate_product_description,
    generate_seo_title,
    generate_weekly_report,
    search_prom_prices,
)

_CONFIG_DIR = Path(__file__).parent / "config"


@CrewBase
class GylkaBusinessCrew:
    """
    GYLKA Business AI Crew — команда з 7 спеціалізованих агентів
    для автоматизації та зростання маркетплейс-бізнесу.

    Декоратор @CrewBase автоматично завантажує YAML-файли, вказані в
    agents_config / tasks_config, і робить їх доступними як словники
    (self.agents_config["..."], self.tasks_config["..."]).
    """

    agents_config = str(_CONFIG_DIR / "agents.yaml")
    tasks_config = str(_CONFIG_DIR / "tasks.yaml")

    # ------------------------------------------------------------------
    # Агенти
    # ------------------------------------------------------------------

    @agent
    def business_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config["business_strategist"],
            tools=[
                generate_weekly_report,
                calculate_margin,
                generate_ad_budget_plan,
            ],
            verbose=True,
        )

    @agent
    def market_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["market_researcher"],
            tools=[
                search_prom_prices,
                analyze_rozetka_competitors,
            ],
            verbose=True,
        )

    @agent
    def content_creator(self) -> Agent:
        return Agent(
            config=self.agents_config["content_creator"],
            tools=[
                generate_seo_title,
                generate_product_description,
            ],
            verbose=True,
        )

    @agent
    def pricing_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["pricing_analyst"],
            tools=[
                calculate_margin,
                search_prom_prices,
                analyze_rozetka_competitors,
            ],
            verbose=True,
        )

    @agent
    def customer_relations_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["customer_relations_manager"],
            tools=[analyze_reviews],
            verbose=True,
        )

    @agent
    def analytics_expert(self) -> Agent:
        return Agent(
            config=self.agents_config["analytics_expert"],
            tools=[
                generate_weekly_report,
                calculate_margin,
            ],
            verbose=True,
        )

    @agent
    def advertising_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["advertising_manager"],
            tools=[
                generate_ad_budget_plan,
                analyze_rozetka_competitors,
                search_prom_prices,
            ],
            verbose=True,
        )

    # ------------------------------------------------------------------
    # Завдання
    # ------------------------------------------------------------------

    @task
    def daily_market_research(self) -> Task:
        return Task(config=self.tasks_config["daily_market_research"])

    @task
    def content_optimization(self) -> Task:
        return Task(config=self.tasks_config["content_optimization"])

    @task
    def pricing_strategy(self) -> Task:
        return Task(config=self.tasks_config["pricing_strategy"])

    @task
    def advertising_plan(self) -> Task:
        return Task(config=self.tasks_config["advertising_plan"])

    @task
    def customer_feedback_analysis(self) -> Task:
        return Task(config=self.tasks_config["customer_feedback_analysis"])

    @task
    def weekly_analytics_report(self) -> Task:
        return Task(
            config=self.tasks_config["weekly_analytics_report"],
            output_file="data/weekly_report.md",
        )

    # ------------------------------------------------------------------
    # Crew
    # ------------------------------------------------------------------

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
