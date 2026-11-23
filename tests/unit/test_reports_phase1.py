"""Unit tests for Phase 1: Foundation (Centralized Styling, Footer Clearance, Repeating longtable Headers)."""

import os
import re
import tempfile
import pytest

from osdagbridge.core.reports.styles import (
    PAGE_PAPER,
    MARGIN_TOP,
    MARGIN_BOTTOM,
    MARGIN_LEFT,
    MARGIN_RIGHT,
    HEAD_HEIGHT,
    HEAD_SEP,
    FOOT_SKIP,
    FOOTRULE_DEFAULT_VSPACE,
    FOOTRULE_SD_NOTE_VSPACE,
    FOOTRULE_RULE_VSPACE,
    FOOTRULE_POST_VSPACE,
    TABCOLSEP,
    ARRAYSTRETCH,
    LTPRE,
    LTPOST,
    ARRAYRULEWIDTH,
    EXTRAROWHEIGHT,
    COLOR_OSDAG_GREEN_HEX,
    COLOR_OSDAG_GREEN_NAME,
    COLOR_TABLE_HEADER_BG_HEX,
    COLOR_TABLE_HEADER_BG_NAME,
    COLOR_TABLE_ROW_ALT_HEX,
    COLOR_TABLE_ROW_ALT_NAME,
    COLOR_STATUS_PASS_HEX,
    COLOR_STATUS_PASS_NAME,
    COLOR_STATUS_FAIL_HEX,
    COLOR_STATUS_FAIL_NAME,
    COLOR_STATUS_WARN_HEX,
    COLOR_STATUS_WARN_NAME,
    COLOR_STATUS_NA_HEX,
    COLOR_STATUS_NA_NAME,
    MATPLOTLIB_DPI,
    FIGURE_DEFAULT_SIZE,
    CHART_COLOR_PALETTE,
    MATPLOTLIB_RC_PARAMS,
    apply_matplotlib_style,
    get_geometry_latex,
    get_color_definitions_latex,
    get_table_spacing_latex,
    get_footrule_definition_latex,
    get_status_badge_latex,
)
from osdagbridge.core.reports.report_utils import (
    extract_braced_content,
    format_longtable,
    apply_longtable_repeating_headers,
    save_matplotlib_figure,
)
from osdagbridge.core.reports.chap7 import ch7_quantities
from osdagbridge.core.reports.report_generator import preamble


class TestStylesModule:
    """Test suite for styles.py single source of truth."""

    def test_geometry_constants(self):
        assert PAGE_PAPER == "a4paper"
        assert MARGIN_TOP == "25mm"
        # Verify generous footer clearance (32mm bottom margin and 18mm footskip)
        assert MARGIN_BOTTOM == "32mm"
        assert FOOT_SKIP == "18mm"
        assert MARGIN_LEFT == "25mm"
        assert MARGIN_RIGHT == "25mm"
        assert HEAD_HEIGHT == "16pt"
        assert HEAD_SEP == "12pt"

    def test_footrule_clearance(self):
        # Footnote offset when software default is present must not be aggressive (-20pt)
        assert FOOTRULE_SD_NOTE_VSPACE == "-12pt"
        assert FOOTRULE_DEFAULT_VSPACE == "-8pt"

    def test_table_spacing_constants(self):
        assert TABCOLSEP == "6pt"
        assert ARRAYSTRETCH == 1.15
        assert LTPRE == "0pt"
        assert LTPOST == "6pt"
        assert ARRAYRULEWIDTH == "0.5pt"
        assert EXTRAROWHEIGHT == "0.6pt"

    def test_color_definitions(self):
        assert COLOR_OSDAG_GREEN_HEX == "91B014"
        assert COLOR_OSDAG_GREEN_NAME == "osdagGreen"
        assert COLOR_STATUS_PASS_HEX == "1B5E20"
        assert COLOR_STATUS_FAIL_HEX == "C62828"
        assert COLOR_STATUS_WARN_HEX == "E65100"
        assert COLOR_STATUS_NA_HEX == "616161"

    def test_matplotlib_defaults(self):
        assert MATPLOTLIB_DPI == 300
        assert FIGURE_DEFAULT_SIZE == (8, 5)
        assert "#91B014" in CHART_COLOR_PALETTE
        assert MATPLOTLIB_RC_PARAMS["figure.dpi"] == 300
        assert MATPLOTLIB_RC_PARAMS["savefig.dpi"] == 300

    def test_latex_snippet_generators(self):
        geom = get_geometry_latex()
        assert "bottom=32mm" in geom
        assert "footskip=18mm" in geom
        assert "top=25mm" in geom

        colors = get_color_definitions_latex()
        assert r"\definecolor{osdagGreen}{HTML}{91B014}" in colors
        assert r"\definecolor{tableHeaderBg}{HTML}{EFEFEF}" in colors
        assert r"\definecolor{statusPass}{HTML}{1B5E20}" in colors
        assert r"\definecolor{statusFail}{HTML}{C62828}" in colors

        spacing = get_table_spacing_latex()
        assert r"\setlength{\tabcolsep}{6pt}" in spacing
        assert r"\renewcommand{\arraystretch}{1.15}" in spacing
        assert r"\BeforeBeginEnvironment{longtable}" in spacing

        footrule = get_footrule_definition_latex()
        assert r"\renewcommand{\footrule}" in footrule
        assert "-12pt" in footrule

    def test_status_badge(self):
        pass_badge = get_status_badge_latex("PASS")
        assert r"\textcolor{statusPass}{\textbf{PASS}}" in pass_badge
        fail_badge = get_status_badge_latex("FAIL")
        assert r"\textcolor{statusFail}{\textbf{FAIL}}" in fail_badge


