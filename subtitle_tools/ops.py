"""Transformations: shift, fps conversion, merge, overlap detection."""

from __future__ import annotations

from typing import List, Tuple

from .core import Cue, detect_overlaps


def shift(cues: List[Cue], delta_us: int) -> List[Cue]:
    """Move every cue by delta microseconds (negative = earlier).
    Times are clamped at 0."""
    out: List[Cue] = []
    for c in cues:
        start = max(0, c.start_us + delta_us)
        end = max(0, c.end_us + delta_us)
        out.append(Cue(start, end, c.text))
    return out


def convert_fps(cues: List[Cue], src_fps: float, dst_fps: float) -> List[Cue]:
    """Rescale timings when a subtitle was timed for the wrong frame rate
    (e.g. 23.976 fps subs on a 25 fps video)."""
    if src_fps <= 0 or dst_fps <= 0:
        raise ValueError("fps values must be positive")
    return [c.rescaled(src_fps / dst_fps) for c in cues]


def merge(a: List[Cue], b: List[Cue], gap_us: int = 1000) -> List[Cue]:
    """Merge two subtitle tracks (e.g. TR + EN) into a two-line track.

    Overlapping cues from the two tracks share the screen; otherwise they
    are concatenated chronologically. Returns sorted cues.
    """
    out: List[Cue] = []
    i = j = 0
    while i < len(a) or j < len(b):
        if j >= len(b) or (i < len(a) and a[i].start_us <= b[j].start_us):
            cue = a[i]
            i += 1
        else:
            cue = b[j]
            j += 1
        if out and cue.start_us < out[-1].end_us - gap_us:
            # overlap with the tail: merge into one two-line cue
            prev = out[-1]
            start = min(prev.start_us, cue.start_us)
            end = max(prev.end_us, cue.end_us)
            order = prev.text, cue.text
            out[-1] = Cue(start, end, order[0] + "\n" + order[1])
        else:
            out.append(cue)
    return out


def overlaps(cues: List[Cue]) -> List[Tuple[Cue, Cue]]:
    """Return the pairs of cues whose display times overlap."""
    bad: List[Tuple[Cue, Cue]] = []
    s = sorted(cues, key=lambda c: c.start_us)
    for i in range(1, len(s)):
        if s[i].start_us < s[i - 1].end_us:
            bad.append((s[i - 1], s[i]))
    return bad


def dedupe(cues: List[Cue]) -> List[Cue]:
    """Drop exact duplicate cues (same timing and text)."""
    seen = set()
    out: List[Cue] = []
    for c in sorted(cues, key=lambda c: (c.start_us, c.end_us, c.text)):
        key = (c.start_us, c.end_us, c.text)
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out
