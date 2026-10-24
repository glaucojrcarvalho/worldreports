"""Offline verification for Ukraine source-discovery safeguards.

Run: python3 -m unittest discover -s countries/ukraine/tests -v
No external services, network or third-party libraries are required.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "fetch" / "probe_sources.py"
spec = importlib.util.spec_from_file_location("ukraine_probe_sources", SOURCE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class SourceDiscoveryTests(unittest.TestCase):
    def test_dataflows_parse_both_locales_and_dsd(self):
        raw = b"""<Message xmlns:s="urn:test:s" xmlns:c="urn:test:c">
           <s:Dataflow agencyID="SSSU" id="DF_GDP_EXAMPLE" version="1.0.0">
             <c:Name xml:lang="uk">GDP UK</c:Name>
             <c:Name xml:lang="en">Example GDP</c:Name>
             <s:Structure><Ref class="DataStructure" id="DSD_GDP"/></s:Structure>
           </s:Dataflow></Message>"""
        flows = probe.parse_dataflows(raw)
        self.assertEqual(len(flows), 1)
        self.assertEqual(flows[0]["id"], "DF_GDP_EXAMPLE")
        self.assertEqual(flows[0]["name_en"], "Example GDP")
        self.assertEqual(flows[0]["dsd"], "DSD_GDP")

    def test_dataflows_missing_or_corrupt_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "No SDMX Dataflow"):
            probe.parse_dataflows(b"<Message/>")
        with self.assertRaisesRegex(ValueError, "Invalid SSSU"):
            probe.parse_dataflows(b"<html")

    def test_nbu_official_url_and_date_validation(self):
        url = probe.make_fx_url("20220104", "20220110", "USD")
        self.assertIn("start=20220104", url)
        self.assertIn("end=20220110", url)
        self.assertIn("valcode=usd", url)
        self.assertTrue(url.endswith("&json"))
        with self.assertRaises(ValueError):
            probe.make_fx_url("20220111", "20220110")
        with self.assertRaises(ValueError):
            probe.make_fx_url("20220104", "20220110", "US-D")

    def test_nbu_fx_rate_per_unit(self):
        raw = b'[{"exchangedate":"05.05.2022","cc":"USD","rate":29.2549,"units":1,"rate_per_unit":29.2549}]'
        values = probe.parse_fx(raw, start="20220505", end="20220505")
        self.assertEqual(values[0]["date"], "2022-05-05")
        self.assertAlmostEqual(values[0]["uah_per_unit"], 29.2549)

    def test_nbu_fx_units_are_normalized_explicitly(self):
        raw = b'[{"exchangedate":"05.05.2022","cc":"USD","rate":290.0,"units":10}]'
        values = probe.parse_fx(raw)
        self.assertAlmostEqual(values[0]["uah_per_unit"], 29.0)

    def test_nbu_fx_rejects_bad_shape_currency_and_date(self):
        for raw in [
            b"<html>error 200</html>",
            b'{"error":"blocked"}',
            b'[]',
            b'[{"exchangedate":"05.05.2022","cc":"EUR","rate":29.2549}]',
            b'[{"exchangedate":"05.05.2022","cc":"USD","rate":0}]',
            b'[{"exchangedate":"05.05.2022","cc":"USD","rate":29.2549,"units":0}]',
        ]:
            with self.subTest(payload=raw), self.assertRaises(ValueError):
                probe.parse_fx(raw)
        with self.assertRaisesRegex(ValueError, "outside requested"):
            probe.parse_fx(b'[{"exchangedate":"05.05.2022","cc":"USD","rate":29.2549}]',
                           start="20220601")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            probe.parse_fx(b'[{"exchangedate":"05.05.2022","cc":"USD","rate":29.2},'
                           b'{"exchangedate":"05.05.2022","cc":"USD","rate":29.2}]')

    def test_gini_keeps_missing_observations(self):
        good = {2021: 0.244, 2022: None, 2023: None, 2024: None, 2025: None}
        probe.validate_gini(good)
        for value in [0.0, 0.244]:
            broken = dict(good, **{})  # copy without modifying shared fixture
            broken[2023] = value
            with self.assertRaises(ValueError):
                probe.validate_gini(broken)
        del good[2025]
        with self.assertRaises(ValueError):
            probe.validate_gini(good)

    def test_gdp_spine_exceedance_is_not_hidden(self):
        self.assertTrue(probe.growth_requires_shared_scale_review())
        self.assertLess(probe.GDP_2022_OFFICIAL, probe.GDP_SHARED_SCALE[0])

    def test_live_failures_remain_unverified(self):
        with patch.object(probe, "download", side_effect=OSError("offline")):
            report = probe.run_live()
        probes = report["source_probes"]
        self.assertEqual(probes["sssu_dataflow_catalog"]["result"], "unverified")
        self.assertEqual(probes["nbu_usd_fx"]["result"], "unverified")
        self.assertTrue(probes["gdp_anchor"]["shared_scale_review_required"])
        self.assertEqual(report["status"], "discovery_only_not_accepted_data")


if __name__ == "__main__":
    unittest.main()
