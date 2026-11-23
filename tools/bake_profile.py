"""The profile README's art, in the Supermo design system (The Thing's Arcade edition).

GitHub's Markdown can't load fonts or CSS, so the look lives in SVGs: Ink ground, Bone type,
Signal for the things that matter. Type is set in the brand's own faces (Jersey 10 hooks and
numbers, Silkscreen labels, Pixelify Sans voice, Anton for the MO — FAKHRII wordmark), turned into
outlines so every viewer sees them without the fonts. Super Mo is the real cast art from
The Thing: HQ, drawn at whole pixels per art pixel; the bug is Bug Run's crawler.

Motion is CSS inside the SVG (GitHub plays it in <img>), stepped like the site, and stops for
anyone with reduced motion. Every letter is visible in its base style, so a frozen frame is whole.

  ../.venv/bin/python tools/bake_profile.py    (needs fontTools)

Reads fonts, tokens and Mo from ../the-thing-hq. Writes art/*.svg.
"""
import json
import random
import re
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
HQ = ROOT.parent / "the-thing-hq"
MOD = HQ / "herdr/mods/the-thing-hq"
OUT = ROOT / "art"

TOK = {t["name"]: t["value"] for t in json.load(open(HQ / "assets/tokens.json"))["color"]["tokens"]
       if isinstance(t["value"], str) and t["value"].startswith("#")}
INK, COAL, INK2, ASH_D, ASH, BONE, SIGNAL = (TOK[k] for k in ("ink", "coal", "ink-2", "ash-dark", "ash", "bone", "signal"))

FONTS = {
    "arcade": MOD / "fonts/Jersey10-Regular.ttf",
    "mono": MOD / "fonts/Silkscreen-Regular.ttf",
    "monob": MOD / "fonts/Silkscreen-Bold.ttf",
    "pixel": MOD / "fonts/PixelifySans-Variable.ttf",
    "anton": MOD / "fonts/Anton-Regular.ttf",
}
_fonts = {}


def _font(face):
    if face not in _fonts:
        f = TTFont(FONTS[face])
        _fonts[face] = (f.getGlyphSet(), f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm)
    return _fonts[face]


def glyphs(s, face, size, x, y, tracking=0.0):
    """One outline per character, baseline at (x, y): ([(d, x)], width)."""
    gs, cmap, hmtx, upm = _font(face)
    k = size / upm
    out, cx = [], 0.0
    for ch in s:
        g = cmap.get(ord(ch)) or cmap.get(ord("?"))
        pen = SVGPathPen(gs)
        gs[g].draw(TransformPen(pen, (k, 0, 0, -k, x + cx, y)))
        out.append((pen.getCommands(), x + cx))
        cx += hmtx[g][0] * k + tracking * size
    return out, (cx - tracking * size if s else 0)


def text(s, face, size, x, y, fill, tracking=0.0):
    gl, w = glyphs(s, face, size, x, y, tracking)
    return f'<path fill="{fill}" d="{"".join(d for d, _ in gl)}"/>', w


def width(s, face, size, tracking=0.0):
    return glyphs(s, face, size, 0, 0, tracking)[1]


def mo(pose, x, y, unit, cls=""):
    """Super Mo's real sprite (24 x 32 art px), top left at (x, y), `unit` px per art px."""
    src = (MOD / f"art/cast/mo/{pose}.svg").read_text()
    inner = re.search(r"<svg[^>]*>(.*)</svg>", src, re.S).group(1)
    c = f' class="{cls}"' if cls else ""
    return f'<g{c} transform="translate({x} {y}) scale({unit})" shape-rendering="crispEdges">{inner}</g>'


