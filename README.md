# Monte Carlo business risk engine

How much cash does a course provider need to survive a weak year? This Python model simulates twelve months of enrollment, revenue and operating costs. It tracks the entire cash path so a business that runs out of money midyear is counted even if it later recovers.

## What the model measures

| Question | Measure |
| --- | --- |
| How profitable is a typical year? | Mean and median after-tax annual profit |
| How much downside can the business absorb? | Probability of reaching zero cash at any month-end, plus the 5th and 1st percentiles of ending cash |
| When is the investment recovered? | First month cumulative after-tax profit covers the initial investment |

Seasonal demand, instructor cancellations, equipment failures and marketing underperformance vary across simulations. Prices, enrollment, freelancer costs and starting capital are configurable in [BusinessConfig](business_risk_engine_clean.py).

## Run a small example

From the repository root, install the dependencies in a Python virtual environment.

```bash
python -m pip install numpy pandas matplotlib
```

```python
import numpy as np
from business_risk_engine_clean import BusinessConfig, run_monte_carlo

config = BusinessConfig(n_simulations=1_000)
np.random.seed(config.random_seed)
results = run_monte_carlo(config)
print(round(results["average_annual_profit"], 2))
print(round(results["worst_5_percent_final_cash"], 2))
```

With the default assumptions and seed, this example produced average annual profit of 21,040.35 and a fifth-percentile ending balance of 49,202.10 from 50,000 in starting cash. These figures illustrate the assumptions of the model.

## Run the full study

```bash
python business_risk_engine_clean.py
```

The full run starts with 100,000 baseline years, varies enrollment, instructor costs and starting cash individually, then compares 243 operating strategies with 10,000 simulations per strategy. It prints strategy rankings and displays profit distributions, sample cash paths and sensitivity plots.
