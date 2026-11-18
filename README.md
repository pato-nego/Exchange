# Exchange controllers

Python controllers and API contract for Exchange.

Python service logic belongs in [Exchange-service](https://github.com/pato-nego/Exchange-service), included at `services/Exchange-service` in the parent project.

`GET /exchanges/{from}/{to}` accepts three-letter currency codes and returns
`sell`, `buy`, `date`, and `id-account`. Run it behind the gateway, which
authenticates the user and sets the `id-account` header. Keep the Exchange server
on a private network. `just run` from the parent is for local development.