# Bug Run's crawler (RunnerArt.tsx BugSprite), 30 x 24 art px, facing left.
BUG = "M4 4h2v4H4ZM10 2h2v6h-2ZM2 8h10V6h12v2h4v4h2v8H8v-2H2ZM10 20h4v4h-4ZM18 20h4v4h-4ZM26 20h4v4h-4Z"
BUG_EYES = "M4 10h4v4H4ZM16 10h4v4h-4ZM24 14h4v4h-4ZM12 16h4v2h-4Z"


def bug(x, y, unit, body=BONE, eyes=INK):
    return (f'<g transform="translate({x} {y}) scale({unit})" shape-rendering="crispEdges">'
            f'<path fill="{body}" d="{BUG}"/><path fill="{eyes}" d="{BUG_EYES}"/></g>')


def bubble(s, x, y, tail="right"):
    """A Quip: square Bone bubble, Ink outline, Pixelify text, stepped tail toward the speaker."""
    size, pad, b = 26, 16, 4
    w = width(s, "pixel", size) + pad * 2
    h = size + pad * 2 - 2
    t, _ = text(s, "pixel", size, x + pad, y + pad + size * 0.78, INK)
    tx = x + w - 28 if tail == "right" else x + 16
    steps = "".join(
        f'<rect x="{tx + (i * 4 if tail == "right" else -i * 4)}" y="{y + h + i * 4}" width="{12 - i * 4}" height="4" fill="{BONE}"/>'
        for i in range(3))
    return (f'<rect x="{x - b}" y="{y - b}" width="{w + 2 * b}" height="{h + 2 * b}" fill="{INK}"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{BONE}"/>{steps}{t}'), w


def ground(W, H, seed, dust=26, clear=None):
    """Ink with a Coal haze, pixel dust, scanlines and a vignette (the HQ README's ground)."""
    rnd = random.Random(seed)
    pts = []
    while len(pts) < dust:
        x, y = rnd.randrange(8, W - 8) // 4 * 4, rnd.randrange(8, H - 8) // 4 * 4
        if clear and any(a <= x <= c and b <= y <= d for a, b, c, d in clear):
            continue
        pts.append((x, y, rnd.choice((4, 4, 4, 8)), rnd.choice((ASH_D, ASH_D, ASH))))
    d = "".join(f'<rect x="{x}" y="{y}" width="{s}" height="{s}" fill="{c}"/>' for x, y, s, c in pts)
    return f"""<defs>
  <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="{INK}" opacity=".14"/></pattern>
  <radialGradient id="haze" cx="50%" cy="40%" r="75%"><stop offset="0" stop-color="{COAL}"/><stop offset="1" stop-color="{INK}"/></radialGradient>
  <radialGradient id="vig" cx="50%" cy="50%" r="72%"><stop offset=".6" stop-color="{INK}" stop-opacity="0"/><stop offset="1" stop-color="{INK}" stop-opacity=".7"/></radialGradient>
</defs>
<rect width="{W}" height="{H}" fill="url(#haze)"/>
<g shape-rendering="crispEdges">{d}</g>"""


def finish(W, H):
    return (f'<rect width="{W}" height="{H}" fill="url(#scan)" pointer-events="none"/>'
            f'<rect width="{W}" height="{H}" fill="url(#vig)" pointer-events="none"/>'
            f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" fill="none" stroke="{ASH_D}" stroke-width="2"/>')


def glow(cx, cy, r):
    """The Signal glow behind Mo: three flat rings, no gradient."""
    return "".join(f'<circle cx="{cx}" cy="{cy}" r="{r * k}" fill="{SIGNAL}" opacity="{o}"/>'
                   for k, o in ((1, .06), (.74, .08), (.5, .11)))


def rule(x, y, w, fill=ASH_D, h=2):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" shape-rendering="crispEdges"/>'


def svg(W, H, body, label, style=""):
    st = f"<style>{style}@media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}</style>" if style else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'role="img" aria-label="{label}"><title>{label}</title>{st}{body}</svg>\n')


