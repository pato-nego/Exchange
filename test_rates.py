import unittest
from unittest.mock import patch

import requests

import rates


class PtaxTests(unittest.TestCase):
    def setUp(self):
        rates._quotes.clear()

    def test_cross_rate_and_cache(self):
        date = "2026-11-13 13:03:27"
        with patch.object(rates, "_latest_brl_quote") as load:
            load.side_effect = [rates.BrlQuote(5.0, 5.1, date), rates.BrlQuote(5.5, 5.6, date)]
            quote, status = rates.fetch_quote("USD", "EUR")
            self.assertEqual(quote, {"buy": 0.892857, "sell": 0.927273, "date": date})
            self.assertEqual(status, "miss")
            self.assertEqual(rates.fetch_quote("USD", "EUR"), (quote, "hit"))
            self.assertEqual(load.call_count, 2)

    def test_latest_bulletin_and_stale_fallback(self):
        date = "2026-11-13 13:03:27"
        rows = [
            {"cotacaoCompra": 5.0, "cotacaoVenda": 5.1, "dataHoraCotacao": date + ".123"},
            {"cotacaoCompra": 4.9, "cotacaoVenda": 5.0, "dataHoraCotacao": "2026-11-12 13:00:00"},
        ]
        with patch.object(rates.requests, "get") as get, patch.object(rates, "monotonic") as clock:
            clock.return_value = 0
            get.return_value.json.return_value = {"value": rows}
            quote, status = rates.fetch_quote("USD", "BRL")
            self.assertEqual(quote, {"buy": 5.0, "sell": 5.1, "date": date})
            self.assertEqual(status, "miss")
            self.assertEqual(get.call_args.kwargs["params"]["@moeda"], "'USD'")
            clock.return_value = rates.CACHE_SECONDS + 1
            get.side_effect = requests.Timeout
            self.assertEqual(rates.fetch_quote("USD", "BRL"), (quote, "stale"))
            self.assertEqual(rates.fetch_quote("USD", "BRL"), (quote, "stale"))
            self.assertEqual(get.call_count, 2)

    def test_distinguishes_unknown_currency_from_provider_failure(self):
        with patch.object(rates.requests, "get") as get:
            get.return_value.json.return_value = {"value": []}
            with self.assertRaises(rates.CurrencyPairNotFound):
                rates.fetch_quote("XYZ", "BRL")
            get.side_effect = requests.Timeout
            with self.assertRaises(rates.QuoteUnavailable):
                rates.fetch_quote("USD", "BRL")