class TestReportUtilsLongtableHelpers:
    """Test suite for format_longtable and apply_longtable_repeating_headers."""

    def test_extract_braced_content(self):
        text = r"\caption{\textbf{Title with {nested} braces}} after"
        idx = text.find("{")
        content, end_pos = extract_braced_content(text, idx)
        assert content == r"{\textbf{Title with {nested} braces}}"
        assert text[end_pos:] == " after"

    def test_format_longtable_with_caption(self):
        col_spec = "|C{3.0cm}|L{6.0cm}|"
        headers = ["Code", "Description"]
        rows = [
            r"LC-01 & Dead Load + Live Load \\[6pt] \hline",
            r"LC-02 & Dead Load + Wind Load \\[6pt] \hline",
        ]
        tex = format_longtable(
            col_spec=col_spec,
            headers=headers,
            rows=rows,
            caption="Test Combinations",
            label="tab:test-combos",
            table_note="Note: Test table note",
        )

        assert r"\begin{longtable}{|C{3.0cm}|L{6.0cm}|}" in tex
        assert r"\caption{Test Combinations}\label{tab:test-combos}\\" in tex
        assert r"\endfirsthead" in tex
        assert r"\multicolumn{2}{l}{\small\textbf{\tablename\ \thetable{} -- Continued from previous page}} \\[4pt]" in tex
        assert r"\textbf{Code} & \textbf{Description}" in tex
        assert r"\endhead" in tex
        assert r"\multicolumn{2}{r}{\footnotesize\textit{Continued on next page\ldots}} \\" in tex
        assert r"\endfoot" in tex
        assert r"\endlastfoot" in tex
        assert r"LC-01 & Dead Load + Live Load" in tex
        assert r"\end{longtable}" in tex
        assert r"\noindent\textit{Note: Test table note}" in tex

    def test_apply_longtable_repeating_headers_with_caption(self):
        raw_tex = r"""
\begin{longtable}{|C{4.0cm}|p{11.5cm}|}
\caption{\textbf{Load Combinations}}
\hline
\textbf{Combination ID} & \textbf{Load Cases} \\[6pt]
\hline
ULS-01 & 1.35 DL + 1.5 LL \\[6pt]
\hline
ULS-02 & 1.0 DL + 1.5 WL \\[6pt]
\hline
\end{longtable}
"""
        transformed = apply_longtable_repeating_headers(raw_tex)

        # Check First Head
        assert r"\caption{\textbf{Load Combinations}}\\" in transformed
        assert r"\hline" in transformed
        assert r"\textbf{Combination ID} & \textbf{Load Cases} \\[6pt]" in transformed
        assert r"\endfirsthead" in transformed

        # Check Continuation Head
        assert r"\multicolumn{2}{l}{\small\textbf{\tablename\ \thetable{} -- Continued from previous page}} \\[4pt]" in transformed
        assert r"\endhead" in transformed

        # Check Continuation Foot and Last Foot
        assert r"\multicolumn{2}{r}{\footnotesize\textit{Continued on next page\ldots}} \\" in transformed
        assert r"\endfoot" in transformed
        assert r"\endlastfoot" in transformed

        # Check Data rows preserved
        assert r"ULS-01 & 1.35 DL + 1.5 LL \\[6pt]" in transformed
        assert r"ULS-02 & 1.0 DL + 1.5 WL \\[6pt]" in transformed
        assert r"\end{longtable}" in transformed

    def test_apply_longtable_repeating_headers_without_caption(self):
        raw_tex = r"""
\begin{longtable}{|C{1.0cm}|L{3.8cm}|C{2.6cm}|}
\hline
\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume} \\[6pt]
\hline
1 & Girder Steel & 12.5 m3 \\[6pt]
\hline
\end{longtable}
"""
        transformed = apply_longtable_repeating_headers(raw_tex)

        assert r"\endfirsthead" in transformed
        assert r"\multicolumn{3}{l}{\small\textit{(Continued from previous page)}} \\[4pt]" in transformed
        assert r"\textbf{S.N.} & \textbf{Item Description} & \textbf{Volume}" in transformed
        assert r"\endhead" in transformed
        assert r"\endfoot" in transformed
        assert r"\endlastfoot" in transformed

    def test_apply_longtable_preserves_valid_existing_repeating_headers(self):
        raw_tex = r"""
\begin{longtable}{|c|c|}
\caption{Already Complete}\\
\hline
A & B \\
\hline
\endfirsthead
\multicolumn{2}{c}{Continued}\\
\hline
A & B \\
\hline
\endhead
\hline
\endfoot
\hline
\endlastfoot
1 & 2 \\
\hline
\end{longtable}
"""
        transformed = apply_longtable_repeating_headers(raw_tex)
        # Should not duplicate or corrupt
        assert transformed.count(r"\endfirsthead") == 1
        assert transformed.count(r"\endhead") == 1
        assert transformed.count(r"\endfoot") == 1
        assert transformed.count(r"\endlastfoot") == 1


