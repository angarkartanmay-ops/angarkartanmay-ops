"""Fetch pinned Geist fonts from npm (@fontsource), subset to the glyphs the SVGs use,
and write base64 text files to scripts/fonts/. Needs node/npm, fonttools and brotli."""
import base64, pathlib, subprocess, sys, tempfile, tarfile
from fontTools import subset

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "scripts" / "fonts"
VERSION = "5.3.0"
WANT = {  # output name -> (package, source file)
    "geist-400": ("geist", "geist-latin-400-normal.woff2"),
    "geist-600": ("geist", "geist-latin-600-normal.woff2"),
    "geist-mono-400": ("geist-mono", "geist-mono-latin-400-normal.woff2"),
    "geist-mono-500": ("geist-mono", "geist-mono-latin-500-normal.woff2"),
}
UNICODES = list(range(0x20, 0x7F)) + [0xB7, 0x2014, 0x2192]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        for pkg in sorted({p for p, _ in WANT.values()}):
            subprocess.run(["npm", "pack", f"@fontsource/{pkg}@{VERSION}"], cwd=tmp, check=True,
                           stdout=subprocess.DEVNULL)
            with tarfile.open(next(tmp.glob(f"fontsource-{pkg}-*.tgz"))) as t:
                t.extractall(tmp / pkg)
        for name, (pkg, src) in WANT.items():
            opts = subset.Options()
            opts.flavor = "woff2"
            opts.layout_features = ["kern", "liga", "calt"]
            font = subset.load_font(str(tmp / pkg / "package" / "files" / src), opts)
            sub = subset.Subsetter(opts)
            sub.populate(unicodes=UNICODES)
            sub.subset(font)
            dst = tmp / f"{name}.woff2"
            subset.save_font(font, str(dst), opts)
            (OUT / f"{name}.b64").write_text(base64.b64encode(dst.read_bytes()).decode())
            print(name, dst.stat().st_size, "bytes")


if __name__ == "__main__":
    sys.exit(main())
