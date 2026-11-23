import matplotlib.pyplot as plt
from io import BytesIO

def generate_utilization_chart(data: dict, title: str = "Utilization Ratios") -> bytes:
    """Create a simple bar chart for utilization ratios.
    *data* keys are labels, values are utilization numbers (float).
    Returns PNG image bytes. Handles invalid input safely.
    """
    import math
    # Validate that data is a nonâ€‘empty dict of finite numbers
    if not isinstance(data, dict) or not data:
        return b""
    clean_data = {}
    for k, v in data.items():
        try:
            fv = float(v)
            if not math.isfinite(fv):
                return b""
            clean_data[k] = fv
        except Exception:
            return b""
    if not clean_data:
        return b""
    labels = list(clean_data.keys())
    values = list(clean_data.values())
    fig, ax = plt.subplots(figsize=(6, 4))
    try:
        bars = ax.bar(labels, values, color='skyblue')
        ax.axhline(1.0, color='red', linestyle='--', linewidth=1.5)
        ax.set_ylabel('Utilization Ratio')
        ax.set_title(title)
        ax.set_ylim(0, max(1.2, max(values) * 1.1))
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{val:.2f}",
                    ha='center', va='bottom', fontsize=8)
        buf = BytesIO()
        plt.tight_layout()
        fig.savefig(buf, format='png')
        return buf.getvalue()
    finally:
        # Ensure only this figure is closed
        plt.close(fig)
    """Create a simple bar chart for utilization ratios.
    *data* keys are labels, values are utilization numbers (float).
    Returns PNG image bytes.
    """
    labels = list(data.keys())
    values = [float(v) for v in data.values()]
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(labels, values, color='skyblue')
    # red dashed line at 1.0
    ax.axhline(1.0, color='red', linestyle='--', linewidth=1.5)
    ax.set_ylabel('Utilization Ratio')
    ax.set_title(title)
    ax.set_ylim(0, max(1.2, max(values) * 1.1))
    # annotate values
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{val:.2f}",
                ha='center', va='bottom', fontsize=8)
    buf = BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format='png')
    plt.close(fig)
    return buf.getvalue()

def generate_quantity_chart(labels: list, values: list, title: str = "Material Quantities") -> bytes:
    """Bar chart for material quantities with validation.
    *labels* and *values* must be same length and contain finite numbers.
    Returns PNG image bytes; empty bytes on invalid input.
    """
    import math
    if not isinstance(labels, list) or not isinstance(values, list):
        return b""
    if len(labels) != len(values) or not labels:
        return b""
    clean_labels = []
    clean_values = []
    for l, v in zip(labels, values):
        try:
            fv = float(v)
            if not math.isfinite(fv):
                return b""
            clean_labels.append(str(l))
            clean_values.append(fv)
        except Exception:
            return b""
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(clean_labels, clean_values, color='lightgreen')
    ax.set_ylabel('Quantity')
    ax.set_title(title)
    ax.set_ylim(0, max(clean_values) * 1.2 if clean_values else 1)
    for bar, val in zip(bars, clean_values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{val:.2f}",
                ha='center', va='bottom', fontsize=8)
    buf = BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format='png')
    plt.close(fig)
    return buf.getvalue()
    """Bar chart for material quantities.
    *labels* and *values* must be same length.
    Returns PNG image bytes.
    """
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(labels, values, color='lightgreen')
    ax.set_ylabel('Quantity')
    ax.set_title(title)
    ax.set_ylim(0, max(values) * 1.2 if values else 1)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{val:.2f}",
                ha='center', va='bottom', fontsize=8)
    buf = BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format='png')
    plt.close(fig)
    return buf.getvalue()
import re
from typing import Optional, List, Any, Union

from osdagbridge.core.utils.common import (
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GIRDER_DEPTH,
    KEY_TS_NO_OF_GIRDERS,
)

# =============================================================================
# COMMON HELPERS (determinism & validation)
# =============================================================================
from .determinism import format_status_text, validate_latex_balance, safe_float
import re
from typing import Optional, List, Any, Union