def wordmark(x, y, size):
    """MO — FAKHRII in Anton, the dash in Signal."""
    a, aw = text("MO", "anton", size, x, y, BONE, .02)
    gap = size * .32
    dash_w = size * .7
    dash = f'<rect x="{x + aw + gap}" y="{y - size * .42}" width="{dash_w}" height="{max(3, size * .09)}" fill="{SIGNAL}"/>'
    b, bw = text("FAKHRII", "anton", size, x + aw + gap * 2 + dash_w, y, BONE, .02)
    return a + dash + b, aw + gap * 2 + dash_w + bw


# ------------------------------------------------------------------ the hero
def hero():
    W, H = 1280, 680
    M = 64
    b = [ground(W, H, 3, 36, [(0, 0, 760, H), (760, 380, W, H)])]

    # eyebrow
    b.append(f'<rect x="{M}" y="{M + 6}" width="16" height="16" fill="{SIGNAL}"/>')
    e, _ = text("PLAYER 1 · SOLUTIONS ARCHITECT + DEVOPS", "mono", 20, M + 30, M + 22, BONE, .04)
    b.append(e)

    # the hook, typed on a CRT: each letter steps in, the caret settles and blinks
    css = []
    i = 0
    for line, y in (("MUSTAFA", M + 176), ("OMAR", M + 308)):
        gl, w = glyphs(line, "arcade", 160, M - 6, y)
        for d, _ in gl:
            b.append(f'<path class="k" style="animation-delay:{0.5 + i * 0.12:.2f}s" fill="{BONE}" d="{d}"/>')
            i += 1
        last_w = w
    stop, sw = glyphs(".", "arcade", 160, M - 6 + last_w + 2, M + 308)
    b.append(f'<path class="k" style="animation-delay:{0.5 + i * 0.12:.2f}s" fill="{SIGNAL}" d="{stop[0][0]}"/>')
    cx = M - 6 + last_w + 2 + sw + 14
    b.append(f'<rect class="caret" x="{cx}" y="{M + 214}" width="30" height="94" fill="{SIGNAL}"/>')
    css.append(".k{animation:type .1s steps(1) backwards}"
               "@keyframes type{from{opacity:0}}"
               f".caret{{animation:blink 1.1s steps(1) {0.5 + (i + 1) * 0.12:.2f}s infinite}}"
               "@keyframes blink{50%{opacity:0}}")

    # the voice
    v1, _ = text("I build real systems for work,", "pixel", 32, M, M + 378, BONE)
    v2, _ = text("and strange little things for fun.", "pixel", 32, M, M + 420, ASH)
    b += [v1, v2]

    # the wordmark and the proof
    wm, _ = wordmark(M, H - 96, 40)
    b.append(wm)
    p, _ = text("THE-THING.DEV  ·  MUSTAFA-OMAR.COM", "mono", 16, M, H - 44, ASH, .04)
    b.append(p)

    # Bug Run, on auto-play: Mo walks, a bug crawls in, Mo hops it, forever
    u = 7
    floor = H - 128
    mx, my = 900, floor - 32 * u
    b.append(glow(mx + 12 * u, my + 18 * u, 200))
    b.append(rule(800, floor, W - 800 - M + 10, ASH_D, 4))
    # floor bits scroll left so the world moves under him
    bits = "".join(rule(k * 48, 14, 16, ASH_D, 4) for k in range(12))
    b.append(f'<svg x="800" y="{floor}" width="{W - 800 - M + 10}" height="30" overflow="hidden">'
             f'<g class="ground">{bits}</g></svg>')
    b.append(f'<g class="hop">'
             f'<g class="f0">{mo("walk-0", mx, my, u)}</g><g class="f1">{mo("walk-1", mx, my, u)}</g></g>')
    bu = 3
    by = floor - 24 * bu
    b.append(f'<svg x="800" y="{by - 10}" width="{W - 800 - M + 10}" height="{24 * bu + 10}" overflow="hidden">'
             f'<g class="crawl">{bug(300, 10, bu)}</g></svg>')
    css.append(
        ".f0{animation:walk0 .5s steps(1) infinite}.f1{opacity:0;animation:walk1 .5s steps(1) infinite}"
        "@keyframes walk0{50%{opacity:0}}@keyframes walk1{50%{opacity:1}}"
        ".crawl{animation:crawl 2.4s linear infinite}"
        f"@keyframes crawl{{from{{transform:translateX({W - 800 - M + 10 - 300}px)}}to{{transform:translateX(-{300 + 30 * bu}px)}}}}"
        ".hop{animation:hop 2.4s steps(3) infinite}"
        "@keyframes hop{0%,32%{transform:translateY(0)}42%{transform:translateY(-96px)}55%{transform:translateY(-112px)}68%{transform:translateY(-96px)}78%,100%{transform:translateY(0)}}"
        ".ground{animation:scroll .4s linear infinite}@keyframes scroll{to{transform:translateX(-48px)}}")
    tag, tw = text("SUPER MO · BUG RUN · AUTO-PLAY", "mono", 14, 0, 0, ASH, .04)
    t2, _ = text("SUPER MO · BUG RUN · AUTO-PLAY", "mono", 14, W - M - tw, floor + 56, ASH, .04)
    b.append(t2)

    b.append(finish(W, H))
    return svg(W, H, "".join(b),
               "Mustafa Omar. Solutions architect and DevOps engineer. I build real systems for work, and strange little things for fun. Super Mo hops a bug.",
               "".join(css))


