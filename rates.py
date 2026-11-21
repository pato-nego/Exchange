import os
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from math import isfinite
from threading import Lock
from time import monotonic
from typing import NamedTuple

import requests

PTAX_URL = os.getenv(
    "PTAX_URL", "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata"
).rstrip("/")
PTAX_TIMEOUT = float(os.getenv("PTAX_TIMEOUT", "3"))
CACHE_SECONDS = float(os.getenv("CACHE_SECONDS", "300"))
RETRY_SECONDS = float(os.getenv("RETRY_SECONDS", "30"))
BRASILIA_TIME = timezone(timedelta(hours=-3))


class CurrencyPairNotFound(Exception):
    pass


class QuoteUnavailable(Exception):
    pass


class BrlQuote(NamedTuple):
    buy: float
    sell: float
    date: str


class CacheEntry(NamedTuple):
    quote: BrlQuote
    expires_at: float
    status: str


_quotes: dict[str, CacheEntry] = {}
_locks = defaultdict(Lock)


def _fetch_rows(endpoint: str, **params: str) -> list[dict]:
    try:
        response = requests.get(
            f"{PTAX_URL}/{endpoint}",
            params={"$format": "json", **params},
            timeout=PTAX_TIMEOUT,
        )
        response.raise_for_status()
        rows = response.json()["value"]
        if not isinstance(rows, list):
            raise TypeError("Expected a list of PTAX records")
    except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
        raise QuoteUnavailable("PTAX request failed") from exc
    return rows


def _latest_brl_quote(currency: str) -> BrlQuote:
    today = datetime.now(BRASILIA_TIME).date()
    since = today - timedelta(days=7)
    rows = _fetch_rows(
        "CotacaoMoedaPeriodo(moeda=@moeda,dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)",
        **{
            "@moeda": f"'{currency}'",
            "@dataInicial": f"'{since:%m-%d-%Y}'",
            "@dataFinalCotacao": f"'{today:%m-%d-%Y}'",
            "$select": "cotacaoCompra,cotacaoVenda,dataHoraCotacao",
        },
    )
    if not rows:
        raise CurrencyPairNotFound(currency)
    try:
        bulletin = max(rows, key=lambda row: row["dataHoraCotacao"])
        buy = float(bulletin["cotacaoCompra"])
        sell = float(bulletin["cotacaoVenda"])
        published_at = datetime.fromisoformat(bulletin["dataHoraCotacao"])
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise QuoteUnavailable(currency) from exc
    if not all(isfinite(rate) and rate > 0 for rate in (buy, sell)):
        raise QuoteUnavailable(currency)
    return BrlQuote(buy, sell, published_at.isoformat(sep=" ", timespec="seconds"))


def _brl_quote(currency: str) -> tuple[BrlQuote, str]:
    if currency == "BRL":
        return BrlQuote(1.0, 1.0, ""), "hit"
    with _locks[currency]:
        cached = _quotes.get(currency)
        if cached and monotonic() < cached.expires_at:
            return cached.quote, cached.status
        try:
            quote = _latest_brl_quote(currency)
        except QuoteUnavailable:
            if cached is None:
                raise
            _quotes[currency] = CacheEntry(cached.quote, monotonic() + RETRY_SECONDS, "stale")
            return cached.quote, "stale"
        _quotes[currency] = CacheEntry(quote, monotonic() + CACHE_SECONDS, "hit")
        return quote, "miss"


def fetch_quote(from_currency: str, to_currency: str) -> tuple[dict, str]:
    source, target = from_currency.upper(), to_currency.upper()
    if not re.fullmatch(r"[A-Z]{3}-[A-Z]{3}", f"{source}-{target}"):
        raise ValueError("Use three-letter currency codes, such as USD and BRL")

    source_quote, source_status = _brl_quote(source)
    target_quote, target_status = _brl_quote(target)
    statuses = (source_status, target_status)
    cache_status = next(status for status in ("miss", "stale", "hit") if status in statuses)
    date = source_quote.date or target_quote.date
    if source == target:
        date = date or datetime.now(BRASILIA_TIME).date().isoformat()
        return {"sell": 1.0, "buy": 1.0, "date": date}, cache_status

    rates = {
        "sell": round(source_quote.sell / target_quote.buy, 6),
        "buy": round(source_quote.buy / target_quote.sell, 6),
        "date": date,
    }
    return rates, cache_status


def fetch_currencies() -> list[dict[str, str]]:
    rows = _fetch_rows("Moedas", **{"$select": "simbolo,nomeFormatado"})
    try:
        return [{"symbol": row["simbolo"], "name": row["nomeFormatado"]} for row in rows]
    except (KeyError, TypeError) as exc:
        raise QuoteUnavailable("Invalid PTAX currency list") from exc
