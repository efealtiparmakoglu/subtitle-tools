"""SRT and WebVTT readers/writers."""

from __future__ import annotations

from typing import List

from .core import Cue, format_ts_srt, format_ts_vtt, parse_ts


def parse_srt(text: str) -> List[Cue]:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\ufeff", "")
    blocks = text.split("\n\n")
    cues: List[Cue] = []
    for block in blocks:
        lines = [l for l in block.split("\n") if l.strip() != ""]
        if not lines:
            continue
        # the timing line may be preceded by an index line
        idx = 0
        if "-->" not in lines[0] and len(lines) >= 2 and "-->" in lines[1]:
            idx = 1
        if idx >= len(lines) or "-->" not in lines[idx]:
            continue
        timing = lines[idx]
        try:
            arrow = timing.index("-->")
            start = parse_ts(timing[:arrow].strip())
            # the end side may carry position coords after another space
            end_part = timing[arrow + 3 :].strip().split(" ")[0]
            end = parse_ts(end_part)
        except ValueError:
            continue
        body = "\n".join(lines[idx + 1 :]).strip()
        cues.append(Cue(start, end, body))
    return cues


def render_srt(cues: List[Cue]) -> str:
    blocks = []
    for i, c in enumerate(cues, 1):
        blocks.append(
            f"{i}\n{format_ts_srt(c.start_us)} --> {format_ts_srt(c.end_us)}\n{c.text}\n"
        )
    return "\n".join(blocks)


def parse_vtt(text: str) -> List[Cue]:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\ufeff", "")
    if text.startswith("WEBVTT"):
        head, _, rest = text.partition("\n\n")
    else:
        rest = text
    blocks = rest.split("\n\n")
    cues: List[Cue] = []
    for block in blocks:
        lines = [l for l in block.split("\n") if l.strip() != ""]
        if not lines:
            continue
        idx = 0
        if "-->" not in lines[0]:
            if len(lines) >= 2 and "-->" in lines[1]:
                idx = 1  # cue identifier line
            else:
                continue  # NOTE/STYLE/REGION blocks
        timing = lines[idx]
        arrow = timing.index("-->")
        start = parse_ts(timing[:arrow].strip())
        end_part = timing[arrow + 3 :].strip().split(" ")[0]
        end = parse_ts(end_part)
        body = "\n".join(lines[idx + 1 :]).strip()
        cues.append(Cue(start, end, body))
    return cues


def render_vtt(cues: List[Cue]) -> str:
    out = ["WEBVTT", ""]
    for i, c in enumerate(cues, 1):
        out.append(f"{format_ts_vtt(c.start_us)} --> {format_ts_vtt(c.end_us)}")
        out.append(c.text)
        if i < len(cues):
            out.append("")
    return "\n".join(out) + "\n"
