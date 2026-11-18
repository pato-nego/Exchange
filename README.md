# Exchange controllers

Python controllers and API contract for Exchange.

Python service logic belongs in [Exchange-service](https://github.com/pato-nego/Exchange-service), included at `api/exchange-service` in the parent project.

`GET /exchange/{from}/{to}` accepts three-letter currency codes and returns
`sell`, `buy`, `date`, and `id-account`. The rate comes from
[Bacen PTAX](https://insper.github.io/platform/2026.2/exercises/exchange/bacen/).
`/exchanges/{from}/{to}` is also supported. `GET /exchange/currencies` lists the
currencies quoted by PTAX. Run the API behind the gateway, which
authenticates the user and sets the `id-account` header. Keep the Exchange server
on a private network. `just run` from the parent is for local development.
