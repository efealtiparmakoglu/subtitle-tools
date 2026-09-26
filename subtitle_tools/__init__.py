"""subtitle-tools — SRT/VTT shift, convert, merge, check."""

from .core import Cue, detect_overlaps, format_ts_srt, format_ts_vtt, parse_ts
from . import formats, ops

__version__ = "1.0.0"

__all__ = [
    "Cue",
    "detect_overlaps",
    "format_ts_srt",
    "format_ts_vtt",
    "parse_ts",
    "formats",
    "ops",
    "__version__",
]