from osdagbridge.core.utils.common import (
    KEY_MP_GD_MEMBER_ID,
    KEY_MP_GD_SELECT_GIRDER,
    KEY_MP_GIRDER_DEPTH,
    KEY_TS_NO_OF_GIRDERS
)


def _tex(value):
    """Escape a Python value for safe LaTeX embedding."""
    s = str(value) if value is not None else ''
    if not s:
        return r''
    # Normalise non-ASCII glyphs from section designations (e.g. "âˆ  100 â…¹ 100â…¹ 10")
    # that pdflatex cannot render.
    for uni, ascii_ in [('âˆ ', 'L'), ('â…¹', 'x'), ('Ã—', 'x')]:
        s = s.replace(uni, ascii_)
    s = s.replace('\\', r'\textbackslash{}')
    for ch, esc in [('&', r'\&'), ('%', r'\%'), ('$', r'\$'), ('#', r'\#'),
                    ('{', r'\{'), ('}', r'\}'),
                    ('_', r'\_\allowbreak{}'),
                    ('~', r'\textasciitilde{}'), ('^', r'\^{}')]:
        s = s.replace(ch, esc)
    s = s.replace(':', r':\allowbreak{}')
    return s


def _render_value(source_dict, key, unit=""):
    val = source_dict.get(key)
    if val in ("", None):
        return ""
    return _tex(val) + unit


def get_girder_entries(input_dict):
    """
    Retrieve all girder labels and member IDs from backend keys.

    Usage Example:
    --------------------------
    girder_entries = get_girder_entries(bridge.input_dict)

    # 1. Fallback handling (if backend hasn't populated keys yet)
    if not girder_entries:
        n = int(bridge.input_dict.get(KEY_TS_NO_OF_GIRDERS, 1))
        girder_entries = [(f"Girder {i}", f"M1") for i in range(1, n + 1)]

    # 2. Get total number of girders safely
    n_girders = len(girder_entries)

    # 3. Iterate over the girders to build table rows
    for lbl, mid in girder_entries:
        # lbl will be e.g., "G1", mid will be e.g., "G1M1"
        # Access girder specific keys dynamically:
        # val = input_dict.get(f"{KEY_MP_GIRDER_DEPTH}.{lbl}.{mid}")
        pass

    Returns:
        List[Tuple[str, str]]
    """
    n = int(input_dict.get(KEY_TS_NO_OF_GIRDERS, 0))

    entries = []

    for i in range(1, n + 1):
        entries.append(
            (
                input_dict.get(f"{KEY_MP_GD_SELECT_GIRDER}.G{i}", ""),
                input_dict.get(f"{KEY_MP_GD_MEMBER_ID}.G{i}.M1", ""),
            )
        )

    return entries


def _fig_or_placeholder(path, caption, width=r'0.9\textwidth'):
    """Embed figure if path is provided (file already copied to assets), else show placeholder box.
    path is the relative path as pdflatex will see it (e.g. 'assets/plan.png').
    """
    if path:
        p = path.replace('\\', '/')
        return (r'\begin{figure}[H]' + '\n'
                r'\centering' + '\n'
                r'\includegraphics[width=' + width + ']{' + p + '}\n'
                r'\caption*{' + caption + '}\n'
                r'\end{figure}')
    return (r'\begin{figure}[H]' + '\n'
            r'\centering' + '\n'
            r'\fbox{\parbox{0.97\textwidth}{' + '\n'
            r'\textit{[ PLACEHOLDER: ' + caption + r' ]}' + '\n'
            r'}}' + '\n'
            r'\caption*{' + caption + '}\n'
            r'\end{figure}')

