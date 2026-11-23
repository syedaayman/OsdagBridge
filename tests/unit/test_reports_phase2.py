"""Unit tests for Phase 2: Chapter 3 — Vehicle Live Loads & Footway Live Load Restructuring."""

import pytest
import re

from osdagbridge.core.reports.chap3 import ch3_loads
from osdagbridge.core.reports.report_utils import apply_longtable_repeating_headers
from osdagbridge.core.utils.common import (
    KEY_SPAN,
    KEY_FOOTPATH,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_NO_OF_FOOTPATHS,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_CLASS_SV,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
)


def _base_payload():
    """Returns a minimal valid input dictionary for Chapter 3."""
    return {
        KEY_SPAN: 30.0,
        KEY_WC_LD_LANE_TABLE_COUNT: 2,
        KEY_FOOTPATH: "None",
    }


class TestPhase2LiveLoads:
    """Test suite for restructured Chapter 3 Vehicle Live Loads and Footway Live Load."""

    def test_dynamic_vehicle_filtering_all_checked(self):
        """All IRC 6 vehicle options are checked; all 8 should appear with impact factors."""
        payload = _base_payload()
        payload.update({
            KEY_LL_IRC_CLASS_A: True,
            KEY_LL_IRC_70R_WHEELED: True,
            KEY_LL_IRC_70R_TRACKED: True,
            KEY_LL_IRC_AA_WHEELED: True,
            KEY_LL_IRC_AA_TRACKED: True,
            KEY_LL_IRC_70R_BOGIE: True,
            KEY_LL_IRC_CLASS_SV: True,
            KEY_LL_IRC_CLASS_FATIGUE: True,
        })
        tex = ch3_loads(payload)

        # Confirm dedicated table headers
        assert r"\caption{\textbf{Vehicle Live Loads (IRC 6)}}" in tex
        assert r"\caption{\textbf{Footway Live Load (IRC 6 Cl. 206.1)}}" in tex

        # Verify all vehicle names are present in Vehicles Considered
        for v in [
            "Class A", "Class 70R (Wheeled)", "Class 70R (Tracked)",
            "Class AA (Wheeled)", "Class AA (Tracked)", "Class 70R (Bogie)",
            "Class SV", "Class Fatigue"
        ]:
            assert v in tex
            assert f"Impact Factor --- {v}" in tex

        # Impact factor values for span = 30m:
        # Class A: 9 / (13.5 + 30) = 0.207 -> 1.207
        assert "1.207 (IM = 20.7\\%, IRC 6 Cl. 208.2)" in tex
        # Class 70R (Tracked): 10% for span >= 5m -> 1.100
        assert "1.100 (IM = 10.0\\%, IRC 6 Cl. 208.3)" in tex
        # Class SV: No impact allowance
        assert "1.000 (No dynamic impact allowance, IRC 6 Cl. 204.6)" in tex
        # Class Fatigue: Static/fatigue
        assert "1.000 (Static / Fatigue verification, IRC 6 Cl. 204.5)" in tex

    def test_dynamic_vehicle_filtering_subset_unchecked(self):
        """Unchecked vehicles (e.g. Class SV and Class Fatigue) must NOT appear."""
        payload = _base_payload()
        payload.update({
            KEY_LL_IRC_CLASS_A: True,
            KEY_LL_IRC_70R_WHEELED: True,
            KEY_LL_IRC_CLASS_SV: False,
            KEY_LL_IRC_CLASS_FATIGUE: "false",
        })
        tex = ch3_loads(payload)

        # Selected vehicles must be present
        assert "Class A" in tex
        assert "Class 70R (Wheeled)" in tex
        assert "Impact Factor --- Class A" in tex
        assert "Impact Factor --- Class 70R (Wheeled)" in tex

        # Unselected vehicles must NOT appear in the table
        assert "Class SV" not in tex
        assert "Class Fatigue" not in tex
        assert "Impact Factor --- Class SV" not in tex
        assert "Impact Factor --- Class Fatigue" not in tex

    def test_no_vehicles_checked_edge_case(self):
        """When no vehicles are checked, report shows 'None' and 'N/A' gracefully."""
        payload = _base_payload()
        # All vehicle flags omitted / false
        payload.update({
            KEY_LL_IRC_CLASS_A: False,
            KEY_LL_IRC_70R_WHEELED: False,
        })
        tex = ch3_loads(payload)

        assert r"\textnormal{Vehicles Considered} & None" in tex
        assert r"\textnormal{Impact Factor (IRC 6)} & N/A" in tex
        # Must still render valid LaTeX table
        assert r"\begin{longtable}{|L{5.5cm}|p{10.0cm}|}" in tex

    def test_custom_vehicles_handling(self):
        """Custom vehicles are dynamically included with user-defined impact factors."""
        payload = _base_payload()
        payload.update({
            KEY_LL_IRC_CLASS_A: True,
            KEY_LL_CUSTOM_VEHICLES: [
                {
                    "name": "Heavy Transporter 120t",
                    "impact_factor": 1.15,
                    "checked": True,
                },
                {
                    "name": "Inactive Dolly",
                    "impact_factor": 1.10,
                    "checked": False,  # unchecked, should be excluded
                },
                "Simple Custom Rig",  # string format
            ]
        })
        tex = ch3_loads(payload)

        assert "Heavy Transporter 120t" in tex
        assert "Impact Factor --- Heavy Transporter 120t" in tex
        assert "1.150 (User-defined, IM = 15.0\\%)" in tex

        # Inactive custom vehicle must be excluded
        assert "Inactive Dolly" not in tex

        # String custom vehicle included with default static impact
        assert "Simple Custom Rig" in tex
        assert "Impact Factor --- Simple Custom Rig" in tex
        assert "1.000 (Static / User-defined)" in tex

    def test_footpath_automatic_irc6(self):
        """Footpath enabled with Automatic pressure mode renders 4.905 kN/m² (never blank)."""
        payload = _base_payload()
        payload.update({
            KEY_FOOTPATH: "Both Sides",
            KEY_TS_FOOTPATH_WIDTH: 1.5,
            KEY_LL_FOOTPATH_PRESSURE_MODE: "Automatic",
            KEY_LL_FOOTPATH_PRESSURE_VALUE: "",  # empty in automatic mode
        })
        tex = ch3_loads(payload)

        # Footpath Configuration
        assert r"\textnormal{Footpath Configuration} & Both Sides" in tex
        assert r"\textnormal{Footpath Width} & 1.50 m" in tex
        assert r"\textnormal{Pressure Mode} & Automatic (as per IRC 6 Cl. 206.1)" in tex
        # Design Footway Pressure MUST NOT be blank
        assert "4.905 kN/m" in tex
        assert r"\textsuperscript{2} (IRC 6 Cl. 206.1)" in tex
        # Linear load: 4.905 * 1.5 = 7.36 kN/m
        assert "7.36 kN/m (per walkway)" in tex

    def test_footpath_single_side_custom_pressure(self):
        """Footpath enabled with Single Side and User-defined custom pressure."""
        payload = _base_payload()
        payload.update({
            KEY_FOOTPATH: "Single Side",
            KEY_TS_FOOTPATH_WIDTH: 1500,  # mm converted to 1.50 m
            KEY_LL_FOOTPATH_PRESSURE_MODE: "User-defined",
            KEY_LL_FOOTPATH_PRESSURE_VALUE: 4.0,
        })
        tex = ch3_loads(payload)

        assert r"\textnormal{Footpath Configuration} & Single Side" in tex
        assert r"\textnormal{Footpath Width} & 1.50 m" in tex
        assert r"\textnormal{Pressure Mode} & User-defined" in tex
        assert "4.000 kN/m" in tex
        # Linear load: 4.0 * 1.5 = 6.00 kN/m
        assert "6.00 kN/m (per walkway)" in tex

    def test_footpath_disabled_none(self):
        """Footpath disabled ('None') renders clean N/A values (no blank entries)."""
        payload = _base_payload()
        payload.update({
            KEY_FOOTPATH: "None",
            KEY_TS_FOOTPATH_WIDTH: None,
            KEY_LL_FOOTPATH_PRESSURE_VALUE: "",
        })
        tex = ch3_loads(payload)

        assert r"\textnormal{Footpath Configuration} & None / Not Applicable" in tex
        assert r"\textnormal{Footpath Width} & N/A (No Footpath)" in tex
        assert r"\textnormal{Pressure Mode} & N/A" in tex
        assert r"\textnormal{Design Footway Pressure} & N/A (No Footpath)" in tex
        assert r"\textnormal{Resulting Linear Load} & N/A (No Footpath)" in tex

    def test_latex_escaping_safety(self):
        """Special characters in custom vehicle names or strings must not break LaTeX."""
        payload = _base_payload()
        payload.update({
            KEY_LL_CUSTOM_VEHICLES: [
                {
                    "name": "Special_Veh & Sons #1 (50% Load)",
                    "impact_factor": 1.25,
                    "checked": True,
                }
            ]
        })
        tex = ch3_loads(payload)

        # Check escaped special characters
        assert r"Special\_\allowbreak{}Veh \& Sons \#1 (50\% Load)" in tex
        # Percents in impact factor text must be escaped
        assert r"IM = 25.0\%" in tex

    def test_repeating_headers_compatibility(self):
        """Both new tables must be compatible with apply_longtable_repeating_headers."""
        payload = _base_payload()
        payload.update({
            KEY_LL_IRC_CLASS_A: True,
            KEY_FOOTPATH: "Both Sides",
            KEY_TS_FOOTPATH_WIDTH: 2.0,
        })
        raw_tex = ch3_loads(payload)
        processed_tex = apply_longtable_repeating_headers(raw_tex)

        # Both tables must have repeating header constructs
        assert processed_tex.count(r"\endfirsthead") >= 2
        assert processed_tex.count(r"\endhead") >= 2
        assert processed_tex.count(r"\endfoot") >= 2
        assert processed_tex.count(r"\endlastfoot") >= 2

    def test_preserved_existing_chapter3_tables(self):
        """Dead load, Surfacing, Wind, Seismic, Temperature, and Combinations tables remain intact."""
        payload = _base_payload()
        tex = ch3_loads(payload)

        assert r"\caption{\textbf{Dead Load -- Self Weight}}" in tex
        assert r"\caption{\textbf{Dead Load for Surfacing (DW)}}" in tex
        assert r"\caption{\textbf{Wind Load (WL) --- per IRC 6}}" in tex
        assert r"\caption{\textbf{Earthquake Load (EL) --- per IRC 6}}" in tex
        assert r"\caption{\textbf{Temperature Load (TL) --- per IRC 6}}" in tex
        assert r"\caption{\textbf{Load Combinations}}" in tex
