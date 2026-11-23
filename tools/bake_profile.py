"""The profile README's art, in the Supermo design system (The Thing's Arcade edition).

GitHub's Markdown can't load fonts or CSS, so the look lives in SVGs. Type is set in the brand's own
faces (Jersey 10 hooks and numbers, Silkscreen labels, Pixelify Sans voice, Anton for the
MO—FAKHRII wordmark), turned into outlines so every viewer sees them without the fonts. Super Mo is
the real cast art from The Thing: HQ; the bug is Bug Run's crawler.

ONE GRID. Every block is 1280 wide: a full panel, or a row of three cells (1280/3 each) laid side by
side with no gap, so a row reads as one band. Content sits inside the same 64 px margins everywhere,
and a row's three cards land on the same three columns (COLS) as the stats tiles below them.
ONE SURFACE. Flat Ink, cards in Ink-2 with a 2 px Ash-dark rule, Signal only for what matters.
No glow, haze, dust or vignette (The Thing: "no glass, glow, soft shadows").
ONE HEADER. Signal arrow + Silkscreen eyebrow, a Jersey hook in uppercase with a full stop, a rule,
Super Mo peeking over it.

Motion is CSS inside the SVG (GitHub plays it in <img>) and stops for reduced motion; every still
frame is complete.

  python tools/bake_profile.py            (needs fontTools; GITHUB_TOKEN or `gh` for the scoreboard)

The scoreboard (heatmap + stats) is live data, rebuilt daily by .github/workflows/scoreboard.yml.
If GitHub can't be reached, the last numbers in tools/stats-cache.json are used.
"""
import datetime as dt
import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
OUT = ROOT / "art"
USER = "Mustafa98m"

TOK = {t["name"]: t["value"] for t in json.load(open(TOOLS / "tokens.json"))["color"]["tokens"]
       if isinstance(t["value"], str) and t["value"].startswith("#")}
INK, COAL, INK2, ASH_D, ASH, BONE, SIGNAL = (TOK[k] for k in ("ink", "coal", "ink-2", "ash-dark", "ash", "bone", "signal"))

FONTS = {
    "arcade": TOOLS / "fonts/Jersey10-Regular.ttf",
    "mono": TOOLS / "fonts/Silkscreen-Regular.ttf",
    "monob": TOOLS / "fonts/Silkscreen-Bold.ttf",
    "pixel": TOOLS / "fonts/PixelifySans-Variable.ttf",
    "anton": TOOLS / "fonts/Anton-Regular.ttf",
}

# the grid
W, M = 1280, 64
CELL = W / 3
CW, GAP = 340, 66                      # three cards: 3 * 340 + 2 * 66 = 1152 = W - 2M
COLS = [M + i * (CW + GAP) for i in range(3)]
PAD = 28                               # top and bottom padding of every block

_fonts = {}


# ------------------------------------------------------------------ type and sprites
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


def text(s, face, size, x, y, fill, tracking=0.0, anchor="start"):
    w = glyphs(s, face, size, 0, 0, tracking)[1]
    if anchor == "end":
        x -= w
    elif anchor == "middle":
        x -= w / 2
    gl, w = glyphs(s, face, size, x, y, tracking)
    return f'<path fill="{fill}" d="{"".join(d for d, _ in gl)}"/>', w


def width(s, face, size, tracking=0.0):
    return glyphs(s, face, size, 0, 0, tracking)[1]


def label(s, x, y, fill=ASH, size=14, anchor="start", bold=False):
    """Silkscreen label: uppercase, .04em tracking (the site's one tracking)."""
    return text(s, "monob" if bold else "mono", size, x, y, fill, .04, anchor)[0]


def mo(pose, x, y, unit, cls=""):
    """Super Mo's real sprite (24 x 32 art px), top left at (x, y), `unit` px per art px."""
    src = (TOOLS / f"mo/{pose}.svg").read_text()
    inner = re.search(r"<svg[^>]*>(.*)</svg>", src, re.S).group(1)
    c = f' class="{cls}"' if cls else ""
    return f'<g{c} transform="translate({x} {y}) scale({unit})" shape-rendering="crispEdges">{inner}</g>'


# Bug Run's crawler (RunnerArt.tsx BugSprite), 30 x 24 art px, facing left.
BUG = "M4 4h2v4H4ZM10 2h2v6h-2ZM2 8h10V6h12v2h4v4h2v8H8v-2H2ZM10 20h4v4h-4ZM18 20h4v4h-4ZM26 20h4v4h-4Z"
BUG_EYES = "M4 10h4v4H4ZM16 10h4v4h-4ZM24 14h4v4h-4ZM12 16h4v2h-4Z"


