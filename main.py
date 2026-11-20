from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Path, Response
from pydantic import BaseModel, Field

from rates import CurrencyPairNotFound, QuoteUnavailable, fetch_currencies, fetch_quote

app = FastAPI()


class QuoteResponse(BaseModel):
    sell: float
    buy: float
    date: str
    account_id: str = Field(serialization_alias="id-account")


@app.get("/exchange/health-check")
@app.get("/health", include_in_schema=False)
def health():
    return {"message": "Exchange is healthy"}


@app.get("/exchange/currencies")
def currencies() -> list[dict[str, str]]:
    try:
        return fetch_currencies()
    except QuoteUnavailable as exc:
        raise HTTPException(status_code=502, detail="Currency list unavailable") from exc


@app.get("/exchange/{from}/{to}")
@app.get("/exchanges/{from}/{to}", include_in_schema=False)
def get_exchange(
    response: Response,
    from_currency: Annotated[str, Path(alias="from", pattern=r"^[A-Za-z]{3}$")],
    to_currency: Annotated[str, Path(alias="to", pattern=r"^[A-Za-z]{3}$")],
    account_id: Annotated[str | None, Header(alias="id-account")] = None,
) -> QuoteResponse:
    if not account_id or not account_id.strip():
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        quote, cache_status = fetch_quote(from_currency, to_currency)
    except CurrencyPairNotFound as exc:
        raise HTTPException(status_code=404, detail="Currency pair not found") from exc
    except QuoteUnavailable as exc:
        raise HTTPException(status_code=502, detail="Exchange rate unavailable") from exc

    response.headers["X-Cache"] = cache_status
    return QuoteResponse(**quote, account_id=account_id)
