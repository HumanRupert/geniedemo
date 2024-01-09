import itertools

import pypfopt as ppo
import pandas as pd

from src import transform, api, backtest, config

risk_models = [
    (ppo.risk_models.risk_matrix, "sample_cov"),
    (lambda df: ppo.risk_models.CovarianceShrinkage(df).ledoit_wolf(), "ledoit_wolf"),
    (
        lambda df: ppo.risk_models.CovarianceShrinkage(df).oracle_approximating(),
        "oracle_approximating",
    ),
    (ppo.risk_models.exp_cov, "exp_cov"),
]

returns_estimators = [
    (ppo.expected_returns.mean_historical_return, "sample_rets"),
    (ppo.expected_returns.ema_historical_return, "sample_rets_ema"),
]

long_short = [((0, 1), "long"), ((-1, 1), "long_short")]
optimizers = [
    "min_volatility",
]


params = [risk_models, returns_estimators, long_short, optimizers]
grid = list(itertools.product(*params))

for ix, item in enumerate(grid[1:]):
    print(f"{ix} of {len(grid)} done...")
    init = backtest.Initialize(
        get_risk_model=item[0][0],
        get_returns_est=item[1][0],
        optimizer_prop=item[3],
        recalc_weights_per=126,
        rebalance_port_per=21,
        weights_bounds=item[2][0],
        assets=[
            "ETH-USD",
            "USDT-USD",
            "XMR-USD",
            "LTC-USD",
            "BTC-USD",
            "ETC-USD",
            "BCH-USD",
            "XLM-USD",
            "XRP-USD",
            "DOGE-USD",
        ],
    )
    backtest.run(
        f"{item[0][1]}_{item[1][1]}_{item[2][0][0]}_{item[3]}",
        init,
        pd.Timestamp("2017-11-09 00:00:00"),
        pd.Timestamp("2023-07-20 00:00:00"),
        config.RES_DIR,
    )
