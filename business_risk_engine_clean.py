import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dataclasses import dataclass, replace


# ============================================================
# CONFIGURATION
# ============================================================

@dataclass
class BusinessConfig:
    # Simulation
    n_simulations: int = 100_000
    months: int = 12
    random_seed: int = 42

    # Demand
    base_students_per_course: int = 12
    student_std: int = 3
    min_students: int = 0
    max_students: int = 30

    # Prices
    weekday_price: float = 45
    weekend_price: float = 55

    # Course schedule
    weekday_courses_per_week: int = 5
    weekend_courses_per_week: int = 2
    weeks_per_month: float = 4.33

    # Variable cost
    freelancer_cost_per_course: float = 350

    # Fixed monthly costs
    monthly_rent: float = 900
    monthly_nebenkosten: float = 250
    monthly_insurance: float = 60
    monthly_accounting: float = 150
    monthly_software: float = 80
    monthly_marketing: float = 500
    monthly_materials: float = 400
    monthly_compliance: float = 150

    # Capital assumptions
    initial_investment: float = 20_000
    starting_cash: float = 50_000
    tax_rate: float = 0.30

    # Unexpected monthly costs
    unexpected_cost_low: int = 100
    unexpected_cost_high: int = 1000

    # Seasonality
    high_season_factor: float = 1.20
    normal_season_factor: float = 1.00
    low_season_factor: float = 0.80

    # Operational shocks
    prob_instructor_cancel: float = 0.10
    instructor_replacement_cost_low: int = 200
    instructor_replacement_cost_high: int = 500

    prob_equipment_failure: float = 0.03
    equipment_cost_low: int = 300
    equipment_cost_high: int = 1000

    prob_marketing_underperformance: float = 0.10
    marketing_demand_factor: float = 0.85


MONTHS = ["jan", "feb", "mar", "apr", "may", "jun",
          "jul", "aug", "sep", "oct", "nov", "dec"]


# ============================================================
# CORE BUSINESS LOGIC
# ============================================================

def fixed_monthly_costs(config: BusinessConfig) -> float:
    return (
        config.monthly_rent
        + config.monthly_nebenkosten
        + config.monthly_insurance
        + config.monthly_accounting
        + config.monthly_software
        + config.monthly_marketing
        + config.monthly_materials
        + config.monthly_compliance
    )


def get_season_factor(month: str, config: BusinessConfig) -> float:
    if month in ["jan", "sep"]:
        return config.high_season_factor
    elif month in ["jul", "aug", "dec"]:
        return config.low_season_factor
    else:
        return config.normal_season_factor


def simulate_one_month(month: str, config: BusinessConfig) -> dict:
    """
    Simulates one month of business activity.

    Includes:
    - seasonality
    - demand uncertainty
    - marketing underperformance
    - unexpected costs
    - instructor cancellation shock
    - equipment failure shock
    - taxes on positive profit
    """

    season_factor = get_season_factor(month, config)
    mean_students = config.base_students_per_course * season_factor

    operational_extra_costs = 0

    # Marketing shock reduces expected demand
    marketing_underperformed = np.random.random() < config.prob_marketing_underperformance
    if marketing_underperformed:
        mean_students *= config.marketing_demand_factor

    # Demand simulation
    students_per_course = round(
        np.random.normal(loc=mean_students, scale=config.student_std)
    )
    students_per_course = max(
        config.min_students,
        min(config.max_students, students_per_course)
    )

    # Unexpected base cost
    unexpected_costs = np.random.randint(
        low=config.unexpected_cost_low,
        high=config.unexpected_cost_high + 1
    )

    # Instructor cancellation shock
    instructor_cancelled = np.random.random() < config.prob_instructor_cancel
    if instructor_cancelled:
        operational_extra_costs += np.random.randint(
            low=config.instructor_replacement_cost_low,
            high=config.instructor_replacement_cost_high + 1
        )

    # Equipment failure shock
    equipment_failed = np.random.random() < config.prob_equipment_failure
    if equipment_failed:
        operational_extra_costs += np.random.randint(
            low=config.equipment_cost_low,
            high=config.equipment_cost_high + 1
        )

    # Monthly students
    weekday_students = round(
        students_per_course
        * config.weekday_courses_per_week
        * config.weeks_per_month
    )

    weekend_students = round(
        students_per_course
        * config.weekend_courses_per_week
        * config.weeks_per_month
    )

    # Revenue
    revenue_weekdays = weekday_students * config.weekday_price
    revenue_weekends = weekend_students * config.weekend_price
    revenue = revenue_weekdays + revenue_weekends

    # Courses
    monthly_weekday_courses = round(
        config.weekday_courses_per_week * config.weeks_per_month
    )
    monthly_weekend_courses = round(
        config.weekend_courses_per_week * config.weeks_per_month
    )
    monthly_courses = monthly_weekday_courses + monthly_weekend_courses

    # Costs
    freelancer_cost = monthly_courses * config.freelancer_cost_per_course
    fixed_costs = fixed_monthly_costs(config)

    profit_before_tax = (
        revenue
        - freelancer_cost
        - fixed_costs
        - unexpected_costs
        - operational_extra_costs
    )

    tax = max(0, profit_before_tax * config.tax_rate)
    profit_after_tax = profit_before_tax - tax

    return {
        "month": month,
        "students_per_course": students_per_course,
        "revenue": revenue,
        "freelancer_cost": freelancer_cost,
        "fixed_costs": fixed_costs,
        "unexpected_costs": unexpected_costs,
        "operational_extra_costs": operational_extra_costs,
        "profit_before_tax": profit_before_tax,
        "tax": tax,
        "profit_after_tax": profit_after_tax,
        "marketing_underperformed": marketing_underperformed,
        "instructor_cancelled": instructor_cancelled,
        "equipment_failed": equipment_failed,
    }