def bug(x, y, unit, body=BONE, eyes=INK):
    return (f'<g transform="translate({x} {y}) scale({unit})" shape-rendering="crispEdges">'
            f'<path fill="{body}" d="{BUG}"/><path fill="{eyes}" d="{BUG_EYES}"/></g>')


HEART = "M1 0h2v1H1ZM4 0h2v1H4ZM0 1h7v2H0ZM1 3h5v1H1ZM2 4h3v1H2ZM3 5h1v1H3Z"


def rect(x, y, w, h, fill, stroke=None, sw=2):
    s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"{s} shape-rendering="crispEdges"/>'


def rule(x, y, w, fill=ASH_D, h=2):
    return rect(x, y, w, h, fill)


def card(x, y, w, h, on=False):
    """The one card: Ink-2, a 2 px rule; Signal rule when it's the one in hand."""
    return rect(x + 1, y + 1, w - 2, h - 2, INK2, SIGNAL if on else ASH_D, 2)


def arrow_right(x, y, fill, u=3):
    """A pixel → (7 x 5 art px), top left at (x, y)."""
    return (f'<path fill="{fill}" shape-rendering="crispEdges" transform="translate({x} {y}) scale({u})" '
            f'd="M0 2h5v1H0ZM3 0h1v1H3ZM4 1h1v1H4ZM5 2h1v1H5ZM4 3h1v1H4ZM3 4h1v1H3Z"/>')


def arrow_down(x, y, fill, u=3):
    return (f'<path fill="{fill}" shape-rendering="crispEdges" transform="translate({x} {y}) scale({u})" '
            f'd="M2 0h1v5H2ZM0 3h1v1H0ZM1 4h1v1H1ZM3 4h1v1H3ZM4 3h1v1H4ZM2 5h1v1H2Z"/>')


def wordmark(x, y, size, fill=BONE):
    """MO—FAKHRII to the site's CSS: gap .16em, bar .42em x .11em in Signal, centred on the line."""
    a, aw = text("MO", "anton", size, x, y, fill)
    gap, bw, bh = size * .16, size * .42, size * .11
    bar = rect(round(x + aw + gap, 2), round(y - size * .40 - bh / 2, 2), round(bw, 2), round(bh, 2), SIGNAL)
    b, fw = text("FAKHRII", "anton", size, x + aw + gap * 2 + bw, y, fill)
    return a + bar + b, aw + gap * 2 + bw + fw


def svg(w, h, body, label_, style=""):
    st = f"<style>{style}@media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}</style>" if style else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{round(w)}" height="{h}" viewBox="0 0 {w:g} {h}" '
            f'role="img" aria-label="{label_}"><title>{label_}</title>{st}'
            f'<rect width="{w:g}" height="{h}" fill="{INK}"/>{body}</svg>\n')


def cell_svg(i, h, draw, label_, style=""):
    """Cell i of a row of three: the card is drawn at its grid column, shifted into the cell."""
    off = COLS[i] - i * CELL
    return svg(CELL, h, f'<g transform="translate({off:.3f} 0)">{draw}</g>', label_, style)


