"""fonts-src/ 의 Pretendard OTF 를 화면에 쓰는 글자만 남긴 woff2 로 줄인다.
글자: KS X 1001 한글 2,350자 + 영문·숫자·문장부호 + index.html·kit.js 에 쓰인 모든 글자.
실행: uv run --no-project --with fonttools --with brotli python scripts/subset_fonts.py
"""
from pathlib import Path
from fontTools import subset

ROOT = Path(__file__).resolve().parent.parent
chars = set(chr(c) for c in range(0x20, 0x7F))
for hi in range(0xB0, 0xC9):
    for lo in range(0xA1, 0xFF):
        try:
            chars.add(bytes([hi, lo]).decode("euc-kr"))
        except UnicodeDecodeError:
            pass
for f in ["index.html", "assets/kit.js"]:
    chars |= set((ROOT / f).read_text(encoding="utf-8"))
chars |= set("·—–…‘’“”•→←↗①②③④⑤⑥⑦⑧⑨⑩※○●□■△▲▶▷★☆✓✔")
text = "".join(sorted(c for c in chars if c.isprintable()))
out = ROOT / "assets" / "fonts"
out.mkdir(exist_ok=True)
for src in sorted((ROOT / "fonts-src").glob("*.otf")):
    opts = subset.Options(); opts.flavor = "woff2"; opts.layout_features = ["*"]
    font = subset.load_font(str(src), opts)
    s = subset.Subsetter(opts); s.populate(text=text); s.subset(font)
    dst = out / (src.stem + ".woff2")
    subset.save_font(font, str(dst), opts)
    print(dst.name, dst.stat().st_size // 1024, "KB")
