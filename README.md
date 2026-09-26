# subtitle-tools

**SRT/VTT toolkit in pure Python — shift, fps conversion, dual-language merge, overlap detection. Zero dependencies.**

[![CI](https://github.com/efealtiparmakoglu/subtitle-tools/actions/workflows/ci.yml/badge.svg)](https://github.com/efealtiparmakoglu/subtitle-tools/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org)

```
$ subtitle-tools shift movie.srt --delay 2.5s
1
00:00:03,500 --> 00:00:06,500
Merhaba dunya.
...

$ subtitle-tools fps movie.srt --from-fps 23.976 --to-fps 25
1
00:00:00,959 --> 00:00:03,836
```

Written for subtitle fans who translate and sync their own files: the
fixes you do a hundred times, without a GUI.

## Why subtitle-tools

- **Shift with units.** `--delay 2.5s`, `-250ms`, `1m10s` or `90f`
  (frames, with `--fps`); negative moves earlier, zero-clamped.
- **FPS conversion.** Subs timed for 23.976 fps on a 25 fps release:
  every timestamp rescales by the exact ratio.
- **Dual-language merge.** Two tracks (e.g. TR + EN) become one file;
  overlapping cues share the screen as two lines.
- **Format conversion.** SRT ↔ VTT both directions, incl. VTT cue
  identifiers and SRT index lines.
- **Overlap detection.** `check` lists colliding cues; exit code 1
  makes it CI-friendly.

## Usage

```sh
subtitle-tools shift movie.srt --delay -1.2s -o fixed.srt
subtitle-tools fps movie.srt --from-fps 23.976 --to-fps 25 -o converted.srt
subtitle-tools merge tr.srt en.srt -o dual.srt --to srt
subtitle-tools check movie.srt --json
subtitle-tools convert movie.srt --to vtt      # SRT -> VTT on stdout
```

Exit codes: 0 ok, 1 overlaps found (check), 2 usage error.

## Known limitations

- Formatting tags (`<i>`, `<b>`) are preserved as plain text — no tag
  rewriting during merges.
- Frame-based input (`90f`) requires `--fps`.

## Development

```sh
python3 -m unittest discover -s tests
```

18 tests cover the timestamp parser (SRT/VTT/frame/short forms), SRT
and VTT round trips, shifts with clamping, fps conversion ratios,
dual-language merges with overlap folding, overlap detection and the
delay-unit parser.

## License

MIT — see [LICENSE](LICENSE).