def simulate_one_year(config: BusinessConfig) -> dict:
    """
    Simulates one full year and tracks cash balance,
    ruin probability, cumulative profit, and payback.
    """

    cash = config.starting_cash
    cash_path = [cash]
    monthly_results = []

    ruined = False
    month_of_ruin = None

    cumulative_profit = 0
    payback_month = None

    for month_index, month in enumerate(MONTHS, start=1):
        result = simulate_one_month(month, config)
        monthly_results.append(result)

        monthly_profit = result["profit_after_tax"]
        cumulative_profit += monthly_profit
        cash += monthly_profit
        cash_path.append(cash)

        if cash <= 0 and not ruined:
            ruined = True
            month_of_ruin = month_index

        if cumulative_profit >= config.initial_investment and payback_month is None:
            payback_month = month_index

    cash_path = np.array(cash_path)

    return {
        "cash_path": cash_path,
        "final_cash": cash_path[-1],
        "total_profit": cash_path[-1] - config.starting_cash,
        "ruined": ruined,
        "month_of_ruin": month_of_ruin,
        "payback_month": payback_month,
        "monthly_results": monthly_results,
        "min_cash": cash_path.min(),
    }


# ============================================================
# MONTE CARLO ENGINE
# ============================================================

def run_monte_carlo(config: BusinessConfig) -> dict:
    final_cash = []
    total_profit = []
    ruin_results = []
    months_of_ruin = []
    payback_months = []
    min_cash_values = []
    cash_paths = []

    for _ in range(config.n_simulations):
        year_result = simulate_one_year(config)

        final_cash.append(year_result["final_cash"])
        total_profit.append(year_result["total_profit"])
        ruin_results.append(year_result["ruined"])
        min_cash_values.append(year_result["min_cash"])
        cash_paths.append(year_result["cash_path"])

        if year_result["ruined"]:
            months_of_ruin.append(year_result["month_of_ruin"])

        if year_result["payback_month"] is not None:
            payback_months.append(year_result["payback_month"])

    final_cash = np.array(final_cash)
    total_profit = np.array(total_profit)
    ruin_results = np.array(ruin_results)
    min_cash_values = np.array(min_cash_values)
    cash_paths = np.array(cash_paths)

    metrics = {
        "n_simulations": config.n_simulations,
        "average_final_cash": final_cash.mean(),
        "median_final_cash": np.median(final_cash),
        "average_annual_profit": total_profit.mean(),
        "median_annual_profit": np.median(total_profit),
        "probability_annual_loss": np.mean(total_profit < 0) * 100,
        "probability_ending_below_starting_cash": np.mean(final_cash < config.starting_cash) * 100,
        "probability_of_ruin": np.mean(ruin_results) * 100,
        "worst_5_percent_final_cash": np.percentile(final_cash, 5),
        "best_5_percent_final_cash": np.percentile(final_cash, 95),
        "worst_1_percent_final_cash": np.percentile(final_cash, 1),
        "average_min_cash": min_cash_values.mean(),
        "probability_payback_within_12_months": len(payback_months) / config.n_simulations * 100,
        "average_payback_month": np.mean(payback_months) if len(payback_months) > 0 else None,
        "final_cash_array": final_cash,
        "total_profit_array": total_profit,
        "cash_paths": cash_paths,
    }

    return metrics


