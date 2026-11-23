"""Centralized styling, geometry, and layout constants for OsdagBridge reports.

Single Source of Truth for:
- Page geometry & footer clearance (fixing row/footer collisions on multi-page longtables)
- Spacing constants (arraystretch, tabcolsep, extrarowheight, etc.)
- Color definitions (osdagGreen = #91B014, table headers, alternating rows, status indicators)
- Matplotlib chart styling defaults (300 DPI, clean publication theme)
"""

import os
from typing import Dict, Any, Optional

# =============================================================================
# 1. PAGE LAYOUT & GEOMETRY
# =============================================================================
# Generous bottom margin (32mm / ~1.26in) and footskip (18mm / ~51pt) guarantee
# that multi-page longtable rows, footnotes, and the footrule line never collide
# or bleed into the footer block (resolving issues such as Page 30 row overlap).

PAGE_PAPER = "a4paper"
MARGIN_TOP = "25mm"
MARGIN_BOTTOM = "32mm"
MARGIN_LEFT = "25mm"
MARGIN_RIGHT = "25mm"
HEAD_HEIGHT = "16pt"
HEAD_SEP = "12pt"
FOOT_SKIP = "18mm"

# Footrule vertical offsets within fancyhdr
FOOTRULE_DEFAULT_VSPACE = "-8pt"
FOOTRULE_SD_NOTE_VSPACE = "-12pt"  # software default note spacing (prevents bleeding into text)
FOOTRULE_RULE_VSPACE = "4pt"
FOOTRULE_POST_VSPACE = "6pt"

# =============================================================================
# 2. TABLE SPACING & SIZING CONSTANTS
# =============================================================================
TABCOLSEP = "6pt"
ARRAYSTRETCH = 1.15
LTPRE = "0pt"
LTPOST = "6pt"
ARRAYRULEWIDTH = "0.5pt"
EXTRAROWHEIGHT = "0.6pt"
LINE_STRETCH = 1.15
NEEDSPACE_TABLE = "5\\baselineskip"
NEEDSPACE_LONGTABLE = "5\\baselineskip"

# =============================================================================
# 3. COLOR DEFINITIONS
# =============================================================================
# Brand colors
COLOR_OSDAG_GREEN_HEX = "91B014"
COLOR_OSDAG_GREEN_NAME = "osdagGreen"

# Table shading colors
COLOR_TABLE_HEADER_BG_HEX = "EFEFEF"
COLOR_TABLE_HEADER_BG_NAME = "tableHeaderBg"
COLOR_TABLE_ROW_ALT_HEX = "F8F9FA"
COLOR_TABLE_ROW_ALT_NAME = "tableRowAltBg"

# Status colors
COLOR_STATUS_PASS_HEX = "1B5E20"    # Dark Green
COLOR_STATUS_PASS_NAME = "statusPass"
COLOR_STATUS_FAIL_HEX = "C62828"    # Strong Red
COLOR_STATUS_FAIL_NAME = "statusFail"
COLOR_STATUS_WARN_HEX = "E65100"    # Amber / Orange
COLOR_STATUS_WARN_NAME = "statusWarn"
COLOR_STATUS_NA_HEX = "616161"      # Medium Gray
COLOR_STATUS_NA_NAME = "statusNA"

# Mapping for status badges / LaTeX colors
STATUS_COLORS = {
    "PASS": COLOR_STATUS_PASS_NAME,
    "FAIL": COLOR_STATUS_FAIL_NAME,
    "WARNING": COLOR_STATUS_WARN_NAME,
    "WARN": COLOR_STATUS_WARN_NAME,
    "N/A": COLOR_STATUS_NA_NAME,
    "NA": COLOR_STATUS_NA_NAME,
}

# =============================================================================
# 4. MATPLOTLIB CHART STYLING DEFAULTS
# =============================================================================
MATPLOTLIB_DPI = 300
FIGURE_DEFAULT_SIZE = (8, 5)
FIGURE_WIDE_SIZE = (10, 5)
FONT_FAMILY = "sans-serif"
FONT_SANS_SERIF = ["DejaVu Sans", "Arial", "Helvetica", "sans-serif"]
FONT_SIZE_TITLE = 12
FONT_SIZE_LABEL = 10
FONT_SIZE_TICK = 8
FONT_SIZE_LEGEND = 8
LINE_WIDTH = 1.5
GRID_LINE_STYLE = "--"
GRID_ALPHA = 0.5
GRID_COLOR = "#D0D0D0"

CHART_COLOR_PALETTE = [
    "#91B014",  # Osdag Green
    "#1E88E5",  # Steel Blue
    "#E53935",  # Crimson
    "#FB8C00",  # Amber Orange
    "#43A047",  # Forest Green
    "#8E24AA",  # Purple
    "#546E7A",  # Blue Grey
]

MATPLOTLIB_RC_PARAMS: Dict[str, Any] = {
    "figure.dpi": MATPLOTLIB_DPI,
    "savefig.dpi": MATPLOTLIB_DPI,
    "font.size": FONT_SIZE_LABEL,
    "font.family": FONT_FAMILY,
    "font.sans-serif": FONT_SANS_SERIF,
    "axes.titlesize": FONT_SIZE_TITLE,
    "axes.labelsize": FONT_SIZE_LABEL,
    "axes.grid": True,
    "grid.linestyle": GRID_LINE_STYLE,
    "grid.alpha": GRID_ALPHA,
    "grid.color": GRID_COLOR,
    "lines.linewidth": LINE_WIDTH,
    "xtick.labelsize": FONT_SIZE_TICK,
    "ytick.labelsize": FONT_SIZE_TICK,
    "legend.fontsize": FONT_SIZE_LEGEND,
    "legend.framealpha": 0.8,
}


