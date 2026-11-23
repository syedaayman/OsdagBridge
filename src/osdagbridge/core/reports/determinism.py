import math
from typing import Any

def format_status_text(status: str) -> str:
    """Standardize status text for LaTeX.

    Currently returns the raw status string, but can be extended to wrap with
    LaTeX colour commands (e.g., ``\\textcolor{red}{FAIL}``).
    """
    return status

def validate_latex_balance(tex_str: str) -> bool:
    """Validate that LaTeX groups are balanced.

    Checks that the numbers of ``\\begin{...}``/``\\end{...}`` and
    ``\\begingroup``/``\\endgroup`` pairs match. Raises ``ValueError`` if an
    imbalance is detected.
    """
    import re as _re
    begin_cnt = len(_re.findall(r'\\\\begin\{', tex_str))
    end_cnt = len(_re.findall(r'\\\\end\{', tex_str))
    if begin_cnt != end_cnt:
        raise ValueError(f"Unbalanced \\begin{{}} / \\end{{}} count: {begin_cnt} vs {end_cnt}")
    begingroup_cnt = tex_str.count('\\begingroup')
    endgroup_cnt = tex_str.count('\\endgroup')
    if begingroup_cnt != endgroup_cnt:
        raise ValueError(f"Unbalanced \\begingroup / \\endgroup count: {begingroup_cnt} vs {endgroup_cnt}")
    return True

def safe_float(value: Any) -> float:
    """Convert a value to float safely, returning ``float('nan')`` on failure.

    Handles ``None``, empty strings, and non‑numeric types gracefully.
    """
    try:
        return float(value)
    except Exception:
        return float('nan')