def _fig_embed(path, caption, width=r'\textwidth', height=None):
    """Embed a real figure when path is provided (already copied); otherwise use an fbox placeholder."""
    if path:
        p = path.replace('\\', '/')
        opts = 'width=' + width
        if height:
            opts += ',height=' + height + ',keepaspectratio'
        return (r'\begin{figure}[H]' + '\n'
                r'\vspace{-0.5em}' + '\n'
                r'\centering' + '\n'
                r'\includegraphics[' + opts + ']{' + p + '}\n'
                r'\vspace{0.5em}' + '\n'
                r'\caption*{\small ' + caption + '}\n'
                r'\vspace{-0.5em}' + '\n'
                r'\end{figure}')
    # fbox placeholder â€” matches template exactly
    return (r'\noindent\fbox{\parbox{0.97\textwidth}{' + '\n'
            r'\textit{[ PLACEHOLDER: ' + caption + r' ]}' + '\n'
            r'}}')


# =============================================================================
# REUSABLE LONGTABLE FORMATTERS AND REPEATING HEADERS
# =============================================================================

def extract_braced_content(text: str, start_idx: int):
    """Extract content enclosed in balanced braces starting at start_idx.

    Returns:
        (content_with_braces, next_index) or (None, start_idx) if unbalanced.
    """
    if start_idx >= len(text) or text[start_idx] != '{':
        return None, start_idx
    depth = 0
    for i in range(start_idx, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[start_idx:i + 1], i + 1
    return None, start_idx


def _process_single_longtable_body(body: str) -> str:
    """Transform the body of a longtable into one with repeating headers and footers.

    Ensures:
    - First head has caption ending in \\\\ (if caption is present) followed by \\endfirsthead.
    - Continuation head has continuation caption/note followed by \\endhead.
    - Intermediate pages have 'Continued on next page...' followed by \\endfoot.
    - Final page closes with \\endlastfoot.
    """
    # If already has non-empty endfirsthead and endhead, keep as-is
    if r'\endfirsthead' in body:
        if not re.search(r'\\endfirsthead\s*\\endhead', body):
            return body.strip()

    cap_idx = body.find(r'\caption')
    caption_block = ''
    rest = body
    if cap_idx != -1:
        first_hline = body.find(r'\hline')
        if first_hline == -1 or cap_idx < first_hline:
            cmd_end = cap_idx + len(r'\caption')
            if cmd_end < len(body) and body[cmd_end] == '*':
                cmd_end += 1
            s = body[cmd_end:]
            m_opt = re.match(r'^\s*\[([^\]]*)\]', s)
            if m_opt:
                cmd_end += m_opt.end()
            b_start = body.find('{', cmd_end)
            if b_start != -1:
                b_content, b_end = extract_braced_content(body, b_start)
                if b_content:
                    cap_full = body[cap_idx:b_end].strip()
                    curr_pos = b_end
                    m_lbl = re.match(r'^\s*\\label', body[curr_pos:])
                    if m_lbl:
                        lbl_brace = body.find('{', curr_pos + m_lbl.end() - 1)
                        if lbl_brace != -1:
                            _, lbl_end = extract_braced_content(body, lbl_brace)
                            cap_full += ' ' + body[curr_pos:lbl_end].strip()
                            curr_pos = lbl_end
                    m_sl = re.match(r'^\s*\\\\', body[curr_pos:])
                    if m_sl:
                        curr_pos += m_sl.end()
                    caption_block = cap_full
                    rest = body[:cap_idx] + body[curr_pos:]

    hlines = list(re.finditer(r'\\hline', rest))
    if len(hlines) < 2:
        return body.strip()

    pre_table = rest[:hlines[0].start()].strip()
    hdr_start = hlines[0].end()
    hdr_end = hlines[1].start()
    hdr_rows = rest[hdr_start:hdr_end].strip()

    # Clean any stray/broken \endfirsthead \endhead within headers
    hdr_rows_clean = re.sub(r'\\endfirsthead\s*\\endhead', '', hdr_rows).strip()
    if not hdr_rows_clean:
        return body.strip()

    max_amps = 0
    for row in hdr_rows_clean.split(r'\\'):
        c_row = re.sub(r'%.*$', '', row).strip()
        if c_row:
            max_amps = max(max_amps, c_row.count('&'))
    ncols = max(max_amps + 1, 1)

    data_rows = rest[hlines[1].end():].strip()
    data_rows = re.sub(r'\\endfirsthead\s*\\endhead', '', data_rows).strip()
    if data_rows and not data_rows.rstrip().endswith(r'\hline'):
        data_rows += '\n\\hline'

    out = []
    if pre_table:
        out.append(pre_table)
    if caption_block:
        out.append(caption_block + r'\\')
    out.append(r'\hline')
    out.append(hdr_rows_clean)
    out.append(r'\hline')
    out.append(r'\endfirsthead')
    out.append('')
    if caption_block:
        out.append(f'\\multicolumn{{{ncols}}}{{l}}{{\\small\\textbf{{\\tablename\\ \\thetable{{}} -- Continued from previous page}}}} \\\\[4pt]')
    else:
        out.append(f'\\multicolumn{{{ncols}}}{{l}}{{\\small\\textit{{(Continued from previous page)}}}} \\\\[4pt]')
    out.append(r'\hline')
    out.append(hdr_rows_clean)
    out.append(r'\hline')
    out.append(r'\endhead')
    out.append('')
    out.append(r'\hline')
    out.append(f'\\multicolumn{{{ncols}}}{{r}}{{\\footnotesize\\textit{{Continued on next page\\ldots}}}} \\\\')
    out.append(r'\endfoot')
    out.append('')
    out.append(r'\endlastfoot')
    out.append('')
    out.append(data_rows)

    return '\n'.join(out)


def apply_longtable_repeating_headers(tex_content: str) -> str:
    """Parse and transform all longtable environments in a LaTeX document to repeat headers.

    Preserves existing captions and column structures while adding \\endfirsthead,
    continuation headers with \\endhead, continuation footers with \\endfoot, and \\endlastfoot.
    """
    pattern_tag = r'\begin{longtable}'
    end_tag = r'\end{longtable}'
    out = []
    curr = 0
    L = len(tex_content)

    while curr < L:
        start_idx = tex_content.find(pattern_tag, curr)
        if start_idx == -1:
            out.append(tex_content[curr:])
            break

        out.append(tex_content[curr:start_idx])

        brace_start = tex_content.find('{', start_idx + len(pattern_tag))
        if brace_start == -1:
            out.append(tex_content[start_idx:])
            break

        col_spec_full, spec_end = extract_braced_content(tex_content, brace_start)
        if not col_spec_full:
            out.append(tex_content[start_idx:])
            break

        end_idx = tex_content.find(end_tag, spec_end)
        if end_idx == -1:
            out.append(tex_content[start_idx:])
            break

        body = tex_content[spec_end:end_idx]
        transformed_body = _process_single_longtable_body(body)

        out.append(pattern_tag + col_spec_full + '\n' + transformed_body + '\n' + end_tag)
        curr = end_idx + len(end_tag)

    return ''.join(out)


def format_longtable(
    col_spec: str,
    headers: Union[List[str], str],
    rows: Union[List[str], str],
    caption: Optional[str] = None,
    label: Optional[str] = None,
    continuation_note: Optional[str] = None,
    continuation_footer: bool = True,
    table_note: Optional[str] = None,
) -> str:
    """Construct a complete LaTeX longtable environment with repeating headers and footers.

    Parameters:
        col_spec: Column specification (e.g., '|C{2.5cm}|L{8.0cm}|p{5.0cm}|')
        headers: List of column header names, or pre-formatted LaTeX header row string
        rows: List of row strings, or single pre-formatted string of rows
        caption: Optional table caption (placed in first head with proper \\\\)
        label: Optional LaTeX label (e.g. 'tab:load-combos')
        continuation_note: Custom continuation heading note for repeated pages
        continuation_footer: If True, adds 'Continued on next page...' footer on intermediate pages
        table_note: Optional explanatory footnote rendered under the table

    Returns:
        Complete LaTeX longtable environment string.
    """
    col_spec = col_spec.strip()
    if not col_spec.startswith('{'):
        col_spec = f"{{{col_spec}}}"

    if isinstance(headers, (list, tuple)):
        ncols = len(headers)
        hdr_str = " & ".join(r"\textbf{" + str(h) + "}" for h in headers) + r" \\[6pt]"
    else:
        hdr_str = str(headers).strip()
        if hdr_str.endswith(r'\hline'):
            hdr_str = hdr_str[:-6].strip()
        ncols = max(hdr_str.count('&') + 1, 1)

    if isinstance(rows, (list, tuple)):
        body_str = "\n".join(r.strip() for r in rows if r)
    else:
        body_str = str(rows).strip()

    if body_str and not body_str.rstrip().endswith(r'\hline'):
        body_str += '\n\\hline'

    parts = [r"\begin{longtable}" + col_spec]

    # First head
    if caption:
        cap_line = r"\caption{" + caption + "}"
        if label:
            cap_line += r"\label{" + label + "}"
        cap_line += r"\\"
        parts.append(cap_line)
    parts.append(r"\hline")
    parts.append(hdr_str)
    parts.append(r"\hline")
    parts.append(r"\endfirsthead")
    parts.append("")

    # Continuation head
    if continuation_note:
        parts.append(f"\\multicolumn{{{ncols}}}{{l}}{{\\small\\textbf{{{continuation_note}}}}} \\\\[4pt]")
    elif caption:
        parts.append(f"\\multicolumn{{{ncols}}}{{l}}{{\\small\\textbf{{\\tablename\\ \\thetable{{}} -- Continued from previous page}}}} \\\\[4pt]")
    else:
        parts.append(f"\\multicolumn{{{ncols}}}{{l}}{{\\small\\textit{{(Continued from previous page)}}}} \\\\[4pt]")
    parts.append(r"\hline")
    parts.append(hdr_str)
    parts.append(r"\hline")
    parts.append(r"\endhead")
    parts.append("")

    # Continuation foot
    if continuation_footer:
        parts.append(r"\hline")
        parts.append(f"\\multicolumn{{{ncols}}}{{r}}{{\\footnotesize\\textit{{Continued on next page\\ldots}}}} \\\\")
        parts.append(r"\endfoot")
    else:
        parts.append(r"\endfoot")
    parts.append("")

    # Last foot
    parts.append(r"\endlastfoot")
    parts.append("")

    # Body
    parts.append(body_str)
    parts.append(r"\end{longtable}")

    if table_note:
        parts.append(r"\noindent\textit{" + table_note + "}")

    return "\n".join(parts)


# =============================================================================
# REUSABLE MATPLOTLIB FIGURE SAVER
# =============================================================================

def save_matplotlib_figure(fig: Any, output_dir: str, filename: str, dpi: int = 300, close: bool = True) -> str:
    """Save a matplotlib figure to output_dir with 300 DPI resolution and cleanly close it.

    Parameters:
        fig: matplotlib Figure object (or any object with a savefig method)
        output_dir: Directory path where the image will be saved
        filename: Output image filename (e.g. 'bm_envelope.png')
        dpi: Target image resolution in DPI (default: 300)
        close: Whether to close the figure after saving to prevent memory leaks (default: True)

    Returns:
        Absolute normalized path to the saved PNG image, or empty string on failure.
    """
    if fig is None:
        return ""

    try:
        os.makedirs(output_dir, exist_ok=True)
        if not filename.lower().endswith(".png"):
            filename += ".png"
        out_path = os.path.join(output_dir, filename)

        if hasattr(fig, "savefig"):
            fig.savefig(out_path, dpi=dpi, bbox_inches="tight")

        if close:
            try:
                import matplotlib.pyplot as plt
                plt.close(fig)
            except Exception:
                pass

        return os.path.abspath(out_path).replace("\\", "/")
    except Exception:
        return ""