# ------------------------------------------------------------------ section headers
SECTIONS = [
    ("01", "now", "NOW PLAYING", "Systems at work.", "The Thing after hours.", "hardHat-0", "On it."),
    ("02", "cartridges", "CARTRIDGES", "Things I made.", "Plug one in.", "point-0", "Pick one."),
    ("03", "inventory", "INVENTORY", "The tools I reach for,", "slot by slot.", "giggle-0", "Ctrl+S."),
    ("04", "link-cable", "LINK CABLE", "Say hi.", "I read everything.", "wave-1", "You rang?"),
]


def header(n, label, v1, v2, pose, quip, seed):
    W, H = 1280, 220
    M = 64
    b = [ground(W, H, seed, 14, [(0, 0, 940, H)])]
    num, nw = text(n, "arcade", 116, M - 2, 124, SIGNAL)
    b.append(num)
    rx = M + nw + 22
    b.append(rule(rx, 84, 72, ASH_D, 4))
    lab, _ = text(label, "mono", 26, rx + 92, 98, BONE, .04)
    b.append(lab)
    a, aw = text(v1, "pixel", 30, M, 176, BONE)
    c, _ = text(v2, "pixel", 30, M + aw + 10, 176, ASH)
    b += [a, c]
    u = 5
    mx, my = W - M - 24 * u, H - 24 - 32 * u
    b.append(rule(W - M - 260, H - 24, 260))
    b.append(glow(mx + 12 * u, my + 18 * u, 88))
    b.append(mo(pose, mx, my, u))
    qw = width(quip, "pixel", 26) + 32
    q, _ = bubble(quip, mx - qw + 36, my - 30)
    b.append(q)
    b.append(finish(W, H))
    return svg(W, H, "".join(b), f"{n}: {label.title()}. {v1} {v2}")


