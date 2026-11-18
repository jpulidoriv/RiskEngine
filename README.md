# Monte Carlo Business Risk Engine

A course provider pays instructors per class, while its revenue depends on how many students attend. This Python model simulates the first year of operations to estimate annual profit, the risk of running out of cash and the chance of recovering the initial investment.

## How the simulation works

Each simulated month starts with an enrollment estimate that varies by season. Weekday and weekend classes have separate prices. The model deducts instructor fees and fixed expenses, samples occasional costs such as replacing an instructor or repairing equipment, and applies tax to positive monthly profit. The remaining profit or loss rolls into the next month’s cash balance.

The baseline runs 100,000 simulated years. It records a cash shortfall whenever the month-end balance reaches zero or falls below it, even if the business later finishes the year in profit. Payback occurs in the first month when cumulative after-tax profit covers the initial investment.

## Comparing operating decisions

The sensitivity analysis varies attendance, instructor fees and starting cash one at a time. A separate grid search compares 243 combinations of those assumptions and weekday and weekend prices, using 10,000 simulated years per combination. One ranking shows which strategies earn the highest average profit while keeping the estimated probability of a cash shortfall below 1%. A second ranking also accounts for the fifth percentile of year-end cash, giving more weight to what happens in a poor year.

[Simulation and analysis](business_risk_engine_clean.py)
