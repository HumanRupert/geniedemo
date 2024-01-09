from pyfolio import plotting
from matplotlib import pyplot as plt
import matplotlib.gridspec as gridspec


@plotting.customize
def create_returns_tear_sheet(
    returns,
    positions=None,
    transactions=None,
    live_start_date=None,
    cone_std=(1.0, 1.5, 2.0),
    bootstrap=False,
    turnover_denom="AGB",
    header_rows=None,
    return_fig=False,
):
    vertical_sections = 8

    if live_start_date is not None:
        vertical_sections += 1
        live_start_date = ep.utils.get_utc_timestamp(live_start_date)

    if bootstrap:
        vertical_sections += 1

    fig = plt.figure(figsize=(14, vertical_sections * 4))
    gs = gridspec.GridSpec(vertical_sections, 3, wspace=0.5, hspace=0.5)
    ax_rolling_returns = plt.subplot(gs[:2, :])

    i = 2
    ax_rolling_returns_log = plt.subplot(gs[i, :], sharex=ax_rolling_returns)
    i += 1
    ax_returns = plt.subplot(gs[i, :], sharex=ax_rolling_returns)
    i += 1
    ax_rolling_volatility = plt.subplot(gs[i, :], sharex=ax_rolling_returns)
    i += 1
    ax_rolling_sharpe = plt.subplot(gs[i, :], sharex=ax_rolling_returns)
    i += 1
    ax_monthly_heatmap = plt.subplot(gs[i, 0])
    ax_annual_returns = plt.subplot(gs[i, 1])
    ax_monthly_dist = plt.subplot(gs[i, 2])
    i += 1
    ax_return_quantiles = plt.subplot(gs[i, :])
    i += 1

    plotting.plot_rolling_returns(
        returns,
        factor_returns=None,
        live_start_date=live_start_date,
        cone_std=cone_std,
        ax=ax_rolling_returns,
    )
    ax_rolling_returns.set_title("Cumulative returns")

    plotting.plot_rolling_returns(
        returns,
        factor_returns=None,
        logy=True,
        live_start_date=live_start_date,
        cone_std=cone_std,
        ax=ax_rolling_returns_log,
    )
    ax_rolling_returns_log.set_title("Cumulative returns on logarithmic scale")

    plotting.plot_returns(
        returns,
        live_start_date=live_start_date,
        ax=ax_returns,
    )
    ax_returns.set_title("Returns")
    plotting.plot_rolling_volatility(
        returns, factor_returns=None, ax=ax_rolling_volatility
    )

    plotting.plot_rolling_sharpe(returns, ax=ax_rolling_sharpe)

    plotting.plot_monthly_returns_heatmap(returns, ax=ax_monthly_heatmap)
    plotting.plot_annual_returns(returns, ax=ax_annual_returns)
    plotting.plot_monthly_returns_dist(returns, ax=ax_monthly_dist)

    plotting.plot_return_quantiles(
        returns, live_start_date=live_start_date, ax=ax_return_quantiles
    )

    for ax in fig.axes:
        ax.tick_params(
            axis="x",
            which="major",
            bottom=True,
            top=False,
            labelbottom=True,
        )

    if return_fig:
        return fig
