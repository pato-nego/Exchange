from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Path
from pydantic import BaseModel, Field

from rates import CurrencyPairNotFound, QuoteUnavailable, fetch_quote

app = FastAPI()


class QuoteResponse(BaseModel):
    sell: float
    buy: float
    date: str
    account_id: str = Field(serialization_alias="id-account")


@app.get("/health")
def health():
    return {"message": "Exchange is healthy"}


@app.get("/exchanges/{from}/{to}")
def get_exchange(
    from_currency: Annotated[str, Path(alias="from", pattern=r"^[A-Za-z]{3}$")],
    to_currency: Annotated[str, Path(alias="to", pattern=r"^[A-Za-z]{3}$")],
    account_id: Annotated[str | None, Header(alias="id-account")] = None,
) -> QuoteResponse:
    if not account_id or not account_id.strip():
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        quote = fetch_quote(from_currency, to_currency)
    except CurrencyPairNotFound as exc:
        raise HTTPException(status_code=404, detail="Currency pair not found") from exc
    except QuoteUnavailable as exc:
        raise HTTPException(status_code=502, detail="Exchange rate unavailable") from exc

    return QuoteResponse(**quote, account_id=account_id)
