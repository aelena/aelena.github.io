"""Generate og.png — the 1200x630 social card for aelena.com.

Built to the spec in DESIGN.md section 7: "Antonio Elena" in serif and the
tagline in mono. Follows section 4.1 (Cormorant Garamond 300, IBM Plex Mono 300,
letter-spaced) and section 4.2 (warm cream, near-black, mid grey; monochrome, no
accent colour). Section 4.3 says no chrome, so there is no frame or rule.

The two webfonts the site loads are not usually installed locally, so they are
fetched once from the Google Fonts repository into tools/.fonts/ (git-ignored).

    python tools/make-og-image.py
"""
import os
import urllib.request
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
BG, INK, MUTED = "#fafaf8", "#1a1a1a", "#888888"

NAME = "Antonio Elena"
TAGLINE = "ai · architecture · cloud · software · writing"
DOMAIN = "aelena.com"

FONTS = {
    "CormorantGaramond[wght].ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/"
        "cormorantgaramond/CormorantGaramond%5Bwght%5D.ttf",
    "IBMPlexMono-Regular.ttf":
        "https://raw.githubusercontent.com/google/fonts/main/ofl/"
        "ibmplexmono/IBMPlexMono-Regular.ttf",
}
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".fonts")


def font_path(name):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, name)
    if not os.path.exists(p):
        print(f"fetching {name}")
        urllib.request.urlretrieve(FONTS[name], p)
    return p


def load(name, size, weight=None):
    f = ImageFont.truetype(font_path(name), size)
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])  # Cormorant is a variable font
        except Exception:
            pass  # static instance; the default weight is close enough
    return f


def tracked(draw, xy, text, font, fill, tracking):
    """PIL has no letter-spacing, and DESIGN.md 4.1 asks for a spaced mono."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking
    return x


def tracked_width(draw, text, font, tracking):
    return sum(draw.textlength(c, font=font) for c in text) + tracking * (len(text) - 1)


img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

serif = load("CormorantGaramond[wght].ttf", 132, weight=300)
mono = load("IBMPlexMono-Regular.ttf", 27)
mono_sm = load("IBMPlexMono-Regular.ttf", 22)

# Centred, per DESIGN.md 4.3. The block is optically centred as a whole rather
# than each line independently.
name_w = d.textlength(NAME, font=serif)
tag_w = tracked_width(d, TAGLINE, mono, 2.4)
dom_w = tracked_width(d, DOMAIN, mono_sm, 1.6)

top = 214
d.text(((W - name_w) / 2, top), NAME, font=serif, fill=INK)
tracked(d, ((W - tag_w) / 2, top + 196), TAGLINE, mono, MUTED, 2.4)
tracked(d, ((W - dom_w) / 2, top + 262), DOMAIN, mono_sm, MUTED, 1.6)

out = "og.png"
img.save(out, "PNG", optimize=True)
print(f"{out}  {W}x{H}  {os.path.getsize(out) / 1024:.0f} KB")
