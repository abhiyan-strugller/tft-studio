"""Reel renderer — 1080x1920, 30 fps, 15-40 s.

Each slide is a library photo with a slow Ken Burns move, an animated caption,
and a soft cross-fade into the next slide. Audio is generated in-repo by
gen_audio.py (drone + singing-bowl strikes on every cut), so there is never a
music-copyright claim.

  python3 scripts/render_reel.py --input input/reels/<slug>.json [--out output/reels/<slug>.mp4]

Reel doc:
{
  "slug": "2026-11-17-muktinath-108",
  "seed": 4,                                # optional: audio variation
  "slides": [
    {"photo": "muktinath", "kicker": "Mustang, Nepal", "text": "108 sacred water spouts", "sub": "...", "seconds": 3.5,
     "focus_x": 0.5, "focus_y": 0.5, "move": "in"|"out"|"left"|"right"},
    ...
    {"end": true, "text": "Plan your yatra with us", "sub": "WhatsApp +977 985-1007885", "photo": "...", "seconds": 4}
  ]
}
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render as R  # noqa: E402

ROOT = R.ROOT
W, H, FPS = 1080, 1920, 30
XF = 0.45  # cross-fade seconds
PAD = 1.14  # how much bigger than the frame the photo is prepared, for movement


def overlay(slide: dict, idx: int, n: int) -> Image.Image:
    """Transparent text layer for one slide."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    m = 84
    end = slide.get("end", False)
    if end:
        # centred brand close
        lg = R.logo(300)
        plate = Image.new("RGBA", (lg.width + 48, lg.height + 48), (0, 0, 0, 0))
        ImageDraw.Draw(plate).rounded_rectangle((0, 0, plate.width - 1, plate.height - 1), 36,
                                                fill=(252, 250, 246, 240))
        plate.alpha_composite(lg, (24, 24))
        layer.alpha_composite(plate, ((W - plate.width) // 2, 560))
        tf, tl = R.fit(d, slide["text"], "serif", W - 2 * m, 3, [96, 86, 78, 70])
        _, y = R.text_block(d, (m, 560 + plate.height + 70), tl, tf, R.WHITE, 1.08, align="center", box_w=W - 2 * m)
        if slide.get("sub"):
            sf, sl = R.fit(d, slide["sub"], "sans_m", W - 2 * m, 3, [44, 40, 36])
            R.text_block(d, (m, y + 30), sl, sf, R.GOLD, 1.4, align="center", box_w=W - 2 * m)
        return layer
    # regular beat: kicker + big text in lower third
    tf, tl = R.fit(d, slide["text"], "serif", W - 2 * m, 4, [104, 94, 86, 78, 70, 64])
    bottom = H - 360
    if slide.get("sub"):
        sf, sl = R.fit(d, slide["sub"], "sans", W - 2 * m, 4, [44, 40, 37, 34])
        R.text_block(d, (m, bottom), sl, sf, (238, 233, 224), 1.38, anchor_bottom=True)
        bottom -= int(sf.size * 1.38) * len(sl) + 30
    top, _ = R.text_block(d, (m, bottom), tl, tf, R.WHITE, 1.05, anchor_bottom=True)
    if slide.get("kicker"):
        kf = R.font("sans_sb", 34)
        ky = top - 70
        d.rectangle((m, ky + 17, m + 54, ky + 22), fill=R.SAFFRON)
        R.spaced(d, (m + 72, ky), slide["kicker"].upper(), kf, R.SAFFRON, 6)
    if idx == 0:
        pass
    return layer


def prepared_photo(slide: dict) -> Image.Image:
    img = R.photo(slide["photo"])
    pw, ph = int(W * PAD), int(H * PAD)
    return R.cover(img, pw, ph, slide.get("focus_x", 0.5), slide.get("focus_y", 0.5))


def base_frame(prep: Image.Image, t: float, move: str) -> Image.Image:
    """Ken Burns: t in 0..1 across the slide."""
    u = t * t * (3 - 2 * t)
    pw, ph = prep.size
    if move in ("in", "out"):
        z = 1 + (PAD - 1) * (u if move == "in" else 1 - u)  # 1 = widest
        cw, ch = pw / z, ph / z
        x, y = (pw - cw) / 2, (ph - ch) / 2
    else:
        cw, ch = W * 1.04, H * 1.04
        span = pw - cw
        x = span * (u if move == "right" else 1 - u)
        y = (ph - ch) / 2
    return prep.resize((W, H), Image.BILINEAR, box=(x, y, x + cw, y + ch))


SCRIM = None


def scrim() -> Image.Image:
    global SCRIM
    if SCRIM is None:
        s = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        s.alpha_composite(R.gradient(W, H, 0, 225, start=0.40))
        s.alpha_composite(R.gradient(W, 360, 100, 0))
        SCRIM = s
    return SCRIM


def render_reel(doc: dict, out: Path) -> float:
    slides = doc["slides"]
    n = len(slides)
    durs = [float(s.get("seconds", 3.5)) for s in slides]
    total = sum(durs)
    if not 12 <= total <= 45:
        raise SystemExit(f"reel length {total:.1f}s outside 12-45s")
    moves = ["in", "right", "out", "left"]
    preps, overs = [], []
    for i, s in enumerate(slides):
        preps.append(prepared_photo(s))
        overs.append(overlay(s, i, n))
    starts = np.cumsum([0] + durs[:-1])
    cuts = [float(x) for x in starts[1:]]
    out.parent.mkdir(parents=True, exist_ok=True)
    wav = out.with_suffix(".wav")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "gen_audio.py"), "--seconds", f"{total:.2f}",
                    "--out", str(wav), "--seed", str(doc.get("seed", 1)),
                    "--cuts", ",".join(f"{c:.2f}" for c in cuts)], check=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", str(wav), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(out)]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    sc = scrim()
    nframes = int(round(total * FPS))

    def slide_img(i: int, gt: float) -> Image.Image:
        lt = (gt - starts[i]) / durs[i]
        lt = min(max(lt, 0.0), 1.0)
        mv = slides[i].get("move", moves[i % 4])
        fr = base_frame(preps[i], lt, mv).convert("RGBA")
        if slides[i].get("end"):
            fr = fr.filter(ImageFilter.GaussianBlur(6))
            fr.alpha_composite(Image.new("RGBA", (W, H), (14, 12, 10, 170)))
        else:
            fr.alpha_composite(sc)
        # caption: fade + rise over first 0.5 s of the slide
        local = gt - starts[i]
        a = min(max((local - 0.15) / 0.5, 0.0), 1.0)
        a = a * a * (3 - 2 * a)
        if a > 0:
            ov = overs[i]
            if a < 1:
                al = ov.getchannel("A").point(lambda v, a=a: int(v * a))
                ov = ov.copy()
                ov.putalpha(al)
            dy = int((1 - a) * 40)
            fr.alpha_composite(ov, (0, dy))
        return fr

    for k in range(nframes):
        gt = k / FPS
        i = int(np.searchsorted(starts, gt, side="right") - 1)
        i = min(max(i, 0), n - 1)
        fr = slide_img(i, gt)
        # cross-fade into the next slide during the last XF seconds
        if i < n - 1:
            rem = starts[i] + durs[i] - gt
            if rem < XF:
                nxt = slide_img(i + 1, starts[i + 1] + 0.001)
                fr = Image.blend(fr, nxt, 1 - rem / XF)
        # progress bar
        d = ImageDraw.Draw(fr)
        d.rectangle((0, 0, int(W * gt / total), 7), fill=R.SAFFRON)
        ff.stdin.write(fr.convert("RGB").tobytes())
    ff.stdin.close()
    if ff.wait() != 0:
        raise SystemExit("ffmpeg failed")
    wav.unlink(missing_ok=True)
    verify(out)
    return total


def verify(mp4: Path) -> None:
    """Video and audio stream durations must agree within 0.5 s; total 12-45 s."""
    def dur(sel):
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", sel, "-show_entries",
                            "stream=duration", "-of", "csv=p=0", str(mp4)], capture_output=True, text=True)
        return float(r.stdout.strip().splitlines()[0])
    v, a = dur("v:0"), dur("a:0")
    if abs(v - a) > 0.5 or not 12 <= v <= 45:
        raise SystemExit(f"BROKEN REEL {mp4}: video {v:.2f}s audio {a:.2f}s")
    print(f"reel ok: {mp4} ({v:.1f}s video / {a:.1f}s audio)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    doc = json.loads(Path(a.input).read_text())
    out = Path(a.out) if a.out else ROOT / "output" / "reels" / f"{doc['slug']}.mp4"
    render_reel(doc, out)
