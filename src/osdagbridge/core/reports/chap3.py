# =============================================================================
# Chapter 3: Loads and Load Combinations
# Extracted from report_generator.py — DO NOT add business logic here.
# =============================================================================

from osdagbridge.core.utils.common import (
    KEY_CB_LOAD,
    KEY_FOOTPATH,
    KEY_LL_CUSTOM_VEHICLES,
    KEY_LL_FOOTPATH_PRESSURE_MODE,
    KEY_LL_FOOTPATH_PRESSURE_VALUE,
    KEY_LL_IRC_70R_BOGIE,
    KEY_LL_IRC_70R_TRACKED,
    KEY_LL_IRC_70R_WHEELED,
    KEY_LL_IRC_AA_TRACKED,
    KEY_LL_IRC_AA_WHEELED,
    KEY_LL_IRC_CLASS_A,
    KEY_LL_IRC_CLASS_FATIGUE,
    KEY_LL_IRC_CLASS_SV,
    KEY_MATERIAL_DECK_DENSITY,
    KEY_MATERIAL_GIRDER_DENSITY,
    KEY_PL_SELF_WEIGHT_FACTOR,
    KEY_RL_LOAD_VALUE,
    KEY_SL_DAMPING,
    KEY_SL_DEAD_LOAD_MODE,
    KEY_SL_DEAD_LOAD_VALUE,
    KEY_SL_HORIZONTAL_COEFF,
    KEY_SL_IMPORTANCE_FACTOR,
    KEY_SL_LIVE_LOAD_MODE,
    KEY_SL_LIVE_LOAD_VALUE,
    KEY_SL_SEISMIC_ZONE,
    KEY_SL_SOIL_TYPE,
    KEY_SL_SPECTRAL_COEFF,
    KEY_SL_TIME_PERIOD,
    KEY_SL_VERTICAL_COEFF,
    KEY_SL_ZONE_FACTOR,
    KEY_SPAN,
    KEY_TL_BRIDGE_TEMP_MAX,
    KEY_TL_BRIDGE_TEMP_MIN,
    KEY_TL_HIGHEST_MAX_TEMP,
    KEY_TL_LOWEST_MIN_TEMP,
    KEY_TL_TEMP_FALL,
    KEY_TL_TEMP_RISE,
    KEY_TS_FOOTPATH_THICKNESS,
    KEY_TS_FOOTPATH_WIDTH,
    KEY_TS_NO_OF_FOOTPATHS,
    KEY_WC_LD_LANE_TABLE_COUNT,
    KEY_WC_MATERIAL,
    KEY_WC_THICKNESS,
    KEY_WL_AVG_EXPOSED_HEIGHT,
    KEY_WL_BASIC_WIND_SPEED,
    KEY_WL_HOURLY_MEAN_WIND,
    KEY_WL_HOURLY_WIND_PRESSURE,
    KEY_WL_LONGITUDINAL_WIND_FORCE,
    KEY_WL_TERRAIN_TYPE,
    KEY_WL_TRANSVERSE_WIND_FORCE,
    KEY_WL_VERTICAL_WIND_FORCE
)

from osdagbridge.core.reports.report_utils import _tex, _render_value

