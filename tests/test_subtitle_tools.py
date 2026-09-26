import unittest

from subtitle_tools import formats, ops
from subtitle_tools.core import parse_ts, format_ts_srt, format_ts_vtt

SRT = """1
00:00:01,000 --> 00:00:03,500
Hello there.

2
00:00:04,000 --> 00:00:06,000
General Kenobi!
"""

VTT = """WEBVTT

00:00:01.000 --> 00:00:03.500
Hello there.

intro
00:00:04.000 --> 00:00:06.000
General Kenobi!
"""


class TimestampTests(unittest.TestCase):
    def test_srt_and_vtt_forms(self):
        self.assertEqual(parse_ts("00:00:01,250"), 1_250_000)
        self.assertEqual(parse_ts("00:00:01.250"), 1_250_000)
        self.assertEqual(parse_ts("01:02:03,004"), 3_723_004_000)

    def test_short_form(self):
        self.assertEqual(parse_ts("01.5"), 1_500_000)

    def test_frames(self):
        self.assertEqual(parse_ts("25f", 25.0), 1_000_000)
        with self.assertRaises(ValueError):
            parse_ts("25f")  # no fps

    def test_formatting(self):
        self.assertEqual(format_ts_srt(3_723_004_000), "01:02:03,004")
        self.assertEqual(format_ts_vtt(3_723_004_000), "01:02:03.004")


class SrtTests(unittest.TestCase):
    def test_parse_render_roundtrip(self):
        cues = formats.parse_srt(SRT)
        self.assertEqual(len(cues), 2)
        self.assertEqual(cues[0].start_us, 1_000_000)
        self.assertEqual(cues[0].end_us, 3_500_000)
        self.assertEqual(cues[0].text, "Hello there.")
        out = formats.render_srt(cues)
        self.assertEqual(formats.parse_srt(out), cues)

    def test_missing_index_line(self):
        cues = formats.parse_srt("00:00:01,000 --> 00:00:02,000\nhi\n")
        self.assertEqual(cues[0].text, "hi")


class VttTests(unittest.TestCase):
    def test_parse_with_identifier(self):
        cues = formats.parse_vtt(VTT)
        self.assertEqual(len(cues), 2)
        self.assertEqual(cues[1].text, "General Kenobi!")

    def test_render_vtt_header(self):
        text = formats.render_vtt(formats.parse_vtt(VTT))
        self.assertTrue(text.startswith("WEBVTT\n"))

    def test_srt_to_vtt_convert(self):
        cues = formats.parse_srt(SRT)
        text = formats.render_vtt(cues)
        back = formats.parse_vtt(text)
        self.assertEqual(back, cues)


class ShiftTests(unittest.TestCase):
    def test_shift_forward_and_back(self):
        cues = formats.parse_srt(SRT)
        fwd = ops.shift(cues, 500_000)
        self.assertEqual(fwd[0].start_us, 1_500_000)
        back = ops.shift(fwd, -500_000)
        self.assertEqual(back, cues)

    def test_clamp_at_zero(self):
        cues = formats.parse_srt(SRT)
        early = ops.shift(cues, -5_000_000)
        self.assertEqual(early[0].start_us, 0)


class FpsTests(unittest.TestCase):
    def test_23976_to_25(self):
        cues = [__import__("subtitle_tools").core.Cue(1_000_000, 2_000_000, "x")]
        out = ops.convert_fps(cues, 23.976, 25.0)
        # 1s at 23.976 becomes 0.9590..s
        self.assertEqual(out[0].start_us, round(1_000_000 * 23.976 / 25.0))

    def test_rejects_zero_fps(self):
        with self.assertRaises(ValueError):
            ops.convert_fps([], 0, 25)


class MergeTests(unittest.TestCase):
    def test_dual_language_merge(self):
        tr = formats.parse_srt(SRT)
        en = [
            __import__("subtitle_tools").core.Cue(1_000_000, 3_500_000, "Hello there!"),
        ]
        merged = ops.merge(tr, en)
        self.assertEqual(len(merged), 2)
        # the overlapping pair becomes one two-line cue
        self.assertIn("Hello there.", merged[0].text.split("\n")[0] + merged[0].text.split("\n")[-1])

    def test_chronological_merge(self):
        a = formats.parse_srt("1\n00:00:01,000 --> 00:00:02,000\nA\n")
        b = formats.parse_srt("1\n00:00:05,000 --> 00:00:06,000\nB\n")
        merged = ops.merge(a, b)
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0].text, "A")
        self.assertEqual(merged[1].text, "B")


class OverlapTests(unittest.TestCase):
    def test_detects_overlap(self):
        cues = formats.parse_srt(
            "1\n00:00:01,000 --> 00:00:05,000\nA\n\n"
            "2\n00:00:04,000 --> 00:00:06,000\nB\n"
        )
        pairs = ops.overlaps(cues)
        self.assertEqual(len(pairs), 1)

    def test_clean_file(self):
        cues = formats.parse_srt(SRT)
        self.assertEqual(ops.overlaps(cues), [])


class DelayParseTests(unittest.TestCase):
    def test_units(self):
        from subtitle_tools.cli import parse_delay
        self.assertEqual(parse_delay("3.5s", None), 3_500_000)
        self.assertEqual(parse_delay("-250ms", None), -250_000)
        self.assertEqual(parse_delay("1m10s", None), 70_000_000)
        self.assertEqual(parse_delay("90f", 25.0), 3_600_000)
        with self.assertRaises(SystemExit):
            parse_delay("90f", None)


if __name__ == "__main__":
    unittest.main()