# ------------------------------------------------------------------ hero
def hero():
    H = 640
    b = []
    # header bar, like the site's: the wordmark, then a ruled eyebrow row
    wm, _ = wordmark(M, 74, 36)
    b.append(wm)
    b.append(label("MUSTAFA-OMAR.COM", W - M, 70, ASH, 14, "end"))
    b.append(rule(M, 104, W - 2 * M))
    b.append(rect(M, 125, 10, 10, SIGNAL))
    b.append(label("SOLUTIONS ARCHITECT + DEVOPS ENGINEER", M + 22, 136, BONE, 14))
    b.append(label("PLAYER 1 · MOSUL, IRAQ", W - M, 136, ASH, 14, "end"))
    b.append(rule(M, 156, W - 2 * M))

    # the hook, typed on a CRT, scanlines through the letters like the site's hero
    css = []
    i = 0
    for line, y in (("MUSTAFA", 328), ("OMAR", 466)):
        gl, w = glyphs(line, "arcade", 156, M - 6, y)
        for d, _ in gl:
            b.append(f'<path class="k" style="animation-delay:{0.5 + i * 0.12:.2f}s" fill="{BONE}" d="{d}"/>')
            i += 1
        last_w = w
    stop, sw = glyphs(".", "arcade", 156, M - 6 + last_w + 2, 466)
    b.append(f'<path class="k" style="animation-delay:{0.5 + i * 0.12:.2f}s" fill="{SIGNAL}" d="{stop[0][0]}"/>')
    cx = M - 6 + last_w + 2 + sw + 14
    b.append(f'<rect class="caret" x="{cx:.1f}" y="370" width="30" height="96" fill="{SIGNAL}"/>')
    b.append(f'<defs><pattern id="scan" width="4" height="5" patternUnits="userSpaceOnUse">'
             f'<rect width="4" height="1.5" fill="{INK}" opacity=".55"/></pattern></defs>'
             f'<rect x="{M - 10}" y="200" width="680" height="280" fill="url(#scan)"/>')
    css.append(".k{animation:type .1s steps(1) backwards}@keyframes type{from{opacity:0}}"
               f".caret{{animation:blink 1.1s steps(1) {0.5 + (i + 1) * 0.12:.2f}s infinite}}"
               "@keyframes blink{50%{opacity:0}}")

    b.append(text("I build real systems for work,", "pixel", 28, M, 530, BONE)[0])
    b.append(text("and strange little things for fun.", "pixel", 28, M, 568, ASH)[0])

    # Bug Run on a little screen: Mo walks, a bug crawls in, Mo hops it
    sx, sy, sw_, sh = 760, 196, 456, 372
    b.append(card(sx, sy, sw_, sh))
    b.append(rect(sx + 12, sy + 44, sw_ - 24, sh - 56, INK))
    b.append(rect(sx + 14, sy + 20, 8, 8, SIGNAL))
    b.append(label("BUG CAVE", sx + 30, sy + 30, BONE, 12))
    for k in range(3):
        b.append(f'<path fill="{SIGNAL}" transform="translate({sx + sw_ - 30 - k * 26} {sy + 16}) scale(3)" d="{HEART}" shape-rendering="crispEdges"/>')
    iw, ih = sw_ - 24, sh - 56
    fy = ih - 64
    u = 4
    mx, my = 96, fy - 32 * u
    inner = [rect(0, fy, iw, 2, ASH_D)]
    for r in range(3):  # bricks
        for c in range(-1, iw // 40 + 1):
            inner.append(rect(c * 40 + (20 if r % 2 else 0) + 2, fy + 6 + r * 18, 36, 14, INK2))
    inner.append(f'<g class="hop"><g class="f0">{mo("walk-0", mx, my, u)}</g><g class="f1">{mo("walk-1", mx, my, u)}</g></g>')
    bu = 2
    inner.append(f'<g class="crawl">{bug(300, fy - 24 * bu, bu)}</g>')
    b.append(f'<svg x="{sx + 12}" y="{sy + 44}" width="{iw}" height="{ih}" overflow="hidden">{"".join(inner)}</svg>')
    travel = iw + 30 * bu
    css.append(
        ".f0{animation:w0 .5s steps(1) infinite}.f1{opacity:0;animation:w1 .5s steps(1) infinite}"
        "@keyframes w0{50%{opacity:0}}@keyframes w1{50%{opacity:1}}"
        ".crawl{animation:crawl 2.4s linear infinite}"
        f"@keyframes crawl{{from{{transform:translateX({iw - 300}px)}}to{{transform:translateX(-{300 + 30 * bu}px)}}}}"
        ".hop{animation:hop 2.4s steps(3) infinite}"
        "@keyframes hop{0%,50%{transform:translateY(0)}58%{transform:translateY(-72px)}66%{transform:translateY(-84px)}"
        "74%{transform:translateY(-72px)}82%,100%{transform:translateY(0)}}")
    b.append(label("SUPER MO · BUG RUN · AUTO-PLAY", sx + sw_, sy + sh + 30, ASH, 12, "end"))
    return svg(W, H, "".join(b),
               "Mustafa Omar. Solutions architect and DevOps engineer. I build real systems for work, and strange little things for fun. Super Mo hops a bug.",
               "".join(css))


# ------------------------------------------------------------------ section headers
SECTIONS = [
    ("01", "what-i-do", "BY DAY, AFTER HOURS", "WHAT I DO.", "peekUpNod-0", "MUSTAFA-OMAR.COM"),
    ("02", "things-i-made", "CARTRIDGES", "THINGS I MADE.", "peekPoint-0", "THE-THING.DEV"),
    ("03", "scoreboard", "LIVE FROM GITHUB", "THE SCOREBOARD.", "peekUpHappy-0", "UPDATED DAILY"),
    ("04", "the-tools", "INVENTORY", "THE TOOLS.", "peekUp-0", "18 SLOTS"),
    ("05", "say-hi", "LINK CABLE", "SAY HI.", "peekWave-0", "I READ EVERYTHING"),
]


def header(n, eyebrow, hook, pose, aside):
    H = 210
    b = [arrow_down(M, 48, SIGNAL), label(f"{n} · {eyebrow}", M + 26, 64, ASH, 14)]
    b.append(text(hook, "arcade", 92, M - 2, 152, BONE)[0])
    ry = 176
    u = 4
    mx = W - M - 24 * u
    b.append(mo(pose, mx, ry + 2 - 32 * u, u))
    b.append(rule(M, ry, W - 2 * M))
    b.append(label(aside, mx - 24, 152, SIGNAL, 13, "end"))
    return svg(W, H, "".join(b), f"{n}. {eyebrow.title()}. {hook.title()}")


# ------------------------------------------------------------------ 01: the dialog box
NOW = [
    ("BY DAY", [("I'm a solutions architect and DevOps engineer.", BONE),
                ("I build AI-powered solutions, agentic workflows,", ASH),
                ("and the production infrastructure under them.", ASH)]),
    ("AFTER HOURS", [("I make The Thing, my playground for films, games", BONE),
                     ("and buttons you probably shouldn't press.", ASH),
                     ("Super Mo lives there. He has opinions.", ASH)]),
]


def dialog():
    H = PAD + 352 + PAD
    b = [card(M, PAD, W - 2 * M, 352)]
    px, py = M + 32, PAD + 52
    b.append(label("MO", px, py - 14, SIGNAL, 13, bold=True))
    b.append(rect(px, py, 152, 176, INK, ASH_D))
    b.append(mo("nod-0", px + 16, py + 14, 5))
    x = px + 152 + 48
    cw = W - M - 40 - x
    for c, (head, lines) in enumerate(NOW):
        y = PAD + 50 + c * 160
        b.append(label(head, x, y, SIGNAL, 13, bold=True))
        b.append(rule(x, y + 12, cw))
        for k, (line, col) in enumerate(lines):
            b.append(text(line, "pixel", 23, x, y + 50 + k * 32, col)[0])
    b.append(f'<path class="more" fill="{SIGNAL}" d="M{W - M - 40} {PAD + 318}h16v4h-4v4h-4v4h-4v-4h-4v-4h-4z"/>')
    label_ = " ".join(l for _, ls in NOW for l, _ in ls)
    return svg(W, H, "".join(b), label_, ".more{animation:more 1s steps(2) infinite}@keyframes more{50%{transform:translateY(4px)}}")


# ------------------------------------------------------------------ 02: cartridges
def cartridge(i, title, sub, art, stamp, stamp_on, desc, empty=False):
    """A handheld cartridge, CW wide: Ink-2 shell with grip ridges, a Bone label, art, blurb and stamp."""
    k = CW / 300
    s = []
    dash = ' stroke-dasharray="8 6"' if empty else ""
    s.append(f'<path fill="{INK if empty else INK2}" stroke="{ASH_D}" stroke-width="2"{dash} d="M14 14H262L286 38V406H14Z"/>')
    for r in range(5):
        s.append(rule(40 + r * 14, 26, 8, ASH_D, 14))
    lx, ly, lw, lh = 34, 58, 232, 296
    if empty:
        s.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" fill="none" stroke="{ASH_D}" stroke-width="2" stroke-dasharray="6 6"/>')
        s.append(text("EMPTY", "arcade", 44, lx + lw / 2, ly + 140, ASH_D, anchor="middle")[0])
        s.append(text("SLOT 06", "mono", 12, lx + lw / 2, ly + 168, ASH_D, .04, "middle")[0])
    else:
        s.append(rect(lx, ly, lw, lh, BONE))
        s.append(rect(lx + 10, ly + 10, lw - 20, 140, INK))
        s.append(f'<g transform="translate({lx + 10} {ly + 10})">{art}</g>')
        ts = 34
        while width(title, "arcade", ts) > lw - 24:
            ts -= 2
        s.append(text(title, "arcade", ts, lx + 12, ly + 186, INK)[0])
        s.append(text(sub, "mono", 11, lx + 12, ly + 214, ASH_D, .04)[0])
    for j, line in enumerate(desc):
        fs = 15
        while width(line, "pixel", fs) > lw - 24:
            fs -= .5
        s.append(text(line, "pixel", fs, lx + 12, ly + 244 + j * 20, ASH if empty else INK)[0])
    if stamp:
        sw = width(stamp, "monob", 14, .06) + 20
        st, _ = text(stamp, "monob", 14, 10, 21, INK if stamp_on else BONE, .06)
        s.append(f'<g transform="translate({lx + lw - sw + 8} {ly - 14}) rotate(-6)">{rect(0, 0, sw, 30, SIGNAL if stamp_on else ASH_D)}{st}</g>')
    for j in range(9):
        s.append(rule(64 + j * 20, 378, 10, ASH_D, 16))
    h = round(420 * k)
    body = f'<g transform="translate(0 {PAD - 10}) scale({k:.4f})">{"".join(s)}</g>'
    return cell_svg(i, h + 2 * PAD - 20, body, f"Cartridge: {title}. {' '.join(desc)} {stamp.title() if stamp else ''}".strip())


def art_thing():
    a, _ = text("THE", "arcade", 58, 18, 66, BONE)
    c, cw = text("THING", "arcade", 58, 18, 120, BONE)
    d, dw = text(".", "arcade", 58, 18 + cw + 2, 120, SIGNAL)
    scan = "".join(f'<rect x="0" y="{y}" width="212" height="1" fill="{INK}" opacity=".35"/>' for y in range(0, 140, 4))
    return a + c + d + rect(18 + cw + dw + 10, 86, 12, 34, SIGNAL) + scan


def art_bugrun():
    return (rule(0, 118, 212, ASH_D, 3) + mo("cheer-0", 30, 22, 3) + bug(140, 70, 2)
            + "".join(rect(x, y, 4, 4, SIGNAL) for x, y in ((118, 34), (126, 26), (176, 30), (184, 46))))


def art_block():
    cell = 20
    pieces = [("b", [(1, 4), (2, 4), (3, 4), (2, 3)], BONE), ("i", [(4, 5), (5, 5), (6, 5), (7, 5)], ASH),
              ("p", [(0, 5), (1, 5), (0, 6), (1, 6)], SIGNAL), ("a", [(2, 5), (3, 5), (3, 6), (4, 6)], ASH),
              ("u", [(5, 6), (6, 6), (7, 6), (8, 6)], BONE), ("s", [(5, 0), (6, 0), (6, 1), (7, 1)], SIGNAL)]
    out = []
    for tag, cells, col in pieces:
        for (cx, cy) in cells:
            out.append(rect(6 + cx * cell, cy * cell, cell - 2, cell - 2, col))
        cx, cy = cells[0]
        out.append(text(f"<{tag}>", "mono", 8, 6 + cx * cell + (cell - 2) / 2, cy * cell + 12, INK, anchor="middle")[0])
    return "".join(out)


def art_hq():
    floor = "".join(rect(x, 112, 14, 4, ASH_D) for x in range(0, 212, 16))
    screens = "".join(rect(x, 34, 34, 24, INK2, ASH_D, 1) + rect(x + 5, 40, 12 + (x % 3) * 4, 3, SIGNAL if x == 128 else ASH)
                      + rect(x + 5, 47, 18, 3, ASH_D) for x in (128, 168))
    return floor + screens + mo("hardHat-0", 22, 18, 3)


def art_portfolio():
    bar = (rect(0, 0, 212, 18, INK2) + "".join(rect(8 + i * 10, 7, 5, 5, c) for i, c in enumerate((SIGNAL, ASH, ASH_D)))
           + text("MUSTAFA-OMAR.COM", "mono", 8, 46, 13, ASH, .04)[0])
    _, ww = wordmark(0, 0, 30)
    wm, _ = wordmark((212 - ww) / 2, 82, 30)
    return bar + wm + text("ARCHITECT · DEVOPS", "mono", 9, 106, 106, ASH, .04, "middle")[0]


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


# ------------------------------------------------------------------ 03: the scoreboard (live)
def _token():
    if os.environ.get("GITHUB_TOKEN"):
        return os.environ["GITHUB_TOKEN"]
    try:
        return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return None


def fetch_stats():
    cache = TOOLS / "stats-cache.json"
    try:
        q = ('query($u:String!){user(login:$u){repositories(ownerAffiliations:OWNER,privacy:PUBLIC){totalCount}'
             'followers{totalCount}contributionsCollection{contributionCalendar{totalContributions '
             'weeks{contributionDays{date contributionCount}}}}}}')
        req = urllib.request.Request("https://api.github.com/graphql",
                                     data=json.dumps({"query": q, "variables": {"u": USER}}).encode(),
                                     headers={"Authorization": f"bearer {_token()}", "User-Agent": "profile-bake"})
        u = json.load(urllib.request.urlopen(req, timeout=30))["data"]["user"]
        cal = u["contributionsCollection"]["contributionCalendar"]
        weeks = [[(d["date"], d["contributionCount"]) for d in w["contributionDays"]] for w in cal["weeks"]]
        visitors = None
        try:
            badge = urllib.request.urlopen(urllib.request.Request(
                f"https://komarev.com/ghpvc/?username={USER}", headers={"User-Agent": "profile-bake"}), timeout=20).read().decode()
            nums = re.findall(r">([\d,]+)<", badge)
            visitors = int(nums[-1].replace(",", "")) if nums else None
        except Exception:
            pass
        old = json.loads(cache.read_text()) if cache.exists() else {}
        data = {"updated": dt.date.today().isoformat(), "total": cal["totalContributions"], "weeks": weeks,
                "repos": u["repositories"]["totalCount"], "followers": u["followers"]["totalCount"],
                "visitors": visitors if visitors is not None else old.get("visitors")}
        cache.write_text(json.dumps(data))
        return data
    except Exception as e:
        print("scoreboard: using cache:", e)
        return json.loads(cache.read_text())


def streaks(weeks):
    days = [c for w in weeks for _, c in w]
    best = run = 0
    for c in days:
        run = run + 1 if c else 0
        best = max(best, run)
    cur = 0
    tail = days[:-1] if days and days[-1] == 0 else days  # today may not have started yet
    for c in reversed(tail):
        if not c:
            break
        cur += 1
    return cur, best, max(days or [0]), sum(1 for c in days if c)


def level_colors():
    def mix(a, b, t):
        a, b = int(a[1:], 16), int(b[1:], 16)
        ch = [round(((a >> s) & 255) * (1 - t) + ((b >> s) & 255) * t) for s in (16, 8, 0)]
        return "#" + "".join(f"{c:02x}" for c in ch)
    return [INK, ASH_D, mix(INK2, SIGNAL, .4), mix(INK2, SIGNAL, .7), SIGNAL]


def level(c, top):
    if c == 0:
        return 0
    q = c / max(top, 1)
    return 1 if q <= .1 else 2 if q <= .3 else 3 if q <= .6 else 4


def heatmap(data):
    """The contribution grid; Super Mo runs above it and each week powers on as he passes."""
    weeks = data["weeks"]
    nweek = len(weeks)
    CH = 372
    H = PAD + CH + PAD
    cx0, cy0, cw_ = M, PAD, W - 2 * M
    b = [card(cx0, cy0, cw_, CH)]
    upd = dt.date.fromisoformat(data["updated"]).strftime("%d %b %Y").upper()
    b.append(rect(cx0 + 24, cy0 + 27, 10, 10, SIGNAL))
    b.append(label("CONTRIBUTIONS · LAST 12 MONTHS", cx0 + 44, cy0 + 38, BONE, 13))
    b.append(label(f"UPDATED {upd}", cx0 + cw_ - 24, cy0 + 38, ASH, 13, "end"))
    gx = cx0 + 24
    gw = cw_ - 48
    pitch = gw / nweek
    cs = pitch - 4
    floor = cy0 + 138
    gy = floor + 34
    b.append(rule(gx, floor, gw))
    cols = level_colors()
    top = max((c for w in weeks for _, c in w), default=1)
    # month labels
    last = None
    for wi, w in enumerate(weeks):
        mth = dt.date.fromisoformat(w[0][0]).strftime("%b").upper()
        if mth != last and wi < nweek - 2:
            b.append(label(mth, gx + wi * pitch, floor + 22, ASH, 10))
            last = mth
    # cells (Sunday first, like GitHub)
    for wi, w in enumerate(weeks):
        for d, c in w:
            wd = (dt.date.fromisoformat(d).weekday() + 1) % 7
            b.append(rect(round(gx + wi * pitch, 2), round(gy + wd * pitch, 2), round(cs, 2), round(cs, 2), cols[level(c, top)]))
    # Super Mo's run: per week, a dim cover that lifts when he passes, and a spark if that week had work
    T = 16
    u = 2
    mw = 24 * u
    x_end = gx + gw - mw
    x_start = gx - 4
    run = .82
    css = [".f0{animation:w0 .4s steps(1) infinite}.f1{opacity:0;animation:w1 .4s steps(1) infinite}"
           "@keyframes w0{50%{opacity:0}}@keyframes w1{50%{opacity:1}}",
           f".run{{animation:run {T}s linear infinite}}"
           f"@keyframes run{{0%{{transform:translateX({x_start - x_end:.1f}px)}}{run * 100:.1f}%,100%{{transform:translateX(0)}}}}"]
    covers = []
    for wi, w in enumerate(weeks):
        xc = gx + wi * pitch + cs / 2
        f = run * (xc - (x_start + mw / 2)) / (x_end - x_start)
        f = min(max(f, 0), run) * 100
        covers.append(f'<rect class="c{wi}" x="{gx + wi * pitch - 1:.2f}" y="{gy - 1}" width="{pitch:.2f}" height="{7 * pitch:.2f}" fill="{INK2}" opacity="0"/>')
        css.append(f".c{wi}{{animation:c{wi} {T}s linear infinite}}"
                   f"@keyframes c{wi}{{0%,{f:.2f}%{{opacity:.9}}{f + .3:.2f}%,97%{{opacity:0}}100%{{opacity:.9}}}}")
        if sum(c for _, c in w):
            covers.append(f'<g class="s{wi}" opacity="0">{rect(round(xc - 2), floor - 14, 4, 4, SIGNAL)}'
                          f'{rect(round(xc - 8), floor - 22, 4, 4, SIGNAL)}{rect(round(xc + 4), floor - 24, 4, 4, SIGNAL)}</g>')
            css.append(f".s{wi}{{animation:s{wi} {T}s steps(1) infinite}}"
                       f"@keyframes s{wi}{{0%,{f:.2f}%{{opacity:0}}{f + .1:.2f}%{{opacity:1}}{f + 1.6:.2f}%,100%{{opacity:0}}}}")
    b += covers
    my = floor - 32 * u
    b.append(f'<g class="run"><g class="f0">{mo("walk-0", x_end, my, u)}</g><g class="f1">{mo("walk-1", x_end, my, u)}</g></g>')
    # legend + caption
    ly = gy + 7 * pitch + 28
    b.append(label("SUPER MO POWERS ON EACH WEEK AS HE RUNS BY", gx, ly + 10, ASH, 11))
    lx = gx + gw - 5 * 16 - width("MORE", "mono", 11, .04) - 10
    b.append(label("LESS", lx - 10, ly + 10, ASH, 11, "end"))
    for k, c in enumerate(cols):
        b.append(rect(lx + k * 16, ly, 12, 12, c, ASH_D if k == 0 else None, 1))
    b.append(label("MORE", lx + 5 * 16 + 6, ly + 10, ASH, 11))
    return svg(W, H, "".join(b), f"{data['total']:,} contributions in the last 12 months, as a heatmap. Super Mo runs across it.", "".join(css))


def stats(data):
    cur, best, busiest, active = streaks(data["weeks"])
    tiles = [
        ("CONTRIBUTIONS", f"{data['total']:,}", "LAST 12 MONTHS"),
        ("CURRENT STREAK", f"{cur:02d}", "DAYS IN A ROW"),
        ("LONGEST STREAK", f"{best:02d}", "DAYS IN A ROW"),
        ("ACTIVE DAYS", f"{active:,}", "OF THE LAST 365"),
        ("BUSIEST DAY", f"{busiest:,}", "CONTRIBUTIONS"),
        ("PROFILE VISITORS", f"{data['visitors']:,}" if data.get("visitors") else "--", "SINCE THE COUNTER STARTED"),
    ]
    th, tg = 132, 22
    H = PAD + 2 * th + tg + PAD
    b = []
    for k, (lab, num, unit) in enumerate(tiles):
        x, y = COLS[k % 3], PAD + (k // 3) * (th + tg)
        b.append(card(x, y, CW, th, on=k == 0))
        b.append(rect(x + 20, y + 21, 8, 8, SIGNAL))
        b.append(label(lab, x + 36, y + 30, BONE, 12))
        b.append(text(num, "arcade", 72, x + 18, y + 98, SIGNAL if k == 0 else BONE)[0])
        b.append(label(unit, x + 20, y + 118, ASH, 10))
    lbl = ". ".join(f"{l.title()}: {n} {u.lower()}" for l, n, u in tiles)
    return svg(W, H, "".join(b), lbl)


# ------------------------------------------------------------------ 04: inventory (a Chaos Mode hotbar)
INVENTORY = [
    ("WEB", ["REACT", "NEXT.JS", "TYPESCRIPT", "JAVASCRIPT", "THREE.JS", "WORDPRESS"]),
    ("OPS", ["DOCKER", "LINUX", "GIT", "ACTIONS", "CLOUDFLARE", "NGINX"]),
    ("MAKE", ["FIGMA", "REMOTION", "BLENDER", "POSTMAN", "CLAUDE CODE", "HERDR"]),
]


def inventory():
    sw, sh, gap = (W - 2 * M - 5 * 12) / 6, 84, 12
    row_h = sh + 40
    H = PAD + row_h * len(INVENTORY) - 14 + PAD
    b = []
    key = 1
    for r, (name, items) in enumerate(INVENTORY):
        y = PAD + 26 + r * row_h
        b.append(label(name, M, y - 12, ASH, 12, bold=True))
        lw_ = width(name, "monob", 12, .04) + 12
        b.append(rule(M + lw_, y - 18, W - 2 * M - lw_))
        for c, item in enumerate(items):
            x = M + c * (sw + gap)
            on = r == 0 and c == 0
            b.append(card(round(x, 2), y, round(sw, 2), sh, on))
            b.append(label(f"{key:02d}", x + 12, y + 22, SIGNAL if on else ASH, 11))
            fs = 18
            while width(item, "mono", fs, .04) > sw - 24:
                fs -= 1
            b.append(label(item, x + sw / 2, y + sh / 2 + fs * .42 + 6, BONE, fs, "middle"))
            key += 1
    lbl = "Inventory. " + ". ".join(f"{n}: " + ", ".join(i.title() for i in items) for n, items in INVENTORY) + "."
    return svg(W, H, "".join(b), lbl)


# ------------------------------------------------------------------ 05: link buttons
BUTTONS = [
    ("portfolio", "PORTFOLIO", "MUSTAFA-OMAR.COM", True),
    ("the-thing", "PLAY", "THE-THING.DEV", True),
    ("linkedin", "LINKEDIN", "MOFAKHRI", False),
    ("email", "EMAIL", "SAY HI", False),
    ("instagram", "INSTAGRAM", "MO_FAKHRII", False),
    ("repos", "GITHUB", "ALL REPOS", False),
]


def button(i, lab, value, primary):
    """A square button, CW wide: Signal with Ink type when it's a main way in, else the card."""
    bh = 96
    H = 12 + bh + 12
    fg = INK if primary else BONE
    sub = INK if primary else ASH
    s = [rect(0, 12, CW, bh, SIGNAL) if primary else card(0, 12, CW, bh)]
    s.append(label(lab, 22, 44, sub, 12, bold=True))
    fs = 22
    while width(value, "mono", fs, .04) > CW - 80:
        fs -= 1
    s.append(label(value, 22, 82, fg, fs))
    s.append(arrow_right(CW - 46, 52, fg, 4))
    return cell_svg(i, H, "".join(s), f"{lab.title()}: {value.lower()}")


# ------------------------------------------------------------------ footer
def footer():
    H = 290
    b = [rule(M, 30, W - 2 * M)]
    t, tw = text("GAME SAVED", "arcade", 92, M - 2, 128, BONE)
    b += [t, text(".", "arcade", 92, M + tw, 128, SIGNAL)[0]]
    b.append(text("Thanks for stopping by.", "pixel", 26, M, 172, BONE)[0])
    b.append(text("Come back when there's more.", "pixel", 26, M, 206, ASH)[0])
    u = 5
    mx, my = W - M - 24 * u, 236 - 32 * u
    b.append(mo("sleepy-0", mx, my, u))
    b.append(label("MUSTAFA-OMAR.COM · THE-THING.DEV", W - M, 266, ASH, 12, "end"))
    b.append(rule(M, 236, W - 2 * M))
    wm, _ = wordmark(M, 268, 18)
    b.append(wm)
    return svg(W, H, "".join(b), "Game saved. Thanks for stopping by. Come back when there's more.")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    (OUT / "hero.svg").write_text(hero())
    for n, slug, eyebrow, hook, pose, aside in SECTIONS:
        (OUT / f"h{n}-{slug}.svg").write_text(header(n, eyebrow, hook, pose, aside))
    (OUT / "now.svg").write_text(dialog())
    for i, (slug, title, sub, art, stamp, on, desc) in enumerate(CARTS):
        (OUT / f"cart-{i + 1}-{slug}.svg").write_text(cartridge(i % 3, title, sub, art(), stamp, on, desc))
    (OUT / "cart-6-empty.svg").write_text(cartridge(2, "EMPTY SLOT", "", "", "", False, ("Saving this one for", "the next thing."), empty=True))
    data = fetch_stats()
    (OUT / "heatmap.svg").write_text(heatmap(data))
    (OUT / "stats.svg").write_text(stats(data))
    (OUT / "inventory.svg").write_text(inventory())
    for i, (slug, lab, val, primary) in enumerate(BUTTONS):
        (OUT / f"btn-{i + 1}-{slug}.svg").write_text(button(i % 3, lab, val, primary))
    (OUT / "footer.svg").write_text(footer())
    print("art:", len(list(OUT.glob("*.svg"))), "files")