# ------------------------------------------------------------------ cartridges
def cartridge(title, sub, art, stamp, stamp_on, desc=()):
    """A handheld cartridge: Ink-2 shell with grip ridges, a Bone label with the game's art and its blurb."""
    W, H = 300, 420
    b = [f'<rect width="{W}" height="{H}" fill="{INK}"/>']
    # shell: square, with the notched top-right corner
    b.append(f'<path fill="{INK2}" stroke="{ASH_D}" stroke-width="2" d="M14 14H262L286 38V406H14Z"/>')
    for k in range(5):
        b.append(rule(40 + k * 14, 26, 8, ASH_D, 14))
    # label
    lx, ly, lw, lh = 34, 58, 232, 296
    b.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" fill="{BONE}"/>')
    b.append(f'<rect x="{lx + 10}" y="{ly + 10}" width="{lw - 20}" height="140" fill="{INK}"/>')
    b.append(f'<g transform="translate({lx + 10} {ly + 10})">{art}</g>')
    ts = 34
    while width(title, "arcade", ts) > lw - 24:
        ts -= 2
    t, _ = text(title, "arcade", ts, lx + 12, ly + 186, INK)
    s, _ = text(sub, "mono", 11, lx + 12, ly + 214, ASH_D, .04)
    b += [t, s]
    for k, line in enumerate(desc):
        fs = 15
        while width(line, "pixel", fs) > lw - 24:
            fs -= .5
        dl, _ = text(line, "pixel", fs, lx + 12, ly + 244 + k * 20, INK)
        b.append(dl)
    # stamp, tilted like Bug Cave's SQUASHED
    sw = width(stamp, "monob", 14, .06) + 20
    st, _ = text(stamp, "monob", 14, 10, 21, INK if stamp_on else BONE, .06)
    fill = SIGNAL if stamp_on else ASH_D
    b.append(f'<g transform="translate({lx + lw - sw + 8} {ly - 14}) rotate(-6)"><rect width="{sw}" height="30" fill="{fill}"/>{st}</g>')
    # contacts
    for k in range(9):
        b.append(rule(64 + k * 20, 378, 10, ASH_D, 16))
    return svg(W, H, "".join(b), f"Cartridge: {title}. {sub.title()}. {' '.join(desc)} {stamp.title()}.")


def art_thing():
    """THE THING. on a little CRT, with its caret."""
    a, aw = text("THE", "arcade", 58, 18, 66, BONE)
    c, cw = text("THING", "arcade", 58, 18, 120, BONE)
    d, dw = text(".", "arcade", 58, 18 + cw + 2, 120, SIGNAL)
    scan = "".join(f'<rect x="0" y="{y}" width="212" height="1" fill="{INK}" opacity=".35"/>' for y in range(0, 140, 4))
    return a + c + d + f'<rect x="{18 + cw + dw + 10}" y="86" width="12" height="34" fill="{SIGNAL}"/>' + scan


def art_bugrun():
    return (rule(0, 118, 212, ASH_D, 3)
            + glow(64, 70, 50)
            + mo("cheer-0", 30, 22, 3)
            + bug(140, 118 - 48, 2)
            + "".join(f'<rect x="{x}" y="{y}" width="4" height="4" fill="{SIGNAL}"/>'
                      for x, y in ((118, 34), (126, 26), (176, 30), (184, 46))))


def art_block():
    """Display: Block: falling one-letter HTML tags."""
    cell = 20
    pieces = [  # (tag, cells, colour)
        ("b", [(1, 4), (2, 4), (3, 4), (2, 3)], BONE),
        ("i", [(4, 5), (5, 5), (6, 5), (7, 5)], ASH),
        ("p", [(0, 5), (1, 5), (0, 6), (1, 6)], SIGNAL),
        ("a", [(2, 5), (3, 5), (3, 6), (4, 6)], ASH),
        ("u", [(5, 6), (6, 6), (7, 6), (8, 6)], BONE),
        ("s", [(5, 0), (6, 0), (6, 1), (7, 1)], SIGNAL),
    ]
    out = []
    for tag, cells, col in pieces:
        for (cx, cy) in cells:
            out.append(f'<rect x="{6 + cx * cell}" y="{cy * cell}" width="{cell - 2}" height="{cell - 2}" fill="{col}"/>')
        cx, cy = cells[0]
        t, tw = text(f"<{tag}>", "mono", 8, 0, 0, INK)
        t, _ = text(f"<{tag}>", "mono", 8, 6 + cx * cell + (cell - 2 - tw) / 2, cy * cell + 12, INK)
        out.append(t)
    return f'<g shape-rendering="crispEdges">{"".join(out)}</g>'