def ch3_loads(input_dict):
    def _is_checked(val):
        if val is None:
            return False
        if isinstance(val, bool):
            return val
        if isinstance(val, (int, float)):
            return val > 0
        s = str(val).strip().lower()
        if s in ("false", "0", "no", "none", "off", ""):
            return False
        if s in ("true", "1", "yes", "checked", "selected", "on"):
            return True
        return False

    # Dynamic Live Load vehicle selection (only selected/checked vehicles)
    irc_vehicle_defs = [
        (KEY_LL_IRC_CLASS_A, "Class A", ["irc_class_a", "class_a"], "class_a"),
        (KEY_LL_IRC_70R_WHEELED, "Class 70R (Wheeled)", ["irc_70r_wheeled", "70r_wheeled"], "70r_wheeled"),
        (KEY_LL_IRC_70R_TRACKED, "Class 70R (Tracked)", ["irc_70r_tracked", "70r_tracked"], "70r_tracked"),
        (KEY_LL_IRC_AA_WHEELED, "Class AA (Wheeled)", ["irc_aa_wheeled", "aa_wheeled"], "aa_wheeled"),
        (KEY_LL_IRC_AA_TRACKED, "Class AA (Tracked)", ["irc_aa_tracked", "aa_tracked"], "aa_tracked"),
        (KEY_LL_IRC_70R_BOGIE, "Class 70R (Bogie)", ["irc_70r_bogie", "70r_bogie"], "70r_bogie"),
        (KEY_LL_IRC_CLASS_SV, "Class SV", ["irc_class_sv", "class_sv"], "class_sv"),
        (KEY_LL_IRC_CLASS_FATIGUE, "Class Fatigue", ["irc_class_fatigue", "class_fatigue"], "class_fatigue"),
    ]

    selected_vehicles = []
    for key, display_name, aliases, code in irc_vehicle_defs:
        val = input_dict.get(key)
        if val is None:
            for alias in aliases:
                if alias in input_dict:
                    val = input_dict[alias]
                    break
        if _is_checked(val):
            selected_vehicles.append((display_name, code, None))

    custom = input_dict.get(KEY_LL_CUSTOM_VEHICLES) or input_dict.get("custom_vehicles")
    if custom and isinstance(custom, list):
        for c in custom:
            if isinstance(c, dict):
                chk = c.get("checked", c.get("enabled", True))
                if _is_checked(chk):
                    c_name = c.get("name") or c.get("vehicle_name") or "Custom Vehicle"
                    selected_vehicles.append((str(c_name), "custom", c))
            elif isinstance(c, str) and c.strip():
                selected_vehicles.append((c.strip(), "custom", None))

    if not selected_vehicles:
        raw_list = input_dict.get("selected_vehicles") or input_dict.get("vehicles")
        if isinstance(raw_list, list):
            for item in raw_list:
                if isinstance(item, str) and item.strip():
                    item_s = item.strip()
                    matched_code = "custom"
                    for _, d_name, _, code in irc_vehicle_defs:
                        if item_s.lower() == d_name.lower():
                            matched_code = code
                            break
                    selected_vehicles.append((item_s, matched_code, None))

    from osdagbridge.core.utils.codes.irc6_2017 import IRC6_2017

    span_raw = input_dict.get(KEY_SPAN) or input_dict.get("span")
    span_m = None
    if span_raw not in (None, ""):
        try:
            s_val = float(span_raw)
            if s_val > 0:
                span_m = s_val
        except (ValueError, TypeError):
            span_m = None

    def _get_vehicle_impact_str(code, span, custom_obj):
        if code == "class_a":
            if span is not None:
                L = min(max(span, 3.0), 45.0)
                im = 9.0 / (13.5 + L)
                return f"{1.0 + im:.3f} (IM = {im * 100:.1f}%, IRC 6 Cl. 208.2)"
            return "N/A (Span not specified)"

        elif code in ("70r_wheeled", "aa_wheeled", "70r_bogie"):
            if span is not None:
                if span < 23.0:
                    im = 0.25
                else:
                    L = min(span, 45.0)
                    im = 9.0 / (13.5 + L)
                return f"{1.0 + im:.3f} (IM = {im * 100:.1f}%, IRC 6 Cl. 208.3)"
            return "N/A (Span not specified)"

        elif code in ("70r_tracked", "aa_tracked"):
            if span is not None:
                im = 0.25 if span < 5.0 else 0.10
                return f"{1.0 + im:.3f} (IM = {im * 100:.1f}%, IRC 6 Cl. 208.3)"
            return "N/A (Span not specified)"

        elif code == "class_sv":
            return "1.000 (No dynamic impact allowance, IRC 6 Cl. 204.6)"

        elif code == "class_fatigue":
            return "1.000 (Static / Fatigue verification, IRC 6 Cl. 204.5)"

        elif code == "custom":
            if custom_obj and isinstance(custom_obj, dict):
                im_val = (
                    custom_obj.get("impact_factor") or
                    custom_obj.get("impact") or
                    custom_obj.get("impact_multiplier")
                )
                if im_val not in (None, ""):
                    try:
                        im_f = float(im_val)
                        if im_f >= 1.0:
                            mult = im_f
                            im_pct = (im_f - 1.0) * 100.0
                        else:
                            mult = 1.0 + im_f
                            im_pct = im_f * 100.0
                        return f"{mult:.3f} (User-defined, IM = {im_pct:.1f}%)"
                    except (ValueError, TypeError):
                        return f"{str(im_val)} (User-defined)"
            return "1.000 (Static / User-defined)"

        return "N/A"

    lanes_raw = (
        input_dict.get(KEY_WC_LD_LANE_TABLE_COUNT) or
        input_dict.get("number_of_lanes") or
        input_dict.get("lanes") or
        input_dict.get("no_of_lanes")
    )
    if lanes_raw not in (None, ""):
        try:
            lanes_int = int(lanes_raw)
            lanes_str = f"{lanes_int} Lane" if lanes_int == 1 else f"{lanes_int} Lanes"
            braking_force_t = IRC6_2017.cl_211_2_braking_force(lanes_int)
            braking_force_kN = braking_force_t * 9.81
            braking_force_str = f"{braking_force_kN:.2f} kN ({braking_force_t:.2f} tonnes)"
        except Exception:
            lanes_str = str(lanes_raw)
            braking_force_str = "N/A"
    else:
        lanes_str = "N/A"
        braking_force_str = "N/A"

    v_rows = []
    v_rows.append(r"\textnormal{Design Traffic Lanes} & " + _tex(lanes_str) + r" \\[6pt]" + "\n" + r"\hline")
    v_rows.append(r"\textnormal{Longitudinal Braking Force} & " + _tex(braking_force_str) + r" \\[6pt]" + "\n" + r"\hline")

    if selected_vehicles:
        vehicles_summary_str = ", ".join(v[0] for v in selected_vehicles)
        v_rows.append(r"\textnormal{Vehicles Considered} & " + _tex(vehicles_summary_str) + r" \\[6pt]" + "\n" + r"\hline")
        for v_name, v_code, custom_obj in selected_vehicles:
            im_text = _get_vehicle_impact_str(v_code, span_m, custom_obj)
            v_rows.append(
                r"\textnormal{Impact Factor --- " + _tex(v_name) + r"} & " + _tex(im_text) + r" \\[6pt]" + "\n" + r"\hline"
            )
    else:
        v_rows.append(r"\textnormal{Vehicles Considered} & None \\[6pt]" + "\n" + r"\hline")
        v_rows.append(r"\textnormal{Impact Factor (IRC 6)} & N/A \\[6pt]" + "\n" + r"\hline")

    v_rows_str = "\n".join(v_rows)

    # Footway Live Load (IRC 6 Cl. 206.1)
    fp_raw = input_dict.get(KEY_FOOTPATH) or input_dict.get("footpath")
    if fp_raw is None and KEY_TS_NO_OF_FOOTPATHS in input_dict:
        n_fp = input_dict.get(KEY_TS_NO_OF_FOOTPATHS)
        try:
            n_fp_int = int(n_fp)
            if n_fp_int == 1:
                fp_raw = "Single Side"
            elif n_fp_int == 2:
                fp_raw = "Both Sides"
            else:
                fp_raw = "None"
        except (ValueError, TypeError):
            fp_raw = "None"

    fp_raw_str = str(fp_raw).strip() if fp_raw is not None else "None"
    has_footpath = fp_raw_str.lower() not in ("none", "false", "no", "0", "")

    if has_footpath:
        footpath_status = fp_raw_str
    else:
        footpath_status = "None / Not Applicable"

    fp_width_val = input_dict.get(KEY_TS_FOOTPATH_WIDTH) or input_dict.get("footpath_width")
    fp_width_m = None
    if has_footpath and fp_width_val not in (None, ""):
        try:
            w_f = float(fp_width_val)
            fp_width_m = w_f / 1000.0 if w_f > 10.0 else w_f
            fp_width_str = f"{fp_width_m:.2f} m"
        except Exception:
            fp_width_str = str(fp_width_val)
    elif not has_footpath:
        fp_width_str = "N/A (No Footpath)"
    else:
        fp_width_str = "N/A"

    fp_mode = input_dict.get(KEY_LL_FOOTPATH_PRESSURE_MODE) or input_dict.get("footpath_pressure_mode")
    fp_val = (
        input_dict.get(KEY_LL_FOOTPATH_PRESSURE_VALUE) or
        input_dict.get("footpath_pressure_value") or
        input_dict.get("footpath_pressure")
    )

    if not has_footpath:
        fp_mode_str = "N/A"
        fp_pressure_str = "N/A (No Footpath)"
        fp_linear_str = "N/A (No Footpath)"
    else:
        mode_clean = str(fp_mode).strip() if fp_mode not in (None, "") else "Automatic"
        mode_lower = mode_clean.lower()
        is_auto = any(k in mode_lower for k in ("auto", "irc 6", "irc6")) or (fp_val in (None, ""))

        if is_auto:
            fp_mode_str = "Automatic (as per IRC 6 Cl. 206.1)"
            try:
                p_kn = IRC6_2017.cl_206_1_footway_load()
            except Exception:
                p_kn = 4.905
            fp_pressure_str = f"{p_kn:.3f} kN/m" + r"\textsuperscript{2} (IRC 6 Cl. 206.1)"
            design_pressure_val = p_kn
        else:
            fp_mode_str = mode_clean
            try:
                p_kn = float(fp_val)
                fp_pressure_str = f"{p_kn:.3f} kN/m" + r"\textsuperscript{2}"
                design_pressure_val = p_kn
            except Exception:
                fp_pressure_str = _tex(str(fp_val)) + r" kN/m\textsuperscript{2}"
                design_pressure_val = None

        if design_pressure_val is not None and fp_width_m is not None:
            linear_load_val = design_pressure_val * fp_width_m
            fp_linear_str = f"{linear_load_val:.2f} kN/m (per walkway)"
        else:
            fp_linear_str = "N/A"

    # Vz / Pz — prefer stored computed values; fall back to IRC6 Table 12
    vz_val = input_dict.get(KEY_WL_HOURLY_MEAN_WIND)
    pz_val = input_dict.get(KEY_WL_HOURLY_WIND_PRESSURE)
    if not vz_val or not pz_val:
        try:
            _vb  = input_dict.get(KEY_WL_BASIC_WIND_SPEED) or input_dict.get('wind_speed')
            _h   = input_dict.get(KEY_WL_AVG_EXPOSED_HEIGHT)
            _ter = {
                "Plain Terrain": "plain",
                "Terrain with Obstructions": "obstructed",
            }.get(str(input_dict.get(KEY_WL_TERRAIN_TYPE, "")).strip(), "plain")
            _res = IRC6_2017.table_12(float(_h), _ter, float(_vb))
            if not vz_val:
                vz_val = _res.get("Vz")
            if not pz_val:
                pz_val = _res.get("Pz")
        except Exception:
            pass
    vz_str = f"{float(vz_val):.2f} m/s" if vz_val not in (None, "") else "N/A"
    pz_str = f"{float(pz_val):.2f} N/m²" if pz_val not in (None, "") else "N/A"

    # Table 3.5 — Seismic: prefer stored computed values; fall back to IRC6 cl_218_5_1
    sl_zone_factor = input_dict.get(KEY_SL_ZONE_FACTOR)
    sl_spectral    = input_dict.get(KEY_SL_SPECTRAL_COEFF)
    sl_ah          = input_dict.get(KEY_SL_HORIZONTAL_COEFF)
    sl_av          = input_dict.get(KEY_SL_VERTICAL_COEFF)
    if not sl_ah or not sl_zone_factor:
        try:
            _zone = input_dict.get(KEY_SL_SEISMIC_ZONE) or input_dict.get('seismic_zone')
            _zmap = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}
            _z    = str(_zone).strip().upper()
            if _z.isdigit():
                _z = _zmap.get(_z)
            _smap = {"Type I – Rocky or Hard": 1, "Type II – Medium Soil": 2, "Type III – Soft Soil": 3}
            _st   = _smap.get(str(input_dict.get(KEY_SL_SOIL_TYPE, "")), 1)
            _tp   = input_dict.get(KEY_SL_TIME_PERIOD)
            _damp = input_dict.get(KEY_SL_DAMPING) or "5"
            _dl_v = input_dict.get(KEY_SL_DEAD_LOAD_VALUE)
            _ll_v = input_dict.get(KEY_SL_LIVE_LOAD_VALUE)
            _dead = float(_dl_v) if str(input_dict.get(KEY_SL_DEAD_LOAD_MODE, "")) == "Custom" and _dl_v else 0.0
            _live = float(_ll_v) if str(input_dict.get(KEY_SL_LIVE_LOAD_MODE, "")) == "Custom" and _ll_v else 0.0
            _res  = IRC6_2017.cl_218_5_1(zone=f"Zone {_z}", soil_type=_st, dead_load_kN=_dead,
                        live_load_kN=_live, period_T=float(_tp) if _tp else None,
                        damping_percent=float(_damp))
            if not sl_zone_factor:
                sl_zone_factor = _res.get("Z")
            if not sl_spectral:
                sl_spectral    = _res.get("Sa_g_adjusted")
            if not sl_ah:
                sl_ah          = _res.get("Ah")
            if not sl_av:
                sl_av          = round(_res.get("Ah", 0) * 2 / 3, 4)
        except Exception:
            pass

    def _sl(v, unit=""):
        return f"{float(v):.4f}{unit}" if v not in (None, "") else "N/A"

    # Table 3.6 — Temperature: compute effective bridge temp range from shade temps
    tl_temp_min = tl_temp_max = tl_rise = tl_fall = "N/A"
    try:
        _tmax = input_dict.get(KEY_TL_HIGHEST_MAX_TEMP) or input_dict.get('shade_temp_max')
        _tmin = input_dict.get(KEY_TL_LOWEST_MIN_TEMP)  or input_dict.get('shade_temp_min')
        if _tmax and _tmin:
            _res    = IRC6_2017.cl_215_2_effective_bridge_temperature(
                          float(_tmax), float(_tmin), 'metallic', False)
            _bt_min = _res.get('T_min', 0)
            _bt_max = _res.get('T_max', 0)
            _mean   = (_bt_max + _bt_min) / 2.0
            tl_temp_min = f"{_bt_min:.2f}"
            tl_temp_max = f"{_bt_max:.2f}"
            tl_rise     = f"{_bt_max - _mean:.2f}"
            tl_fall     = f"{_mean - _bt_min:.2f}"
    except Exception:
        pass

    # --- Table 3.7: Load Combinations (dynamically generated from IRC 6) ---
    _LOAD_LABEL_MAP = {
        'dead_load':         'DL',
        'surfacing':         'SIDL',
        'live_load':         'LL',
        'wind_load':         'WL',
        'thermal_load':      'TL',
        'vehicle_collision': 'VC',
        'barge_impact':      'BI',
        'floating_bodies':   'FB',
        'seismic':           'EQ',
    }

    def _fmt_factors(factors):
        """Format a factors dict into a compact load-case string for the table."""
        parts = []
        for load, val in factors.items():
            label = _LOAD_LABEL_MAP.get(load, load.upper())
            if isinstance(val, dict):  # permanent load with adding/relieving
                add = val.get('adding')
                rel = val.get('relieving')
                add_s = f"{add:.2f}" if add is not None else '--'
                rel_s = f"{rel:.2f}" if rel is not None else '--'
                parts.append(f"{label}({add_s}/{rel_s})")
            else:
                if val is None:
                    continue  # skip N/A factors
                parts.append(f"{label}({val:.2f})")
        return ' + '.join(parts)

    uls_combos = IRC6_2017.uls_load_combinations()
    sls_combos = IRC6_2017.sls_load_combinations()
    lc_rows = []
    for i, combo in enumerate(uls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(
            f"ULS-{i:02d}" + r" & " + cases + r" \\[6pt]" + "\n"
            + r"\hline"
        )
    for i, combo in enumerate(sls_combos, start=1):
        cases = _fmt_factors(combo['factors'])
        lc_rows.append(
            f"SLS-{i:02d}" + r" & " + cases + r" \\[6pt]" + "\n"
            + r"\hline"
        )

    lc_rows_str = "\n".join(lc_rows)

    return r"""
\chapter{Loads and Load Combinations}

This section summarizes all loads applied to the bridge and the load combinations considered for analysis and design.

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load -- Self Weight}}
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\textnormal{Steel Self-Weight Applied} & """ + (_render_value(input_dict, KEY_MATERIAL_GIRDER_DENSITY, ' kN/m\\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textnormal{Concrete Deck Weight} & """ + (_render_value(input_dict, KEY_MATERIAL_DECK_DENSITY, ' kN/m\\textsuperscript{3}')) + r""" \\[6pt]
\hline
\textnormal{Self-Weight Factor} & """ + (_render_value(input_dict, KEY_PL_SELF_WEIGHT_FACTOR)) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Dead Load for Surfacing (DW)}}
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\textnormal{Wearing Course Load} & """ + (_render_value(input_dict, KEY_WC_MATERIAL)) + r""" x """ + (_render_value(input_dict, KEY_WC_THICKNESS)) + r""" \\[6pt]
\hline
\textnormal{Additional SIDL (Crash Barrier)} & """ + (_render_value(input_dict, KEY_CB_LOAD)) + r""" kN/m per barrier \\[6pt]
\hline
\textnormal{Railing Load} & """ + (_render_value(input_dict, KEY_RL_LOAD_VALUE)) + r""" kN/m\sdstar{} \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Vehicle Live Loads (IRC 6)}}
\hline
\textbf{parameter} & \textbf{value} \\
\hline
""" + v_rows_str + r"""
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Footway Live Load (IRC 6 Cl. 206.1)}}
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\textnormal{Footpath Configuration} & """ + _tex(footpath_status) + r""" \\[6pt]
\hline
\textnormal{Footpath Width} & """ + _tex(fp_width_str) + r""" \\[6pt]
\hline
\textnormal{Pressure Mode} & """ + _tex(fp_mode_str) + r""" \\[6pt]
\hline
\textnormal{Design Footway Pressure} & """ + fp_pressure_str + r""" \\[6pt]
\hline
\textnormal{Resulting Linear Load} & """ + _tex(fp_linear_str) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Wind Load (WL) --- per IRC 6}}
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\textnormal{Basic Wind Speed, Vb} & """ + (_render_value(input_dict,'wind_speed', ' m/s')) + r""" [from Project Location] \\[6pt]
\hline
\textnormal{Terrain Type} & """ + (_render_value(input_dict, KEY_WL_TERRAIN_TYPE)) + r""" \\[6pt]
\hline
\textnormal{Average Exposed Height, H (m)} & """ + (_render_value(input_dict, KEY_WL_AVG_EXPOSED_HEIGHT, ' m')) + r""" \\[6pt]
\hline
\textnormal{Hourly Mean Wind Speed, Vz} & """ + (_render_value(input_dict, KEY_WL_HOURLY_MEAN_WIND, ' m/s')) + r""" \\[6pt]
\hline
\textnormal{Hourly Wind Pressure, Pz} & """ + (_render_value(input_dict, KEY_WL_HOURLY_WIND_PRESSURE, ' N/m\\textsuperscript{2}')) + r""" \\[6pt]
\hline
\textnormal{Transverse Wind Force} & """ + (_render_value(input_dict, KEY_WL_TRANSVERSE_WIND_FORCE, ' kN')) + r""" \\[6pt]
\hline
\textnormal{Longitudinal Wind Force} & """ + (_render_value(input_dict, KEY_WL_LONGITUDINAL_WIND_FORCE, ' kN')) + r""" \\[6pt]
\hline
\textnormal{Vertical Wind Force} & """ + (_render_value(input_dict, KEY_WL_VERTICAL_WIND_FORCE, ' kN')) + r""" \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Earthquake Load (EL) --- per IRC 6}}
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\textnormal{Seismic Zone} & """ + (_render_value(input_dict,'seismic_zone')) + r""" [from Project Location] \\[6pt]
\hline
\textnormal{Zone Factor, Z} & """ + (_render_value(input_dict, KEY_SL_ZONE_FACTOR)) + r""" \\[6pt]
\hline
\textnormal{Importance Factor, I} & """ + (_render_value(input_dict, KEY_SL_IMPORTANCE_FACTOR)) + r""" \\[6pt]
\hline
\textnormal{Type of Soil} & """ + (_render_value(input_dict, KEY_SL_SOIL_TYPE)) + r""" \\[6pt]
\hline
\textnormal{Sa/g} & """ + (_render_value(input_dict, KEY_SL_SPECTRAL_COEFF)) + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Coefficient, Ah} & """ + (_render_value(input_dict, KEY_SL_HORIZONTAL_COEFF)) + r""" \\[6pt]
\hline
\textnormal{Vertical Seismic Coefficient, Av} & """ + (_render_value(input_dict, KEY_SL_VERTICAL_COEFF)) + r""" \\[6pt]
\hline
\textnormal{Horizontal Seismic Force (longitudinal)} & """ + '' + r""" kN \\[6pt]
\hline
\textnormal{Horizontal Seismic Force (transverse)} & """ + '' + r""" kN \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|L{5.5cm}|p{10.0cm}|}
\caption{\textbf{Temperature Load (TL) --- per IRC 6}}
\hline
\textbf{parameter} & \textbf{value} \\
\hline
\textnormal{Maximum Shade Temperature} & """ + (_render_value(input_dict,'shade_temp_max')) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Minimum Shade Temperature} & """ + (_render_value(input_dict,'shade_temp_min')) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Effective Bridge Temp. Range} & """ + (_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MIN)) + r""" to """ + (_render_value(input_dict, KEY_TL_BRIDGE_TEMP_MAX)) + r""" $^\circ$C \\[6pt]
\hline
\textnormal{Temperature Rise / Fall for Design} & +""" + (_render_value(input_dict, KEY_TL_TEMP_RISE)) + r""" $^\circ$C / \textminus{}""" + (_render_value(input_dict, KEY_TL_TEMP_FALL)) + r""" $^\circ$C \\[6pt]
\hline
\end{longtable}

\vspace{1em}
\begin{longtable}{|C{4.0cm}|p{11.5cm}|}
\caption{\textbf{Load Combinations}}
\hline
\textbf{Combination ID} & \textbf{Load Cases} \\[6pt]
\hline
""" + lc_rows_str + r"""
\end{longtable}

\noindent\textit{Note: All IRC 6 load combinations are auto-generated by OsdagBridge. User-defined custom combinations, if any, are appended.}
"""


