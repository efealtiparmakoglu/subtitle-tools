"""subtitle-tools CLI: shift / convert / merge / check subtitles."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import formats, ops
from .core import parse_ts

VERSION = "1.0.0"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="subtitle-tools",
        description="Shift, convert and merge SRT/VTT subtitles.",
    )
    p.add_argument("--version", action="version", version=f"subtitle-tools {VERSION}")
    sub = p.add_subparsers(dest="command", required=True)

    def common(sp):
        sp.add_argument("input", help="SRT or VTT file")
        sp.add_argument("-o", "--out", help="output file (default: stdout)")
        sp.add_argument("--to", choices=["srt", "vtt"], help="output format (default: same as input)")

    sh = sub.add_parser("shift", help="move all cues by an offset")
    common(sh)
    sh.add_argument("--delay", help="e.g. 3.5s, -250ms, 1m10s, 90f (needs --fps)")
    sh.add_argument("--fps", type=float, help="frame rate for frame-based delays")

    fc = sub.add_parser("fps", help="rescale timings between frame rates")
    common(fc)
    fc.add_argument("--from-fps", dest="src", type=float, required=True, help="source fps")
    fc.add_argument("--to-fps", dest="dst", type=float, help="target fps (or positional)")
    fc.add_argument("dest_fps", nargs="?", type=float, help="target fps")

    mg = sub.add_parser("merge", help="merge two subtitle tracks (dual language)")
    mg.add_argument("first")
    mg.add_argument("second")
    mg.add_argument("-o", "--out", help="output file (default: stdout)")
    mg.add_argument("--to", choices=["srt", "vtt"], default="srt")

    ck = sub.add_parser("check", help="detect overlapping cues")
    ck.add_argument("input")
    ck.add_argument("--json", action="store_true")
    return p


def sniff(path: Path) -> str:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    if text.lstrip().startswith("WEBVTT"):
        return "vtt"
    return "srt"


def load(path: Path):
    fmt = sniff(path)
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    cues = formats.parse_vtt(text) if fmt == "vtt" else formats.parse_srt(text)
    return fmt, cues


def output_format(args, input_fmt: str) -> str:
    to = getattr(args, "to", None)
    if to:
        return to
    return input_fmt


def emit(cues, fmt: str, out: str) -> None:
    text = formats.render_vtt(cues) if fmt == "vtt" else formats.render_srt(cues)
    if out:
        Path(out).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "shift":
        fmt, cues = load(Path(args.input))
        delta = parse_delay(args.delay, args.fps)
        emit(ops.shift(cues, delta), output_format(args, fmt), args.out)
        return 0

    if args.command == "fps":
        fmt, cues = load(Path(args.input))
        dst = args.dst if args.dst is not None else args.dest_fps
        if dst is None:
            parser.error("fps needs a target rate (--to-fps N or positional)")
        emit(ops.convert_fps(cues, args.src, dst), output_format(args, fmt), args.out)
        return 0

    if args.command == "merge":
        f1, c1 = load(Path(args.first))
        f2, c2 = load(Path(args.second))
        merged = ops.merge(c1, c2)
        text = formats.render_vtt(merged) if args.to == "vtt" else formats.render_srt(merged)
        if args.out:
            Path(args.out).write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
        return 0

    if args.command == "check":
        fmt, cues = load(Path(args.input))
        pairs = ops.overlaps(cues)
        if args.json:
            import json
            print(json.dumps([
                {
                    "a": [formats.format_ts_srt(a.start), formats.format_ts_srt(a.end)],
                    "b": [formats.format_ts_srt(b.start), formats.format_ts_srt(b.end)],
                }
                for a, b in pairs
            ]))
        elif not pairs:
            print("no overlaps")
        else:
            for a, b in pairs:
                print(
                    f"OVERLAP: [{formats.format_ts_srt(a.start)} -> {formats.format_ts_srt(a.end)}]"
                    f" vs [{formats.format_ts_srt(b.start)} -> {formats.format_ts_srt(b.end)}]"
                )
        return 1 if pairs else 0

    return 2


def parse_delay(text: str, fps: float) -> int:
    """Parse '3.5s', '-250ms', '1m10s', '90f' into microseconds."""
    if text is None:
        raise SystemExit("shift needs --delay")
    text = text.strip().lower().replace(" ", "")
    total = 0.0
    number = ""
    units = {"h": 3_600_000_000, "m": 60_000_000, "s": 1_000_000, "ms": 1_000}
    i = 0
    sign = 1.0
    if text.startswith("-"):
        sign = -1.0
        i = 1
    if text.endswith("f"):
        if not fps or fps <= 0:
            raise SystemExit("frame delays need --fps")
        frames = float(text[:-1])
        return round(sign * frames / fps * 1_000_000)
    while i < len(text):
        ch = text[i]
        if ch.isdigit() or ch == ".":
            number += ch
            i += 1
            continue
        unit = ""
        while i < len(text) and text[i].isalpha():
            unit += text[i]
            i += 1
        if unit not in units:
            raise SystemExit(f"unknown delay unit {unit!r}")
        total += float(number or 0) * units[unit]
        number = ""
    if number:
        total += float(number)  # bare number = seconds
    return round(sign * total)  # total is already in microseconds


if __name__ == "__main__":
    sys.exit(main())