def art_hq():
    # a pixel desk floor with Mo in his hard hat
    floor = "".join(f'<rect x="{x}" y="{112 + (x // 16) % 2 * 0}" width="14" height="4" fill="{ASH_D}"/>' for x in range(0, 212, 16))
    screens = "".join(f'<rect x="{x}" y="34" width="34" height="24" fill="{INK2}" stroke="{ASH_D}"/>'
                      f'<rect x="{x + 5}" y="{40}" width="{12 + (x % 3) * 4}" height="3" fill="{SIGNAL if x == 128 else ASH}"/>'
                      f'<rect x="{x + 5}" y="{47}" width="18" height="3" fill="{ASH_D}"/>' for x in (128, 168))
    return floor + screens + glow(56, 74, 46) + mo("hardHat-0", 22, 18, 3)


def art_portfolio():
    """A little browser window holding the wordmark."""
    bar = (f'<rect x="0" y="0" width="212" height="18" fill="{INK2}"/>'
           + "".join(f'<rect x="{8 + i * 10}" y="7" width="5" height="5" fill="{c}"/>' for i, c in enumerate((SIGNAL, ASH, ASH_D)))
           + text("MUSTAFA-OMAR.COM", "mono", 8, 46, 13, ASH, .04)[0])
    wm, ww = wordmark(0, 0, 30)
    wm, _ = wordmark((212 - ww) / 2, 78, 30)
    s1, w1 = text("ARCHITECT · DEVOPS", "mono", 9, 0, 0, ASH, .04)
    s1, _ = text("ARCHITECT · DEVOPS", "mono", 9, (212 - w1) / 2, 104, ASH, .04)
    return bar + wm + s1


CARTS = [
    ("portfolio", "PORTFOLIO", "MUSTAFA-OMAR.COM · WORK", art_portfolio, "LIVE", True,
     ("My work: AI solutions, agentic", "workflows and production infra.")),
    ("the-thing", "THE THING", "THE-THING.DEV · PLAYGROUND", art_thing, "LIVE", True,
     ("Films, games, a useless machine,", "and a Chaos Mode that breaks it.")),
    ("bug-run", "BUG RUN", "SUPER MO · GAME", art_bugrun, "SHIPPED", True,
     ("Super Mo's endless runner. Jump", "the bugs, stomp the Bug King.")),
    ("display-block", "DISPLAY: BLOCK", "HTML TAGS · GAME", art_block, "SHIPPED", True,
     ("Falling blocks made of real HTML", "tags. Clear lines with clear: both;")),
    ("the-thing-hq", "THE THING: HQ", "AGENTS · HERDR MOD", art_hq, "SOON", False,
     ("Your coding agents as pixel", "buddies in a command center.")),
]


# ------------------------------------------------------------------ inventory (a Chaos Mode hotbar)
INVENTORY = [
    ("WEB", ["REACT", "NEXT.JS", "TYPESCRIPT", "JAVASCRIPT", "THREE.JS", "WORDPRESS"]),
    ("OPS", ["DOCKER", "LINUX", "GIT", "ACTIONS", "CLOUDFLARE", "NGINX"]),
    ("MAKE", ["FIGMA", "REMOTION", "BLENDER", "POSTMAN", "CLAUDE CODE", "HERDR"]),
]