class TestFigureSaver:
    """Test suite for save_matplotlib_figure."""

    def test_save_figure_mock(self):
        class MockFigure:
            def __init__(self):
                self.saved_path = None
                self.saved_kwargs = None
                self.closed = False

            def savefig(self, path, **kwargs):
                self.saved_path = path
                self.saved_kwargs = kwargs
                # Create a dummy file to simulate actual write
                with open(path, "wb") as f:
                    f.write(b"PNG_DATA")

        fig = MockFigure()
        with tempfile.TemporaryDirectory() as tmpdir:
            res_path = save_matplotlib_figure(fig, tmpdir, "test_chart.png", dpi=300, close=False)
            assert os.path.exists(res_path)
            assert res_path.endswith("test_chart.png")
            assert fig.saved_kwargs["dpi"] == 300
            assert fig.saved_kwargs["bbox_inches"] == "tight"

    def test_save_figure_none(self):
        assert save_matplotlib_figure(None, "dummy", "dummy.png") == ""


class TestChapter7GroupLeak:
    """Test suite to ensure chap7 closes \\begingroup."""

    def test_ch7_begingroup_closed(self):
        input_dict = {
            "steel_girders_qty": 4,
            "steel_girders_wt_total": 25.0,
        }
        tex = ch7_quantities(input_dict)
        assert r"\begingroup" in tex
        assert r"\endgroup" in tex
        # Ensure \endgroup comes strictly after \end{longtable}
        lt_end = tex.find(r"\end{longtable}")
        eg_pos = tex.find(r"\endgroup")
        assert lt_end != -1 and eg_pos != -1
        assert eg_pos > lt_end, "\\endgroup must be placed after \\end{longtable}!"


