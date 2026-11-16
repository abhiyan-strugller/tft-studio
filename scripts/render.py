"""Post card renderer for TempleFront Tours & Travel (1080x1350, 4:5).

Every card is a real photograph from library/ (Pexels License or the agency's
own photos) with type set over it. Templates:

  postcard  full-bleed photo, kicker + title + subtitle on a bottom gradient
  fact      photo under a dark veil, one big true number + what it means
  tour      photo on top, cream panel with the real package: name, days, price, CTA
  tips      dark veiled photo, title + 3-5 short numbered tips
  versus    two photos stacked, "A or B?" — built for comments
  trust     the agency's own photo, review badge + a line about the trip

Usage (normally called by build_day.py):
  python3 scripts/render.py --post '<json>' --out out.png
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
W, H = 1080, 1350
FONTS = ROOT / "assets" / "fonts"

CREAM = (248, 241, 228)
INK = (26, 22, 18)
GOLD = (212, 160, 45)
SAFFRON = (244, 160, 45)
SINDOOR = (200, 40, 26)
WHITE = (252, 250, 246)
MIST = (168, 163, 152)

WHATSAPP = "+977 985-1007885"
SITE = "templefronttours.com"


REPLACE = {"→": "›", "->": "›", "✓": "·"}
_CMAPS: dict = {}


def clean(text: str, kind: str = "sans") -> str:
    """Swap known-missing glyphs, then refuse anything the font cannot draw
    (a missing glyph renders as a tofu box on the live card)."""
    for a, b in REPLACE.items():
        text = text.replace(a, b)
    import re
    text = re.sub(r"(\d) (m|km|ft|days?|nights?|hrs?|hours?)\b", "\\1\u00a0\\2", text)  # keep "3,210 m" together
    fname = font(kind, 10).path
    if fname not in _CMAPS:
        from fontTools.ttLib import TTFont
        _CMAPS[fname] = TTFont(fname).getBestCmap()
    bad = sorted({ch for ch in text if ch not in "\n" and ord(ch) not in _CMAPS[fname]})
    if bad:
        raise ValueError(f"GLYPH MISSING in {kind}: {bad!r} in {text!r} — reword without it")
    return text


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    files = {
        "serif": "DMSerifDisplay-Regular.ttf",
        "serif_i": "DMSerifDisplay-Italic.ttf",
        "sans": "Poppins-Regular.ttf",
        "sans_m": "Poppins-Medium.ttf",
        "sans_sb": "Poppins-SemiBold.ttf",
        "sans_b": "Poppins-Bold.ttf",
    }
    return ImageFont.truetype(str(FONTS / files[name]), size)


# ---------------------------------------------------------------------------
# photo helpers
# ---------------------------------------------------------------------------

def load_library() -> dict:
    lib = json.loads((ROOT / "library" / "library.json").read_text())
    return {p["id"]: p for p in lib}


def photo(pid: str) -> Image.Image:
    lib = load_library()
    if pid not in lib:
        raise SystemExit(f"photo id not in library: {pid}")
    return ImageOps.exif_transpose(Image.open(ROOT / lib[pid]["file"])).convert("RGB")


def cover(img: Image.Image, w: int, h: int, focus_x: float = 0.5, focus_y: float = 0.5) -> Image.Image:
    """Scale to fill w x h, cropping around the focus point (0..1)."""
    s = max(w / img.width, h / img.height)
    nw, nh = int(img.width * s + 0.5), int(img.height * s + 0.5)
    img = img.resize((nw, nh), Image.LANCZOS)
    x = int((nw - w) * focus_x)
    y = int((nh - h) * focus_y)
    return img.crop((x, y, x + w, y + h))


def gradient(w: int, h: int, top_alpha: int, bottom_alpha: int, start: float = 0.0) -> Image.Image:
    """Vertical black gradient as an RGBA layer; transparent above `start`."""
    g = Image.new("L", (1, h))
    for yy in range(h):
        t = yy / max(h - 1, 1)
        if t < start:
            a = top_alpha
        else:
            u = (t - start) / max(1 - start, 1e-6)
            u = u * u * (3 - 2 * u)  # smoothstep
            a = int(top_alpha + (bottom_alpha - top_alpha) * u)
        g.putpixel((0, yy), a)
    g = g.resize((w, h))
    layer = Image.new("RGBA", (w, h), (12, 10, 8, 0))
    layer.putalpha(g)
    return layer


def logo(size: int) -> Image.Image:
    lg = Image.open(ROOT / "assets" / "logo-mark.png").convert("RGBA")
    lg.thumbnail((size, size), Image.LANCZOS)
    return lg


def paste_logo(canvas: Image.Image, x: int, y: int, size: int = 120) -> None:
    lg = logo(int(size * 1.25))
    pad = 14
    plate = Image.new("RGBA", (lg.width + 2 * pad, lg.height + 2 * pad), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plate)
    pd.rounded_rectangle((0, 0, plate.width - 1, plate.height - 1), 22, fill=(252, 250, 246, 235))
    sh = Image.new("RGBA", plate.size, (0, 0, 0, 0))
    sh.putalpha(plate.getchannel("A").point(lambda a: int(a * 0.35)))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), (x + 2, y + 6))
    canvas.alpha_composite(plate, (x, y))
    x, y = x + pad, y + pad
    # soft shadow so the mark reads on bright skies
    sh = Image.new("RGBA", lg.size, (0, 0, 0, 0))
    sh.putalpha(lg.getchannel("A").point(lambda a: int(a * 0.55)))
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    canvas.alpha_composite(sh, (x + 2, y + 4))
    canvas.alpha_composite(lg, (x, y))


# ---------------------------------------------------------------------------
# text helpers
# ---------------------------------------------------------------------------

def wrap(draw: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        words = [w for w in para.split(" ") if w]
        line = ""
        for wd in words:
            test = (line + " " + wd).strip()
            if draw.textlength(test, font=f) <= max_w:
                line = test
            else:
                if line:
                    lines.append(line)
                line = wd
        lines.append(line)
    return lines


def fit(draw, text, kind, max_w, max_lines, sizes) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    """Largest size from `sizes` at which `text` wraps into <= max_lines and no word overflows."""
    text = clean(text, kind)
    for s in sizes:
        f = font(kind, s)
        lines = wrap(draw, text, f, max_w)
        if len(lines) <= max_lines and all(draw.textlength(l, font=f) <= max_w for l in lines):
            # balance: narrow the box while the line count holds, so no lonely last word
            if len(lines) > 1:
                best = lines
                for w in range(max_w - 20, int(max_w * 0.6), -20):
                    trial = wrap(draw, text, f, w)
                    if len(trial) != len(lines):
                        break
                    best = trial
                lines = best
            return f, lines
    raise ValueError(f"TEXT TOO LONG for {max_lines} lines at {sizes[-1]}px: {text!r}")


def text_block(draw, xy, lines, f, fill, leading=1.12, shadow=True, anchor_bottom=False, align="left", box_w=0):
    x, y = xy
    lh = int(f.size * leading)
    total = lh * len(lines)
    if anchor_bottom:
        y -= total
    for i, line in enumerate(lines):
        lx = x
        if align == "center":
            lx = x + (box_w - draw.textlength(line, font=f)) / 2
        if shadow:
            draw.text((lx + 2, y + i * lh + 3), line, font=f, fill=(0, 0, 0, 120))
        draw.text((lx, y + i * lh), line, font=f, fill=fill)
    return y, y + total


def spaced(draw, xy, text, f, fill, tracking=4, shadow=True):
    x, y = xy
    text = clean(text, "sans")
    for ch in text:
        if shadow:
            draw.text((x + 1, y + 2), ch, font=f, fill=(0, 0, 0, 130))
        draw.text((x, y), ch, font=f, fill=fill)
        x += draw.textlength(ch, font=f) + tracking
    return x


def star(draw, cx, cy, r, fill):
    import math
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    draw.polygon(pts, fill=fill)


def footer(draw, y=H - 64, color=WHITE):
    f = font("sans_m", 24)
    t = f"{SITE}   ·   WhatsApp {WHATSAPP}"
    w = draw.textlength(t, font=f)
    draw.text(((W - w) / 2 + 1, y + 2), t, font=f, fill=(0, 0, 0, 110))
    draw.text(((W - w) / 2, y), t, font=f, fill=color)


# ---------------------------------------------------------------------------
# templates
# ---------------------------------------------------------------------------

def t_postcard(p: dict) -> Image.Image:
    c = cover(photo(p["photo"]), W, H, p.get("focus_x", 0.5), p.get("focus_y", 0.5)).convert("RGBA")
    c.alpha_composite(gradient(W, H, 0, 240, start=0.34))
    c.alpha_composite(gradient(W, 260, 110, 0))
    d = ImageDraw.Draw(c)
    paste_logo(c, 52, 46, 128)
    m = 72
    tf, tl = fit(d, p["title"], "serif", W - 2 * m, 3, [118, 106, 96, 88, 80, 72])
    sub_lines, sf = [], None
    if p.get("subtitle"):
        sf, sub_lines = fit(d, p["subtitle"], "sans", W - 2 * m, 3, [38, 35, 32, 30])
    bottom = H - 120
    if sub_lines:
        _, _ = text_block(d, (m, bottom), sub_lines, sf, (235, 230, 220), 1.35, anchor_bottom=True)
        bottom -= int(sf.size * 1.35) * len(sub_lines) + 26
    top, _ = text_block(d, (m, bottom), tl, tf, WHITE, 1.04, anchor_bottom=True)
    if p.get("kicker"):
        kf = font("sans_sb", 27)
        ky = top - 58
        d.rectangle((m, ky + 13, m + 46, ky + 17), fill=SAFFRON)
        spaced(d, (m + 62, ky), p["kicker"].upper(), kf, SAFFRON, 5)
    footer(d)
    return c


def t_fact(p: dict) -> Image.Image:
    c = cover(photo(p["photo"]), W, H, p.get("focus_x", 0.5), p.get("focus_y", 0.5))
    c = c.filter(ImageFilter.GaussianBlur(1.2)).convert("RGBA")
    c.alpha_composite(Image.new("RGBA", (W, H), (12, 10, 8, 120)))
    c.alpha_composite(gradient(W, H, 40, 220, start=0.25))
    d = ImageDraw.Draw(c)
    paste_logo(c, 52, 46, 128)
    m = 80
    kf = font("sans_sb", 28)
    top = 520 if p.get("context") else 600
    spaced(d, (m, top), p.get("kicker", "DID YOU KNOW").upper(), kf, SAFFRON, 5)
    nf, nl = fit(d, p["number"], "serif", W - 2 * m, 1, [250, 220, 196, 172, 150])
    _, y = text_block(d, (m, top + 50), nl, nf, GOLD, 1.0)
    lf, ll = fit(d, p["label"], "serif", W - 2 * m, 2, [70, 62, 56, 50])
    _, y = text_block(d, (m, y + 10), ll, lf, WHITE, 1.08)
    if p.get("context"):
        cf, cl = fit(d, p["context"], "sans", W - 2 * m, 5, [36, 33, 30, 28])
        text_block(d, (m, y + 34), cl, cf, (232, 226, 214), 1.42)
    if p.get("source"):
        sf = font("sans", 22)
        d.text((m, H - 118), "Source: " + p["source"], font=sf, fill=(200, 194, 182))
    footer(d)
    return c


def t_tour(p: dict) -> Image.Image:
    c = Image.new("RGBA", (W, H), CREAM + (255,))
    ph_h = 820
    c.paste(cover(photo(p["photo"]), W, ph_h, p.get("focus_x", 0.5), p.get("focus_y", 0.5)), (0, 0))
    c.alpha_composite(gradient(W, 240, 120, 0))
    paste_logo(c, 52, 46, 128)
    d = ImageDraw.Draw(c)
    # category ribbon on the photo
    if p.get("kicker"):
        kf = font("sans_sb", 26)
        tw = sum(d.textlength(ch, font=kf) + 4 for ch in p["kicker"].upper()) + 40
        d.rounded_rectangle((W - tw - 52, 62, W - 52, 112), 25, fill=SINDOOR)
        spaced(d, (W - tw - 32, 70), p["kicker"].upper(), kf, WHITE, 4, shadow=False)
    m = 72
    y = ph_h + 44
    tf, tl = fit(d, p["title"], "serif", W - 2 * m, 2, [76, 70, 64, 58, 52])
    _, y = text_block(d, (m, y), tl, tf, INK, 1.06, shadow=False)
    if p.get("subtitle"):
        sf, sl = fit(d, p["subtitle"], "sans", W - 2 * m, 2, [32, 30, 28])
        _, y = text_block(d, (m, y + 10), sl, sf, (90, 82, 72), 1.35, shadow=False)
    # chips
    y += 28
    x = m
    cf = font("sans_sb", 28)
    for chip in p.get("chips", [])[:3]:
        tw = d.textlength(chip, font=cf)
        d.rounded_rectangle((x, y, x + tw + 44, y + 58), 29, outline=(46, 77, 140), width=3)
        d.text((x + 22, y + 10), chip, font=cf, fill=(46, 77, 140))
        x += tw + 64
    # CTA bar
    bar_y = H - 150
    d.rectangle((0, bar_y, W, H), fill=INK)
    pf = font("serif", 46)
    price = p.get("price_line", "Private tour · Ask for your price")
    d.text((m, bar_y + 26), price, font=pf, fill=GOLD)
    wf = font("sans_m", 27)
    d.text((m, bar_y + 92), f"WhatsApp {WHATSAPP}   ·   {SITE}", font=wf, fill=CREAM)
    return c


def t_tips(p: dict) -> Image.Image:
    c = cover(photo(p["photo"]), W, H, p.get("focus_x", 0.5), p.get("focus_y", 0.5))
    c = c.filter(ImageFilter.GaussianBlur(2.5)).convert("RGBA")
    c.alpha_composite(Image.new("RGBA", (W, H), (14, 12, 10, 165)))
    tips = p["tips"][:5]
    m = 80
    # lay out on a scratch layer, then centre the block vertically
    layer = Image.new("RGBA", (W, H * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y = 0
    if p.get("kicker"):
        spaced(d, (m, y), p["kicker"].upper(), font("sans_sb", 30), SAFFRON, 5)
        y += 64
    tf, tl = fit(d, p["title"], "serif", W - 2 * m, 3, [96, 88, 80, 72, 64])
    _, y = text_block(d, (m, y), tl, tf, WHITE, 1.06)
    y += 50
    sizes = [42, 40, 38, 36, 34, 32] if len(tips) <= 4 else [40, 38, 36, 34, 32, 30]
    for i, tip in enumerate(tips, 1):
        d.text((m, y - 14), str(i), font=font("serif", 64), fill=GOLD)
        f, lines = fit(d, tip, "sans", W - 2 * m - 80, 3, sizes)
        _, y = text_block(d, (m + 80, y), lines, f, (240, 235, 226), 1.34)
        y += 36
    avail_top, avail_bot = 210, H - 110
    if y > avail_bot - avail_top:
        raise ValueError("TEXT TOO LONG: tips overflow the card")
    top = avail_top + (avail_bot - avail_top - y) // 2
    c.alpha_composite(layer.crop((0, 0, W, H - top)), (0, top))
    paste_logo(c, 52, 46, 120)
    footer(ImageDraw.Draw(c))
    return c


def t_versus(p: dict) -> Image.Image:
    c = Image.new("RGBA", (W, H), INK + (255,))
    half = (H - 8) // 2
    a, b = p["photos"][:2]
    c.paste(cover(photo(a), W, half, 0.5, p.get("focus_a", 0.5)), (0, 0))
    c.paste(cover(photo(b), W, half, 0.5, p.get("focus_b", 0.5)), (0, half + 8))
    c.alpha_composite(gradient(W, half, 0, 190, start=0.45), (0, 0))
    c.alpha_composite(gradient(W, half, 0, 190, start=0.45), (0, half + 8))
    d = ImageDraw.Draw(c)
    paste_logo(c, 44, 36, 104)
    lf = font("serif", 66)
    for i, label in enumerate(p["labels"][:2]):
        y0 = (half - 150) if i == 0 else (H - 104)
        tag = "A" if i == 0 else "B"
        d.ellipse((60, y0 - 4, 132, y0 + 68), fill=SINDOOR)
        d.text((96, y0 + 32), tag, font=font("sans_b", 40), fill=WHITE, anchor="mm")
        f, ln = fit(d, label, "serif", W - 230, 1, [66, 58, 50, 44])
        text_block(d, (156, y0 - 2), ln, f, WHITE, 1.0)
    # center question pill
    q = p.get("question", "Which one would you choose?")
    qf = font("sans_sb", 32)
    qw = d.textlength(q, font=qf)
    cy = half + 4
    d.rounded_rectangle(((W - qw) / 2 - 34, cy - 36, (W + qw) / 2 + 34, cy + 36), 36, fill=CREAM)
    d.text((W / 2, cy), q, font=qf, fill=INK, anchor="mm")
    return c


def t_trust(p: dict) -> Image.Image:
    c = cover(photo(p["photo"]), W, H, p.get("focus_x", 0.5), p.get("focus_y", 0.5)).convert("RGBA")
    c.alpha_composite(gradient(W, H, 0, 230, start=0.5))
    d = ImageDraw.Draw(c)
    paste_logo(c, 52, 46, 128)
    m = 72
    # review badge (the number comes from the site: 19 Google reviews, 5.0)
    bf = font("sans_sb", 30)
    badge = p.get("badge", "5.0 on Google · 19 reviews")
    bw = d.textlength(badge, font=bf)
    x0 = W - bw - 130
    d.rounded_rectangle((x0, 58, W - 52, 118), 30, fill=CREAM)
    star(d, x0 + 40, 88, 17, GOLD)
    d.text((x0 + 66, 68), badge, font=bf, fill=INK)
    tf, tl = fit(d, p["title"], "serif_i", W - 2 * m, 3, [80, 72, 66, 60, 54])
    bottom = H - 120
    if p.get("subtitle"):
        sf, sl = fit(d, p["subtitle"], "sans", W - 2 * m, 2, [34, 31, 29])
        text_block(d, (m, bottom), sl, sf, (235, 230, 220), 1.35, anchor_bottom=True)
        bottom -= int(sf.size * 1.35) * len(sl) + 24
    text_block(d, (m, bottom), tl, tf, WHITE, 1.08, anchor_bottom=True)
    footer(d)
    return c


TEMPLATES = {
    "postcard": t_postcard,
    "fact": t_fact,
    "tour": t_tour,
    "tips": t_tips,
    "versus": t_versus,
    "trust": t_trust,
}


def render(p: dict, out: str | os.PathLike) -> None:
    tpl = p.get("template")
    if tpl not in TEMPLATES:
        raise SystemExit(f"unknown template {tpl!r}; use one of {sorted(TEMPLATES)}")
    img = TEMPLATES[tpl](p).convert("RGB")
    assert img.size == (W, H)
    img.save(out, "PNG", optimize=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--post", required=True, help="post JSON")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    render(json.loads(a.post), a.out)
    print(a.out)