def inventory():
    W = 1280
    M = 64
    sw, sh, gap = 182, 84, 12
    row_h = sh + 34
    H = 70 + row_h * len(INVENTORY) + 28
    b = [ground(W, H, 77, 0)]
    key = 1
    for r, (name, items) in enumerate(INVENTORY):
        y = 54 + r * row_h
        lab, _ = text(name, "monob", 14, M, y - 10, ASH, .06)
        b.append(lab)
        b.append(rule(M + width(name, "monob", 14, .06) + 12, y - 16, W - 2 * M - width(name, "monob", 14, .06) - 12))
        for c, item in enumerate(items):
            x = M + c * (sw + gap)
            on = r == 0 and c == 0
            b.append(f'<rect x="{x}" y="{y}" width="{sw}" height="{sh}" fill="{INK2}" stroke="{SIGNAL if on else ASH_D}" stroke-width="{4 if on else 2}"/>')
            k, _ = text(f"{key:02d}", "mono", 12, x + 10, y + 20, SIGNAL if on else ASH, .04)
            fs = 20
            while width(item, "mono", fs, .04) > sw - 24:
                fs -= 1
            iw = width(item, "mono", fs, .04)
            t, _ = text(item, "mono", fs, x + (sw - iw) / 2, y + sh / 2 + fs * .42 + 6, BONE, .04)
            b += [k, t]
            key += 1
    hint, hw = text("01 IN HAND · 18 SLOTS", "mono", 12, 0, 0, ASH, .04)
    hint, _ = text("01 IN HAND · 18 SLOTS", "mono", 12, W - M - hw, H - 22, ASH, .04)
    b.append(hint)
    b.append(finish(W, H))
    label = "Inventory. " + ". ".join(f"{n}: " + ", ".join(i.title() for i in items) for n, items in INVENTORY) + "."
    return svg(W, H, "".join(b), label)


# ------------------------------------------------------------------ the "now" dialog box
NOW = [
    ("BY DAY", [("I'm a solutions architect and DevOps engineer.", BONE),
                ("I build AI-powered solutions, agentic workflows,", ASH),
                ("and the production infrastructure under them.", ASH)]),
    ("AFTER HOURS", [("I make The Thing, my playground for films, games", BONE),
                     ("and buttons you probably shouldn't press.", ASH),
                     ("Super Mo lives there. He has opinions.", ASH)]),
]


def dialog():
    """An RPG text box: Mo's portrait in a frame, two speeches, a Signal arrow to read on."""
    W, M = 1280, 64
    H = 430
    b = [ground(W, H, 41, 0)]
    b.append(f'<rect x="{M - 6}" y="26" width="{W - 2 * M + 12}" height="{H - 52}" fill="{INK}" stroke="{ASH_D}" stroke-width="2"/>')
    b.append(f'<rect x="{M}" y="32" width="{W - 2 * M}" height="{H - 64}" fill="{INK2}" stroke="{BONE}" stroke-width="4"/>')
    # portrait
    px, py = M + 28, 70
    b.append(f'<rect x="{px}" y="{py}" width="148" height="180" fill="{INK}" stroke="{ASH_D}" stroke-width="2"/>')
    b.append(glow(px + 74, py + 96, 70))
    b.append(mo("nod-0", px + 14, py + 12, 5))
    n, nw = text("MO", "monob", 14, 0, 0, INK, .06)
    b.append(f'<rect x="{px}" y="{py + 180}" width="148" height="0" fill="none"/>')
    tag, _ = text("MO", "monob", 14, px + 10, py - 8, SIGNAL, .06)
    b.append(tag)
    # speeches
    x = px + 148 + 48
    colw = W - M - 40 - x
    for c, (head, lines) in enumerate(NOW):
        y = 82 + c * 170
        h, _ = text(head, "monob", 14, x, y, SIGNAL, .06)
        b.append(h)
        b.append(rule(x, y + 10, colw))
        for k, (line, col) in enumerate(lines):
            t, _ = text(line, "pixel", 24, x, y + 50 + k * 34, col)
            b.append(t)
    b.append(f'<path class="more" fill="{SIGNAL}" d="M{W - M - 36} {H - 58}h16v4h-4v4h-4v4h-4v-4h-4v-4h-4z"/>')
    b.append(finish(W, H))
    label = " ".join(l for _, ls in NOW for l, _ in ls)
    return svg(W, H, "".join(b), label,
               ".more{animation:more 1s steps(2) infinite}@keyframes more{50%{transform:translateY(4px)}}")


