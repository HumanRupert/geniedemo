"""Contains the logic for fetching, caching, and retrieving data"""

import os
import typing as T

import coinmarketcapapi as cmc
from dotenv import load_dotenv
import pandas as pd
import yfinance as yf
from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from pyrate_limiter import Duration, RequestRate, Limiter

from src.config import CACHE_DIR

load_dotenv()

cmc_sess: cmc.CoinMarketCapAPI = cmc.CoinMarketCapAPI(
    os.environ["COINMARKETCAP_API_KEY"]
)


class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
    pass


yf_sess = CachedLimiterSession(
    limiter=Limiter(RequestRate(2, Duration.SECOND * 5)),
    bucket_class=MemoryQueueBucket,
    backend=SQLiteCache("yfinance.cache"),
)


def fetch_candidates(limit: int = 20, sort: str = "market_cap") -> T.List[T.Dict]:
    try:
        res = cmc_sess.cryptocurrency_listings_latest(limit=limit, sort=sort)
        return res.data
    except cmc.CoinMarketCapAPIError as e:
        print(str(e))


def _fetch_ohlcv_from_yf(
    symbols: T.List[str],
    period: str,
    currency: str,
) -> pd.DataFrame:
    yf_symbols = [f"{s}-{currency}" for s in symbols]
    df = yf.download(yf_symbols, group_by="Ticker", period=period, session=yf_sess)
    return df


def fetch_ohlcv(
    symbols: T.List[str] = None,
    reset_cache: bool = False,
    period: str = "max",
    currency: str = "USD",
    cache_dir: str = CACHE_DIR,
) -> pd.DataFrame:
    if reset_cache:
        df = _fetch_ohlcv_from_yf(symbols, period, currency)
        df.to_pickle(cache_dir)
        return df
    else:
        return pd.read_pickle(cache_dir)