def apply_matplotlib_style(plt_or_module=None) -> bool:
    """Apply centralized matplotlib styling defaults.

    Returns True if successfully applied, False if matplotlib is unavailable.
    """
    try:
        if plt_or_module is None:
            import matplotlib as mpl
        elif hasattr(plt_or_module, "rcParams"):
            mpl = plt_or_module
        elif hasattr(plt_or_module, "matplotlib"):
            mpl = plt_or_module.matplotlib
        else:
            return False

        from cycler import cycler
        params = dict(MATPLOTLIB_RC_PARAMS)
        params["axes.prop_cycle"] = cycler(color=CHART_COLOR_PALETTE)
        mpl.rcParams.update(params)
        return True
    except Exception:
        return False


# =============================================================================
# 5. LATEX SNIPPET GENERATORS
# =============================================================================

def get_geometry_latex() -> str:
    """Return LaTeX \\usepackage[...]{geometry} configuration with generous footer clearance."""
    return (
        f"\\usepackage[\n"
        f"  {PAGE_PAPER},\n"
        f"  top={MARGIN_TOP},\n"
        f"  bottom={MARGIN_BOTTOM},\n"
        f"  left={MARGIN_LEFT},\n"
        f"  right={MARGIN_RIGHT},\n"
        f"  headheight={HEAD_HEIGHT},\n"
        f"  headsep={HEAD_SEP},\n"
        f"  footskip={FOOT_SKIP}\n"
        f"]{{geometry}}"
    )


def get_color_definitions_latex() -> str:
    """Return LaTeX \\definecolor statements for brand, tables, and statuses."""
    return (
        f"\\definecolor{{{COLOR_OSDAG_GREEN_NAME}}}{{HTML}}{{{COLOR_OSDAG_GREEN_HEX}}}\n"
        f"\\definecolor{{{COLOR_TABLE_HEADER_BG_NAME}}}{{HTML}}{{{COLOR_TABLE_HEADER_BG_HEX}}}\n"
        f"\\definecolor{{{COLOR_TABLE_ROW_ALT_NAME}}}{{HTML}}{{{COLOR_TABLE_ROW_ALT_HEX}}}\n"
        f"\\definecolor{{{COLOR_STATUS_PASS_NAME}}}{{HTML}}{{{COLOR_STATUS_PASS_HEX}}}\n"
        f"\\definecolor{{{COLOR_STATUS_FAIL_NAME}}}{{HTML}}{{{COLOR_STATUS_FAIL_HEX}}}\n"
        f"\\definecolor{{{COLOR_STATUS_WARN_NAME}}}{{HTML}}{{{COLOR_STATUS_WARN_HEX}}}\n"
        f"\\definecolor{{{COLOR_STATUS_NA_NAME}}}{{HTML}}{{{COLOR_STATUS_NA_HEX}}}"
    )


def get_table_spacing_latex() -> str:
    """Return table layout and spacing LaTeX commands."""
    return (
        f"% Table layout and spacing: consistent padding, row height, and longtable pre/post skips\n"
        f"\\setlength{{\\tabcolsep}}{{{TABCOLSEP}}}\n"
        f"\\renewcommand{{\\arraystretch}}{{{ARRAYSTRETCH}}}\n"
        f"\\setlength{{\\LTpre}}{{{LTPRE}}}\n"
        f"\\setlength{{\\LTpost}}{{{LTPOST}}}\n"
        f"% Table rules (outline thickness) and small extra row height for clarity\n"
        f"\\setlength{{\\arrayrulewidth}}{{{ARRAYRULEWIDTH}}}\n"
        f"\\setlength{{\\extrarowheight}}{{{EXTRAROWHEIGHT}}}\n\n"
        f"% Prevent tables from overflowing past the page bottom:\n"
        f"% if fewer than 5 baseline-skips remain, break to the next page first.\n"
        f"\\BeforeBeginEnvironment{{table}}{{\\needspace{{{NEEDSPACE_TABLE}}}}}\n"
        f"\\BeforeBeginEnvironment{{longtable}}{{\\needspace{{{NEEDSPACE_LONGTABLE}}}}}"
    )


def get_footrule_definition_latex() -> str:
    """Return footrule LaTeX definition with generous clearance."""
    return (
        f"  \\renewcommand{{\\footrule}}{{%\n"
        f"    \\ifbool{{hasSDonPage}}{{%\n"
        f"      \\vspace{{{FOOTRULE_SD_NOTE_VSPACE}}}%\n"
        f"      \\hbox to \\headwidth{{\\textcolor{{black}}{{\\footnotesize\\textit{{* Software default value}}}}\\hfil}}%\n"
        f"      \\vspace{{{FOOTRULE_RULE_VSPACE}}}%\n"
        f"    }}{{%\n"
        f"      \\vspace{{{FOOTRULE_DEFAULT_VSPACE}}}%\n"
        f"    }}%\n"
        f"    \\color{{{COLOR_OSDAG_GREEN_NAME}}}\\hrule width\\headwidth height 1pt \\vspace{{{FOOTRULE_POST_VSPACE}}}%\n"
        f"  }}"
    )


def get_status_badge_latex(status: str) -> str:
    """Return a colored status text badge for LaTeX tables."""
    key = str(status).strip().upper()
    color_name = STATUS_COLORS.get(key, COLOR_STATUS_NA_NAME)
    return f"\\textcolor{{{color_name}}}{{\\textbf{{{status}}}}}"