class TestReportGeneratorPreambleAndAssembly:
    """Test suite for preamble centralized styles and report assembly repeating headers."""

    def test_preamble_contains_centralized_styles(self):
        tex = preamble("Test Bridge", "JOB-101", "2026-11-20", "Rev 0")
        assert "bottom=32mm" in tex
        assert "footskip=18mm" in tex
        assert "osdagGreen" in tex
        assert "tableHeaderBg" in tex
        assert "statusPass" in tex
        assert "statusFail" in tex
        assert r"\renewcommand{\footrule}" in tex
        assert "-12pt" in tex

    def test_full_table_assembly_balance_and_syntax(self):
        raw_doc = r"""
\documentclass{report}
\begin{document}
\begin{longtable}{|C{3.4cm}|L{4.5cm}|C{2.3cm}|C{2.3cm}|>{\centering\arraybackslash}p{1.6cm}|}
\caption{\textbf{Overall Design Check Summary --- All Members}}
\hline
\textbf{Member / Check} & \textbf{Governing Load Combo} & \textbf{Demand} & \textbf{Capacity} & \textbf{UR} \\[6pt]
\hline
Girder Moment & ULS-01 & 1200 kNm & 1500 kNm & 0.80 \\[6pt]
\hline
Girder Shear & ULS-02 & 450 kN & 600 kN & 0.75 \\[6pt]
\hline
\end{longtable}
\end{document}
"""
        final_doc = apply_longtable_repeating_headers(raw_doc)
        assert r"\caption{\textbf{Overall Design Check Summary --- All Members}}\\" in final_doc
        assert r"\endfirsthead" in final_doc
        assert r"\multicolumn{5}{l}{\small\textbf{\tablename\ \thetable{} -- Continued from previous page}} \\[4pt]" in final_doc
        assert r"\endhead" in final_doc
        assert r"\endfoot" in final_doc
        assert r"\endlastfoot" in final_doc

        # Verify balanced begin/end environments
        begins = re.findall(r"\\begin\{([^}]+)\}", final_doc)
        ends = re.findall(r"\\end\{([^}]+)\}", final_doc)
        assert sorted(begins) == sorted(ends)

        # Verify balanced curly braces
        assert final_doc.count("{") == final_doc.count("}")

    def test_full_report_generation_integration(self):
        from osdagbridge.core.reports.report_generator import (
            ReportMetadata, ReportOptions, ReportRequest, ReportFigures, ReportPayload, generate_report
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            md = ReportMetadata(
                project_name="Phase 1 Verification Bridge",
                project_location="Delhi, India",
                designer="Osdag Lead",
                client="National Highways",
                company="IIT Bombay",
                job_number="JOB-P1-001",
                report_date="2026-11-20",
                reviewer="Peer Reviewer",
            )
            ro = ReportOptions(
                sections=["loads", "analysis", "design_checks", "drawings"],
                include_figures=False,
                include_toc=True,
                include_pdf=False,
            )
            req = ReportRequest(
                metadata=md,
                options=ro,
                output_dir=tmpdir,
                file_stem="phase1_test_report",
            )
            payload = ReportPayload(
                metadata=md,
                options=ro,
                inputs={"span": 30.0, "ts.no_of_girders": 2},
                analysis_summary={},
                design_checks=[],
                figures=ReportFigures(),
                log_entries=["Analysis initialized", "Checks passed"],
                output_dict={},
            )
            result = generate_report(payload, req)
            assert result.tex_path is not None
            assert os.path.exists(result.tex_path)

            with open(result.tex_path, "r", encoding="utf-8") as f:
                tex = f.read()

            # 1. Centralized geometry & clearance
            assert "bottom=32mm" in tex
            assert "footskip=18mm" in tex
            assert "osdagGreen" in tex
            assert "tableHeaderBg" in tex
            assert "statusPass" in tex

            # 2. Balanced environments and groups
            begins = re.findall(r"\\begin\{([^}]+)\}", tex)
            ends = re.findall(r"\\end\{([^}]+)\}", tex)
            assert sorted(begins) == sorted(ends)
            assert tex.count(r"\begingroup") == tex.count(r"\endgroup")

            # 3. Key multi-page tables have repeating headers
            key_captions = [
                r"\caption{\textbf{Load Combinations}}",
                r"\caption{\textbf{Girder Section Properties",
                r"\caption{\textbf{Shear Capacity Check}}",
                r"\caption{\textbf{Overall Design Check Summary --- All Members}}",
            ]
            for cap in key_captions:
                idx = tex.find(cap)
                assert idx != -1, f"Caption {cap} not found in output TeX"
                chunk = tex[idx - 50 : idx + 800]
                assert r"\endfirsthead" in chunk, f"{cap} missing \\endfirsthead"
                assert r"\endhead" in chunk, f"{cap} missing \\endhead"
                assert r"\endfoot" in chunk, f"{cap} missing \\endfoot"
                assert r"\endlastfoot" in chunk, f"{cap} missing \\endlastfoot"

            # 4. BOM table (Chapter 7) has repeating headers without caption inside table
            bom_idx = tex.find("Bill of Materials")
            assert bom_idx != -1
            bom_chunk = tex[bom_idx : bom_idx + 1200]
            assert r"\endfirsthead" in bom_chunk
            assert r"\endhead" in bom_chunk
            assert r"\endfoot" in bom_chunk
            assert r"\endlastfoot" in bom_chunk
