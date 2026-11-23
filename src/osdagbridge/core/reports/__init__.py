"""Reports package."""
from .report_generator import (
    ReportMetadata,
    ReportOptions,
    ReportRequest,
    ReportFigures,
    ReportPayload,
    ReportResult,
    build_report_payload,
    generate_report,
)
from .report_utils import (
    apply_longtable_repeating_headers,
    format_longtable,
    save_matplotlib_figure,
)

__all__ = [
    "ReportMetadata", "ReportOptions", "ReportRequest",
    "ReportFigures", "ReportPayload", "ReportResult",
    "build_report_payload", "generate_report",
    "apply_longtable_repeating_headers", "format_longtable", "save_matplotlib_figure",
]
