"""Subtitle model: cues with microsecond timing shared by all formats."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Cue:
    start_us: int  # microseconds
    end_us: int
    text: str  # lines joined with \n

    def shifted(self, delta_us: int) -> "Cue":
        return Cue(self.start_us + delta_us, self.end_us + delta_us, self.text)

    def rescaled(self, factor: float) -> "Cue":
        return Cue(
            round(self.start_us * factor),
            round(self.end_us * factor),
            self.text,
        )


def parse_ts(text: str, fps: float = 0.0) -> int:
    """Parse a timestamp in SRT (00:00:01,250), VTT (00:00:01.250) or
    frames ('123f') form into microseconds."""
    text = text.strip()
    if text.endswith("f"):
        if fps <= 0:
            raise ValueError(f"frame timestamp {text!r} needs --fps")
        frames = float(text[:-1])
        return round(frames / fps * 1_000_000)
    parts = text.replace(",", ".").split(":")
    if len(parts) == 3:
        h, m, s = parts
        total = float(h) * 3600 + float(m) * 60 + float(s)
    elif len(parts) == 2:
        total = float(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 1:
        total = float(parts[0])
    else:
        raise ValueError(f"bad timestamp {text!r}")
    return round(total * 1_000_000)


def format_ts_srt(us: int) -> str:
    us = max(0, us)
    h, rem = divmod(us, 3_600_000_000)
    m, rem = divmod(rem, 60_000_000)
    s, us = divmod(rem, 1_000_000)
    return f"{h:02d}:{m:02d}:{s:02d},{us // 1000:03d}"


def format_ts_vtt(us: int) -> str:
    us = max(0, us)
    h, rem = divmod(us, 3_600_000_000)
    m, rem = divmod(rem, 60_000_000)
    s, us = divmod(rem, 1_000_000)
    return f"{h:02d}:{m:02d}:{s:02d}.{us // 1000:03d}"


def detect_overlaps(cues: List[Cue], tolerance_us: int = 1) -> List[int]:
    """Return the indices of cues overlapping their predecessor."""
    bad: List[int] = []
    ordered = sorted(range(len(cues)), key=lambda i: cues[i].start_us)
    prev = None
    for i in ordered:
        c = cues[i]
        if prev is not None and c.start_us < cues[prev].end_us - tolerance_us:
            bad.append(i)
        prev = i
    return bad