# ------------------------------------------------------------------ link buttons
BUTTONS = [
    ("portfolio", "PORTFOLIO", "MUSTAFA-OMAR.COM", True),
    ("the-thing", "PLAY", "THE-THING.DEV", True),
    ("linkedin", "LINKEDIN", "MOFAKHRI", False),
    ("email", "EMAIL", "SAY HI", False),
    ("instagram", "INSTAGRAM", "MO_FAKHRI98", False),
]


def button(label, value, primary):
    """A square console button: a Silkscreen label over the value, Signal when it's the main way in."""
    W, H = 300, 88
    face = SIGNAL if primary else INK2
    fg = INK if primary else BONE
    sub = INK if primary else ASH
    b = [f'<rect width="{W}" height="{H}" fill="{INK}"/>',
         f'<rect x="4" y="8" width="{W - 8}" height="{H - 12}" fill="{ASH_D if not primary else "#b8360f"}"/>',
         f'<rect x="4" y="4" width="{W - 8}" height="{H - 16}" fill="{face}" stroke="{BONE if not primary else face}" stroke-width="2"/>']
    l, _ = text(label, "monob", 12, 22, 28, sub, .08)
    fs = 22
    while width(value, "mono", fs, .04) > W - 70:
        fs -= 1
    v, _ = text(value, "mono", fs, 22, 60, fg, .04)
    arrow = f'<path fill="{fg}" d="M{W - 40} 30h4v4h4v4h4v4h-4v4h-4v4h-4z"/>'
    b += [l, v, arrow]
    return svg(W, H, "".join(b), f"{label.title()}: {value.lower()}")


# ------------------------------------------------------------------ footer
def footer():
    W, H = 1280, 260
    M = 64
    b = [ground(W, H, 99, 22, [(0, 0, 820, H)])]
    t, tw = text("GAME SAVED", "arcade", 96, M, 112, BONE)
    d, _ = text(".", "arcade", 96, M + tw + 2, 112, SIGNAL)
    v1, _ = text("Thanks for stopping by.", "pixel", 30, M, 162, BONE)
    v2, _ = text("Come back when there's more.", "pixel", 30, M, 198, ASH)
    b += [t, d, v1, v2]
    u = 6
    mx, my = W - M - 24 * u, H - 28 - 32 * u
    b.append(rule(W - M - 300, H - 28, 300))
    b.append(glow(mx + 12 * u, my + 18 * u, 104))
    b.append(mo("sleepy-0", mx, my, u))
    qw = width("Five more min.", "pixel", 26) + 32
    q, _ = bubble("Five more min.", mx - qw + 40, my - 30)
    b.append(q)
    wm, _ = wordmark(M, H - 22, 18)
    b.append(wm)
    b.append(finish(W, H))
    return svg(W, H, "".join(b), "Game saved. Thanks for stopping by. Come back when there's more.")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "hero.svg").write_text(hero())
    for i, (n, slug, label, v1, v2, pose, quip) in enumerate(SECTIONS):
        (OUT / f"{n}-{slug}.svg").write_text(header(n, label, v1, v2, pose, quip, 10 + i))
    for slug, title, sub, art, stamp, on, desc in CARTS:
        (OUT / f"cart-{slug}.svg").write_text(cartridge(title, sub, art(), stamp, on, desc))
    (OUT / "now.svg").write_text(dialog())
    for slug, lab, val, primary in BUTTONS:
        (OUT / f"btn-{slug}.svg").write_text(button(lab, val, primary))
    (OUT / "inventory.svg").write_text(inventory())
    (OUT / "footer.svg").write_text(footer())
    print("art:", sorted(p.name for p in OUT.glob("*.svg")))
