#!/usr/bin/env python3
"""Build the small font subsets that build_assets.py turns into SVG outlines.

Run once (or whenever new Japanese text is added) against the full OFL fonts
from github.com/google/fonts:

    python3 scripts/make_fonts.py /path/to/google-fonts-download

Expected layout of the source dir:
    instrumentserif/InstrumentSerif-Regular.ttf
    instrumentserif/InstrumentSerif-Italic.ttf
    manrope/Manrope[wght].ttf
    ibmplexmono/IBMPlexMono-Regular.ttf
    ibmplexmono/IBMPlexMono-Medium.ttf
    notoserifjp/NotoSerifJP[wght].ttf
"""

from __future__ import annotations

import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_assets import JP_TEXT  # noqa: E402

OUT = Path(__file__).resolve().parent / "fonts"
LATIN = ("".join(chr(c) for c in range(0x20, 0x7F)) + "·—–’“”…↗→←↓×♡é«»№°"
         + "".join(chr(c) for c in range(0x400, 0x460)))  # Cyrillic

FONTS = [
    # (output name, source, variable-axis instance or None)
    ("display.ttf", "instrumentserif/InstrumentSerif-Regular.ttf", None),
    ("display-italic.ttf", "instrumentserif/InstrumentSerif-Italic.ttf", None),
    ("sans.ttf", "manrope/Manrope[wght].ttf", {"wght": 450}),
    ("sans-medium.ttf", "manrope/Manrope[wght].ttf", {"wght": 600}),
    ("mono.ttf", "ibmplexmono/IBMPlexMono-Regular.ttf", None),
    ("mono-medium.ttf", "ibmplexmono/IBMPlexMono-Medium.ttf", None),
    ("jp.ttf", "notoserifjp/NotoSerifJP[wght].ttf", {"wght": 450}),
]


def main(src: Path) -> None:
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.ttf"):
        old.unlink()
    chars = LATIN + JP_TEXT
    for name, rel, axes in FONTS:
        tt = TTFont(src / rel)
        if axes:
            tt = instantiateVariableFont(tt, axes)
        opts = subset.Options()
        opts.layout_features = ["*"]
        opts.name_IDs = ["*"]
        opts.notdef_outline = True
        sub = subset.Subsetter(opts)
        sub.populate(text=chars)
        sub.subset(tt)
        tt.save(OUT / name)
        print(f"  {name}: {(OUT / name).stat().st_size // 1024} KB")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
