"""Contains the logic to setup and execute a backtest"""
import typing as T
import os

import pypfopt as ppo
from zipline.api import order, record, symbol
from zipline import run_algorithm
import zipline as zp
import pandas as pd
import pyfolio as pf
from cvxpy.error import SolverError
from matplotlib.units import ConversionError

from src import transform, config, plotting


class Initialize:
    def __init__(
        self,
        get_risk_model: T.Callable,
        get_returns_est: T.Callable,
        optimizer_prop: str,
        recalc_weights_per: int,
        rebalance_port_per: int,
        weights_bounds: T.Tuple[float, float],
        assets: T.List[str],
    ):
        """Injects parameters as dependencies into zipline's `initialize`, function to facilitate grid search

        Parameters
        ----------
        get_risk_model : `T.Callable`
            https://pyportfolioopt.readthedocs.io/en/latest/RiskModels.html

        get_returns_est : `T.Callable`
            https://pyportfolioopt.readthedocs.io/en/latest/ExpectedReturns.html

        optimizer_prop : `str`
            https://pyportfolioopt.readthedocs.io/en/latest/MeanVariance.html

        recalc_weights_per : `int`
            Period for recalculation of weights (weights will be calculated every n days based on an n-day lookback)

        rebalance_port_per : `int`
            Period for rebalancing portfolio based on calculated weights

        weights_bounds : `T.Tuple[float, float]`
            minimum and maximum weight of each asset OR single min/max pair if all identical, defaults to (0, 1). Must be changed to (-1, 1) for portfolios with shorting.

        assets : `T.List[str]`
            List of assets that will be traded; names must match those used in the zipline bundle
        """
        self.get_risk_model = get_risk_model
        self.get_returns_est = get_returns_est
        self.optimizer_prop = optimizer_prop
        self.recalc_weights_per = recalc_weights_per
        self.rebalance_port_per = rebalance_port_per
        self.weights_bounds = weights_bounds
        self.assets = assets

    def initialize(self, context):
        context.get_risk_model = self.get_risk_model
        context.get_returns_est = self.get_returns_est
        context.optimizer_prop = self.optimizer_prop
        context.recalc_weights_per = self.recalc_weights_per
        context.rebalance_port_per = self.rebalance_port_per
        context.weights_bounds = self.weights_bounds
        context.assets = self.assets
        context.days_since_recalc = 0
        context.days_since_rebalance = 0
        context.i = 0
        context.weights = {}


def _recalc_weights(context, data):
    """Sets `context.weight` based on optimisation parameters passed in `context`"""
    df = transform.zipline2pypfopt(context, data)
    mu = context.get_returns_est(df, compounding=True)
    S = context.get_risk_model(df)
    try:
        ef = ppo.EfficientFrontier(mu, S, weight_bounds=context.weights_bounds)
        optimizer = getattr(ef, context.optimizer_prop)
        optimizer()
    except ValueError as e:
        context.weights = {key: 0.0 for key in df.columns.tolist()}
        print("All expected returns were below RFR. Sell all assets.")
    except SolverError as e:
        context.weights = {key: 0.0 for key in df.columns.tolist()}
        print("All expected returns were below RFR. Sell all assets.")
    else:
        context.weights = ef.clean_weights()
        context.days_since_recalc = 0
        print("Recalculated weights...")
        print(context.weights)
        print("\n \n")


def before_trading_start(context, data):
    context.i += 1
    context.days_since_recalc += 1
    context.days_since_rebalance += 1


def _rebalance(context):
    try:
        for asset in context.assets:
            w = context.weights[asset]
            zp.api.order_target_percent(symbol(asset), w)
        context.days_since_rebalance = 0
    except OverflowError as e:
        # the error triggers when portfolio value is extremely negative
        # if gets to this point, strategy can be safely discarded
        print("!!!Things are pretty bad. Lost too much money!!!")
        context.days_since_rebalance = 0


def handle_data(context, data):
    if context.i <= max(context.recalc_weights_per, context.rebalance_port_per):
        print("Bootstrapping...")
        return

    if context.days_since_recalc >= context.recalc_weights_per:
        _recalc_weights(context, data)

    if context.days_since_rebalance >= context.rebalance_port_per:
        _rebalance(context)


def run(
    name: str,
    init: Initialize,
    start: pd.Timestamp,
    end: pd.Timestamp,
    savedir: str = config.RES_DIR,
):
    result = run_algorithm(
        start=start,
        end=end,
        initialize=init.initialize,
        handle_data=handle_data,
        before_trading_start=before_trading_start,
        capital_base=config.CAPITAL_BASE,
        bundle=config.ZP_BUNDLE,
        data_frequency="daily",
    )
    returns, positions, transactions = pf.utils.extract_rets_pos_txn_from_zipline(
        result
    )
    returns_tearsheet = plotting.create_returns_tear_sheet(
        returns, positions=positions, transactions=transactions, return_fig=True
    )
    returns_tearsheet.savefig(f"{savedir}/{name}.png")