def print_metrics(title: str, metrics: dict):
    print(f"\n{title}")
    print("-" * len(title))
    print("Simulations:", metrics["n_simulations"])
    print("Average final cash:", round(metrics["average_final_cash"], 2))
    print("Median final cash:", round(metrics["median_final_cash"], 2))
    print("Average annual profit:", round(metrics["average_annual_profit"], 2))
    print("Median annual profit:", round(metrics["median_annual_profit"], 2))
    print("Probability of annual loss:", round(metrics["probability_annual_loss"], 2), "%")
    print("Probability ending below starting cash:", round(metrics["probability_ending_below_starting_cash"], 2), "%")
    print("Probability of ruin:", round(metrics["probability_of_ruin"], 2), "%")
    print("Worst 5% final cash:", round(metrics["worst_5_percent_final_cash"], 2))
    print("Worst 1% final cash:", round(metrics["worst_1_percent_final_cash"], 2))
    print("Best 5% final cash:", round(metrics["best_5_percent_final_cash"], 2))
    print("Probability of payback within 12 months:", round(metrics["probability_payback_within_12_months"], 2), "%")

    if metrics["average_payback_month"] is not None:
        print("Average payback month:", round(metrics["average_payback_month"], 2))
    else:
        print("Average payback month: No payback occurred")


# ============================================================
# SENSITIVITY ANALYSIS
# ============================================================

def run_sensitivity_analysis(base_config: BusinessConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sensitivity_n = 20_000

    student_values = [8, 10, 12, 15, 20]
    freelancer_values = [250, 300, 350, 400, 500]
    starting_cash_values = [10_000, 15_000, 20_000, 25_000, 30_000, 50_000]

    student_results = []
    freelancer_results = []
    cash_results = []

    for students in student_values:
        config = replace(
            base_config,
            n_simulations=sensitivity_n,
            base_students_per_course=students
        )
        metrics = run_monte_carlo(config)

        student_results.append({
            "base_students": students,
            "average_annual_profit": metrics["average_annual_profit"],
            "probability_annual_loss": metrics["probability_annual_loss"],
            "probability_of_ruin": metrics["probability_of_ruin"],
            "worst_5_percent_final_cash": metrics["worst_5_percent_final_cash"],
            "probability_payback_12m": metrics["probability_payback_within_12_months"],
        })

    for freelancer_cost in freelancer_values:
        config = replace(
            base_config,
            n_simulations=sensitivity_n,
            freelancer_cost_per_course=freelancer_cost
        )
        metrics = run_monte_carlo(config)

        freelancer_results.append({
            "freelancer_cost": freelancer_cost,
            "average_annual_profit": metrics["average_annual_profit"],
            "probability_annual_loss": metrics["probability_annual_loss"],
            "probability_of_ruin": metrics["probability_of_ruin"],
            "worst_5_percent_final_cash": metrics["worst_5_percent_final_cash"],
            "probability_payback_12m": metrics["probability_payback_within_12_months"],
        })

    for starting_cash in starting_cash_values:
        config = replace(
            base_config,
            n_simulations=sensitivity_n,
            starting_cash=starting_cash
        )
        metrics = run_monte_carlo(config)

        cash_results.append({
            "starting_cash": starting_cash,
            "average_annual_profit": metrics["average_annual_profit"],
            "probability_annual_loss": metrics["probability_annual_loss"],
            "probability_of_ruin": metrics["probability_of_ruin"],
            "worst_5_percent_final_cash": metrics["worst_5_percent_final_cash"],
            "probability_payback_12m": metrics["probability_payback_within_12_months"],
        })

    return (
        pd.DataFrame(student_results),
        pd.DataFrame(freelancer_results),
        pd.DataFrame(cash_results)
    )


# ============================================================
# STRATEGY OPTIMIZATION
# ============================================================

def run_strategy_optimization(base_config: BusinessConfig) -> pd.DataFrame:
    optimization_n = 10_000

    base_student_options = [10, 12, 15]
    freelancer_cost_options = [300, 350, 400]
    starting_cash_options = [20_000, 30_000, 50_000]
    weekday_price_options = [45, 50, 55]
    weekend_price_options = [55, 60, 65]

    results = []

    for base_students in base_student_options:
        for freelancer_cost in freelancer_cost_options:
            for starting_cash in starting_cash_options:
                for weekday_price in weekday_price_options:
                    for weekend_price in weekend_price_options:

                        config = replace(
                            base_config,
                            n_simulations=optimization_n,
                            base_students_per_course=base_students,
                            freelancer_cost_per_course=freelancer_cost,
                            starting_cash=starting_cash,
                            weekday_price=weekday_price,
                            weekend_price=weekend_price
                        )

                        metrics = run_monte_carlo(config)

                        average_profit = metrics["average_annual_profit"]
                        downside = metrics["worst_5_percent_final_cash"] - starting_cash
                        ruin_penalty = 10_000 * metrics["probability_of_ruin"]

                        risk_adjusted_score = (
                            average_profit
                            + 0.5 * downside
                            - ruin_penalty
                        )

                        results.append({
                            "base_students": base_students,
                            "freelancer_cost": freelancer_cost,
                            "starting_cash": starting_cash,
                            "weekday_price": weekday_price,
                            "weekend_price": weekend_price,
                            "average_annual_profit": average_profit,
                            "probability_annual_loss": metrics["probability_annual_loss"],
                            "probability_of_ruin": metrics["probability_of_ruin"],
                            "worst_5_percent_final_cash": metrics["worst_5_percent_final_cash"],
                            "probability_payback_12m": metrics["probability_payback_within_12_months"],
                            "risk_adjusted_score": risk_adjusted_score,
                        })

    return pd.DataFrame(results)


# ============================================================
# VISUALIZATION
# ============================================================

def plot_profit_distribution(metrics: dict):
    plt.figure(figsize=(10, 6))
    plt.hist(metrics["total_profit_array"], bins=60)
    plt.axvline(metrics["total_profit_array"].mean(), linestyle="--", label="Mean")
    plt.axvline(np.percentile(metrics["total_profit_array"], 5), linestyle="--", label="5th percentile")
    plt.title("Monte Carlo Distribution of Annual Profit")
    plt.xlabel("Annual Profit After Tax (€)")
    plt.ylabel("Frequency")
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_sample_cash_paths(metrics: dict, n_paths: int = 50):
    cash_paths = metrics["cash_paths"]

    plt.figure(figsize=(10, 6))

    for i in range(min(n_paths, len(cash_paths))):
        plt.plot(cash_paths[i], alpha=0.25)

    plt.title("Sample Simulated 12-Month Cash Paths")
    plt.xlabel("Month")
    plt.ylabel("Cash Balance (€)")
    plt.tight_layout()
    plt.show()


def plot_sensitivity(df: pd.DataFrame, x_col: str, y_col: str, title: str):
    plt.figure(figsize=(9, 5))
    plt.plot(df[x_col], df[y_col], marker="o")
    plt.title(title)
    plt.xlabel(x_col)
    plt.ylabel(y_col)
    plt.tight_layout()
    plt.show()


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)

    config = BusinessConfig()
    np.random.seed(config.random_seed)

    print("Running baseline Monte Carlo simulation...")
    baseline_metrics = run_monte_carlo(config)
    print_metrics("BASELINE BUSINESS RISK RESULTS", baseline_metrics)

    print("\nRunning sensitivity analysis...")
    student_df, freelancer_df, cash_df = run_sensitivity_analysis(config)

    print("\nSENSITIVITY: STUDENTS PER COURSE")
    print(student_df.round(2))

    print("\nSENSITIVITY: FREELANCER COST")
    print(freelancer_df.round(2))

    print("\nSENSITIVITY: STARTING CASH")
    print(cash_df.round(2))

    print("\nRunning strategy optimization...")
    optimization_df = run_strategy_optimization(config)

    acceptable_strategies = optimization_df[
        optimization_df["probability_of_ruin"] < 1.0
    ].copy()

    best_by_profit = acceptable_strategies.sort_values(
        by="average_annual_profit",
        ascending=False
    )

    best_by_risk_adjusted = optimization_df.sort_values(
        by="risk_adjusted_score",
        ascending=False
    )

    print("\nTOP 10 STRATEGIES BY AVERAGE PROFIT WITH RUIN < 1%")
    print(best_by_profit.head(10).round(2))

    print("\nTOP 10 RISK-ADJUSTED STRATEGIES")
    print(best_by_risk_adjusted.head(10).round(2))

    # Optional plots
    plot_profit_distribution(baseline_metrics)
    plot_sample_cash_paths(baseline_metrics, n_paths=50)

    plot_sensitivity(
        student_df,
        x_col="base_students",
        y_col="average_annual_profit",
        title="Sensitivity: Students per Course vs Annual Profit"
    )

    plot_sensitivity(
        freelancer_df,
        x_col="freelancer_cost",
        y_col="average_annual_profit",
        title="Sensitivity: Freelancer Cost vs Annual Profit"
    )

    plot_sensitivity(
        cash_df,
        x_col="starting_cash",
        y_col="probability_of_ruin",
        title="Sensitivity: Starting Cash vs Probability of Ruin"
    )


if __name__ == "__main__":
    main()