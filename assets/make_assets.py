"""Generate 3D-style animated SVG assets for the GitHub profile README."""
import math, os, random, sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "assets"
os.makedirs(OUT, exist_ok=True)

BG = "#0D1117"
CYAN = "#22D3EE"
TEAL = "#0891B2"
VIOLET = "#7C3AED"
PINK = "#EC4899"
MONO = "'JetBrains Mono','Fira Code','SFMono-Regular',Consolas,'Liberation Mono',monospace"
SANS = "'Segoe UI',Inter,'Helvetica Neue',Arial,sans-serif"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def write(name, svg):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)


def glow_filter(fid, std=3):
    return (f'<filter id="{fid}" x="-30%" y="-30%" width="160%" height="160%">'
            f'<feGaussianBlur stdDeviation="{std}" result="b"/>'
            f'<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')


def extruded_text(x, y, text, size, family, weight, depth, face_fill, side_from, side_to,
                  anchor="middle", dx=1.0, dy=1.0, extra=""):
    """Stack offset copies to fake a 3D extrusion, then the lit face on top."""
    parts = []
    for i in range(depth, 0, -1):
        t = i / depth
        c = mix(side_from, side_to, t)
        parts.append(f'<text x="{x + i*dx:.1f}" y="{y + i*dy:.1f}" font-family="{family}" '
                     f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{c}">{esc(text)}</text>')
    parts.append(f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
                 f'text-anchor="{anchor}" fill="{face_fill}" {extra}>{esc(text)}</text>')
    return "\n".join(parts)


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    ra, rb = hex2rgb(a), hex2rgb(b)
    return "#%02x%02x%02x" % tuple(round(ra[i] + (rb[i]-ra[i]) * t) for i in range(3))


# ---------- wireframe solids (rotating via SMIL path morph) ----------
def rot(v, ax, ay):
    x, y, z = v
    # rotate around Y
    x, z = x*math.cos(ay) + z*math.sin(ay), -x*math.sin(ay) + z*math.cos(ay)
    # rotate around X
    y, z = y*math.cos(ax) - z*math.sin(ax), y*math.sin(ax) + z*math.cos(ax)
    return x, y, z


def project(v, cx, cy, s, f=4.0):
    x, y, z = v
    k = f / (f + z)
    return cx + x*s*k, cy + y*s*k


def wire_anim(verts, edges, cx, cy, s, dur, color, frames=72, width=2, tilt=0.45, reverse=False):
    ds = []
    for i in range(frames + 1):
        a = 2*math.pi*i/frames * (-1 if reverse else 1)
        pts = [project(rot(v, tilt + 0.25*math.sin(a), a), cx, cy, s) for v in verts]
        d = " ".join(f"M{pts[e[0]][0]:.1f},{pts[e[0]][1]:.1f}L{pts[e[1]][0]:.1f},{pts[e[1]][1]:.1f}" for e in edges)
        ds.append(d)
    vertex_dots = ""
    return (f'<path d="{ds[0]}" stroke="{color}" stroke-width="{width}" fill="none" stroke-linecap="round" filter="url(#glow)">'
            f'<animate attributeName="d" dur="{dur}s" repeatCount="indefinite" values="{";".join(ds)}"/></path>{vertex_dots}')


CUBE_V = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
CUBE_E = [(a, b) for a in range(8) for b in range(a+1, 8)
          if sum(1 for k in range(3) if CUBE_V[a][k] != CUBE_V[b][k]) == 1]
OCTA_V = [(1.4, 0, 0), (-1.4, 0, 0), (0, 1.4, 0), (0, -1.4, 0), (0, 0, 1.4), (0, 0, -1.4)]
OCTA_E = [(a, b) for a in range(6) for b in range(a+1, 6) if a//2 != b//2]


def perspective_grid(x0, x1, horizon, bottom, vpx, color, lines=26, dur=2.2, flip=False):
    """Animated synthwave floor. If flip, it's a ceiling (mirrored)."""
    out = []
    H = bottom - horizon
    # converging verticals
    for k in range(-24, 25):
        xb = vpx + k * 70
        out.append(f'<line x1="{vpx}" y1="{horizon}" x2="{xb}" y2="{bottom}" />')
    # receding horizontals, scrolling toward viewer
    zmin = 1.0
    steps = 12
    for i in range(lines):
        z0 = zmin + i + 1
        vals = []
        for s in range(steps + 1):
            z = z0 - s / steps
            vals.append(f"{horizon + H*zmin/z:.2f}")
        y0 = vals[0]
        v = ";".join(vals)
        out.append(f'<line x1="{x0}" x2="{x1}" y1="{y0}" y2="{y0}">'
                   f'<animate attributeName="y1" values="{v}" dur="{dur}s" repeatCount="indefinite"/>'
                   f'<animate attributeName="y2" values="{v}" dur="{dur}s" repeatCount="indefinite"/></line>')
    g = f'<g stroke="{color}" stroke-width="1.4" mask="url(#gridFade)">' + "".join(out) + "</g>"
    if flip:
        g = f'<g transform="translate(0,{horizon*2}) scale(1,-1)">{g}</g>'
    return g


def stars(n, w, h, seed=7):
    rnd = random.Random(seed)
    s = []
    for _ in range(n):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.choice([0.6, 0.9, 1.2, 1.6])
        d = rnd.uniform(2, 5)
        b = rnd.uniform(0, 4)
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#fff">'
                 f'<animate attributeName="opacity" values="0.15;1;0.15" dur="{d:.1f}s" begin="{b:.1f}s" repeatCount="indefinite"/></circle>')
    return "".join(s)


# ================================ HEADER ================================
def header():
    W, H, HZ = 1200, 420, 285
    cx = W / 2
    sun_r = 125
    stripes = "".join(
        f'<rect x="0" y="{HZ - 70 + i*14 + i*i*0.6:.1f}" width="{W}" height="{2 + i*1.6:.1f}" fill="#000"/>'
        for i in range(6))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#03040a"/><stop offset="0.62" stop-color="#160b33"/><stop offset="0.68" stop-color="#2a0f4f"/><stop offset="1" stop-color="#05060d"/>
  </linearGradient>
  <linearGradient id="sun" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{CYAN}"/><stop offset="0.55" stop-color="{VIOLET}"/><stop offset="1" stop-color="{PINK}"/>
  </linearGradient>
  <linearGradient id="face" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#ffffff"/><stop offset="0.5" stop-color="#cffafe"/><stop offset="1" stop-color="{CYAN}"/>
  </linearGradient>
  <linearGradient id="fadeG" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.25" stop-color="#fff" stop-opacity="0.55"/><stop offset="1" stop-color="#fff" stop-opacity="1"/>
  </linearGradient>
  <mask id="gridFade"><rect x="0" y="{HZ}" width="{W}" height="{H-HZ}" fill="url(#fadeG)"/></mask>
  <mask id="sunMask"><rect width="{W}" height="{H}" fill="#fff"/>{stripes}<rect x="0" y="{HZ}" width="{W}" height="{H}" fill="#000"/></mask>
  <radialGradient id="halo" cx="0.5" cy="0.5" r="0.5"><stop offset="0" stop-color="{VIOLET}" stop-opacity="0.55"/><stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></radialGradient>
  <linearGradient id="hzline" x1="0" x2="1"><stop offset="0" stop-color="{PINK}" stop-opacity="0"/><stop offset="0.5" stop-color="{PINK}"/><stop offset="1" stop-color="{PINK}" stop-opacity="0"/></linearGradient>
  {glow_filter("glow", 3)}
  {glow_filter("bigglow", 7)}
</defs>
<rect width="{W}" height="{H}" fill="url(#sky)"/>
{stars(90, W, HZ - 30)}
<ellipse cx="{cx}" cy="{HZ-40}" rx="360" ry="190" fill="url(#halo)"/>
<circle cx="{cx}" cy="{HZ-12}" r="{sun_r}" fill="url(#sun)" mask="url(#sunMask)" opacity="0.92"/>
<rect x="0" y="{HZ}" width="{W}" height="{H-HZ}" fill="#05060d"/>
{perspective_grid(-200, W+200, HZ, H, cx, CYAN)}
<rect x="0" y="{HZ-1.5}" width="{W}" height="3" fill="url(#hzline)" filter="url(#bigglow)"/>
{wire_anim(CUBE_V, CUBE_E, 1040, 140, 52, 10, CYAN)}
{wire_anim(OCTA_V, OCTA_E, 160, 140, 46, 12, PINK, reverse=True)}
<g filter="url(#glow)">
{extruded_text(cx, 150, "ARPIT KUMAR", 96, SANS, 900, 16, "url(#face)", "#6d28d9", "#1e1b4b", dx=0.9, dy=1.1)}
</g>
<g>
  <rect x="{cx-300}" y="187" width="600" height="40" rx="20" fill="#0D1117" fill-opacity="0.78" stroke="{CYAN}" stroke-opacity="0.6"/>
  <text x="{cx-282}" y="214" font-family="{MONO}" font-size="19" fill="{CYAN}">&gt;</text>
  <text x="{cx-262}" y="214" font-family="{MONO}" font-size="19" fill="#E6EDF3">data_analyst <tspan fill="{PINK}">||</tspan> ml_engineer.<tspan fill="{CYAN}">in_progress</tspan>()</text>
  <rect x="{cx+262}" y="198" width="11" height="20" fill="{CYAN}"><animate attributeName="opacity" values="1;1;0;0" dur="1s" repeatCount="indefinite"/></rect>
</g>
</svg>'''
    write("header.svg", svg)


# ================================ SECTION SLABS ================================
def iso_cube(x, y, s, top, left, right):
    """Small solid isometric cube icon; (x,y) = top vertex."""
    h = s * 0.5
    return (f'<polygon points="{x},{y} {x+s},{y+h} {x},{y+2*h} {x-s},{y+h}" fill="{top}"/>'
            f'<polygon points="{x-s},{y+h} {x},{y+2*h} {x},{y+2*h+s} {x-s},{y+h+s}" fill="{left}"/>'
            f'<polygon points="{x+s},{y+h} {x},{y+2*h} {x},{y+2*h+s} {x+s},{y+h+s}" fill="{right}"/>')


def section(name, cmd, accent=CYAN):
    W, H = 940, 96
    depth = 9
    slab = []
    for i in range(depth, 0, -1):
        c = mix(VIOLET, "#1e1b4b", i / depth)
        slab.append(f'<rect x="{12+i}" y="{14+i}" width="{W-40}" height="58" rx="12" fill="{c}"/>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="front" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1b2333"/><stop offset="1" stop-color="#0D1117"/></linearGradient>
  <linearGradient id="shine" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="#fff" stop-opacity="0.13"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <clipPath id="clip"><rect x="12" y="14" width="{W-40}" height="58" rx="12"/></clipPath>
  {glow_filter("glow", 2.2)}
</defs>
<ellipse cx="{W/2}" cy="{H-8}" rx="{W/2-40}" ry="6" fill="#000" opacity="0.55"/>
{''.join(slab)}
<rect x="12" y="14" width="{W-40}" height="58" rx="12" fill="url(#front)" stroke="{accent}" stroke-width="1.6"/>
<g clip-path="url(#clip)"><rect x="-200" y="0" width="160" height="{H}" fill="url(#shine)" transform="skewX(-20)">
  <animate attributeName="x" values="-260;{W+200}" dur="4.5s" repeatCount="indefinite"/></rect></g>
<g transform="translate(0,2)">{iso_cube(52, 26, 18, accent, "#5b21b6", "#312e81")}</g>
<text x="86" y="53" font-family="{MONO}" font-size="26" font-weight="700" fill="{PINK}" filter="url(#glow)">&gt;</text>
<g filter="url(#glow)">{extruded_text(112, 53, cmd, 26, MONO, 700, 4, "#F0F6FC", VIOLET, "#2e1065", anchor="start")}</g>
<rect x="{112 + len(cmd)*15.7 + 8:.0f}" y="33" width="13" height="24" fill="{accent}"><animate attributeName="opacity" values="1;1;0;0" dur="1s" repeatCount="indefinite"/></rect>
<circle cx="{W-58}" cy="43" r="5" fill="#ff5f57"/><circle cx="{W-78}" cy="43" r="5" fill="#febc2e"/><circle cx="{W-98}" cy="43" r="5" fill="#28c840"/>
</svg>'''
    write(f"sec-{name}.svg", svg)


# ================================ PROJECT CARDS ================================
def chips(x, y, items):
    out, cx = [], x
    for it in items:
        w = len(it) * 8.6 + 22
        out.append(f'<rect x="{cx}" y="{y}" width="{w:.0f}" height="26" rx="13" fill="#1e1b4b" stroke="{VIOLET}"/>'
                   f'<text x="{cx + w/2:.0f}" y="{y+18}" font-family="{MONO}" font-size="13" fill="#C4B5FD" text-anchor="middle">{esc(it)}</text>')
        cx += w + 8
    return "".join(out)


def card(name, title, lines, metric, metric_label, stack, W=460, H=300, tilt=0, accent=CYAN, body_y=150):
    depth = 12
    cw, ch = W - 40, H - 46
    ext = []
    for i in range(depth, 0, -1):
        ext.append(f'<rect x="{14+i*0.9:.1f}" y="{12+i:.1f}" width="{cw}" height="{ch}" rx="16" fill="{mix(VIOLET, "#140f2e", i/depth)}"/>')
    body = "".join(f'<text x="38" y="{body_y + k*22}" font-family="{SANS}" font-size="15" fill="#C9D1D9">{esc(l)}</text>'
                   for k, l in enumerate(lines))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="cf" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1c2436"/><stop offset="1" stop-color="#0b0f17"/></linearGradient>
  <linearGradient id="mf" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="{accent}"/></linearGradient>
  <linearGradient id="edge" x1="0" x2="1"><stop offset="0" stop-color="{accent}"/><stop offset="1" stop-color="{PINK}"/></linearGradient>
  <linearGradient id="shine" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="#fff" stop-opacity="0.09"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <clipPath id="cc"><rect x="14" y="12" width="{cw}" height="{ch}" rx="16"/></clipPath>
  {glow_filter("glow", 2.5)}
</defs>
<g transform="rotate({tilt} {W/2} {H/2})">
<ellipse cx="{W/2+6}" cy="{H-14}" rx="{W/2-30}" ry="9" fill="#000" opacity="0.6"/>
{''.join(ext)}
<rect x="14" y="12" width="{cw}" height="{ch}" rx="16" fill="url(#cf)" stroke="url(#edge)" stroke-width="2"/>
<g clip-path="url(#cc)"><rect x="-300" y="0" width="180" height="{H}" fill="url(#shine)" transform="skewX(-20)">
  <animate attributeName="x" values="-300;{W+300}" dur="6s" repeatCount="indefinite"/></rect></g>
<text x="38" y="58" font-family="{SANS}" font-size="23" font-weight="800" fill="#F0F6FC">{esc(title)}</text>
<rect x="38" y="70" width="60" height="3" rx="1.5" fill="{accent}" filter="url(#glow)"/>
<g filter="url(#glow)">{extruded_text(W-46, 116, metric, 34, SANS, 900, 5, "url(#mf)", VIOLET, "#1e1b4b", anchor="end")}</g>
<text x="{W-46}" y="134" font-family="{MONO}" font-size="11" fill="#8B949E" text-anchor="end">{esc(metric_label)}</text>
<g transform="translate(0,10)">{body}</g>
{chips(38, ch - 34, stack)}
</g>
</svg>'''
    write(f"card-{name}.svg", svg)


def reveal(b):
    """Fade in at time b; stays visible if animation is unsupported."""
    t = b + 0.25
    return (f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{b/t:.3f};1" '
            f'dur="{t:.2f}s" begin="0s" fill="freeze"/>')


# ================================ ACHIEVEMENTS TERMINAL ================================
def terminal():
    W, H = 940, 350
    rows = [
        ("2026", "Selected", "Amazon ML Summer School 2026"),
        ("2026", "Finalist", "India Innovates 2026"),
        ("2026", "Finalist", "Stellar Analytics Hackathon (IIT BHU)"),
        ("2026", "Finalist", "KnowledgeQuarry (CIC, University of Delhi)"),
        ("2025", "Track Winner", "CodeSlayer 2k25 (Devsphere India)"),
        ("2025", "Paper", "ICAIN-2025, BITS Dubai: Neuro-symbolic AI Systems"),
        ("----", "HackerRank", "SQL Gold Badge  ·  Python Silver Badge"),
    ]
    depth = 12
    ext = "".join(f'<rect x="{12+i*0.9:.1f}" y="{10+i:.1f}" width="{W-40}" height="{H-40}" rx="14" fill="{mix(VIOLET, "#140f2e", i/depth)}"/>'
                  for i in range(depth, 0, -1))
    lines = []
    for k, (yr, kind, what) in enumerate(rows):
        y = 104 + k * 29
        b = 0.4 + k * 0.35
        star = "★ " if kind in ("Selected", "Track Winner", "HackerRank") else ""
        lines.append(
            f'<g>{reveal(b)}'
            f'<text x="40" y="{y}" font-family="{MONO}" font-size="16" xml:space="preserve">'
            f'<tspan fill="#3FB950">+</tspan><tspan fill="#8B949E"> [{yr}] </tspan>'
            f'<tspan fill="{CYAN}" font-weight="700">{esc(kind):<13}</tspan>'
            f'<tspan fill="#E6EDF3">{esc(star + what)}</tspan></text></g>')
    end_b = 0.4 + len(rows) * 0.35
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="tf" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#161b22"/><stop offset="1" stop-color="#0b0f17"/></linearGradient>
  <linearGradient id="edge" x1="0" x2="1"><stop offset="0" stop-color="{CYAN}"/><stop offset="1" stop-color="{PINK}"/></linearGradient>
  <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#fff" opacity="0.025"/></pattern>
  {glow_filter("glow", 2)}
</defs>
<ellipse cx="{W/2}" cy="{H-12}" rx="{W/2-30}" ry="9" fill="#000" opacity="0.6"/>
{ext}
<rect x="12" y="10" width="{W-40}" height="{H-40}" rx="14" fill="url(#tf)" stroke="url(#edge)" stroke-width="2"/>
<path d="M12,48 h{W-40}" stroke="#30363d"/>
<circle cx="38" cy="29" r="6" fill="#ff5f57"/><circle cx="58" cy="29" r="6" fill="#febc2e"/><circle cx="78" cy="29" r="6" fill="#28c840"/>
<text x="{W/2-14}" y="34" font-family="{MONO}" font-size="13" fill="#8B949E" text-anchor="middle">arpit@github: ~/achievements — zsh</text>
<text x="40" y="74" font-family="{MONO}" font-size="16" fill="#E6EDF3"><tspan fill="{PINK}">❯</tspan> git log <tspan fill="{CYAN}">--achievements</tspan> <tspan fill="#8B949E">--oneline</tspan></text>
<g filter="url(#glow)">{''.join(lines)}</g>
<g>{reveal(end_b)}
<text x="40" y="{104 + len(rows)*29}" font-family="{MONO}" font-size="16" fill="{PINK}">❯</text>
<rect x="58" y="{104 + len(rows)*29 - 15}" width="10" height="19" fill="{CYAN}"><animate attributeName="opacity" values="1;1;0;0" dur="1s" repeatCount="indefinite"/></rect></g>
<rect x="12" y="10" width="{W-40}" height="{H-40}" rx="14" fill="url(#scan)"/>
</svg>'''
    write("achievements.svg", svg)


# ================================ FOOTER ================================
def footer():
    W, H, HZ = 1200, 230, 95
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#05060d" stop-opacity="0"/><stop offset="0.35" stop-color="#160b33"/><stop offset="1" stop-color="#03040a"/></linearGradient>
  <linearGradient id="fadeG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.3" stop-color="#fff" stop-opacity="0.5"/><stop offset="1" stop-color="#fff"/></linearGradient>
  <mask id="gridFade"><rect x="0" y="{HZ}" width="{W}" height="{H-HZ}" fill="url(#fadeG)"/></mask>
  <linearGradient id="face" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="{CYAN}"/></linearGradient>
  <linearGradient id="hzline" x1="0" x2="1"><stop offset="0" stop-color="{PINK}" stop-opacity="0"/><stop offset="0.5" stop-color="{PINK}"/><stop offset="1" stop-color="{PINK}" stop-opacity="0"/></linearGradient>
  {glow_filter("glow", 3)}
  {glow_filter("bigglow", 7)}
</defs>
<rect width="{W}" height="{H}" fill="url(#sky)"/>
{perspective_grid(-200, W+200, HZ, H, W/2, VIOLET, lines=16, dur=2.8)}
<rect x="0" y="{HZ-1.5}" width="{W}" height="3" fill="url(#hzline)" filter="url(#bigglow)"/>
<g filter="url(#glow)">{extruded_text(W/2, 70, "</EOF>", 46, MONO, 800, 8, "url(#face)", "#6d28d9", "#1e1b4b")}</g>
</svg>'''
    write("footer.svg", svg)


if __name__ == "__main__":
    header()
    for n, c in [("whoami", "whoami"), ("stack", "ls ~/tech-stack"), ("projects", "cat ./featured_projects.log"),
                 ("achievements", "git log --achievements"), ("stats", "./github_stats.sh --live"),
                 ("contrib", "render --3d ./contributions"), ("connect", "ping arpit --connect")]:
        section(n, c)
    card("ipl", "IPL Auction Strategy",
         ["Strike rates, consistency, venue impact &", "toss analysis across IPL 2008–2016 →",
          "data-driven RCB auction recommendations."],
         "9 SEASONS", "of ball-by-ball data", ["SQL"], tilt=-1.5)
    card("churn", "Airline Loyalty Churn Model",
         ["Churn prediction across 12 customer", "segments, flagging 165 high-risk",
          "customers from 48M+ loyalty records."],
         "$776K", "at-risk CLV flagged", ["SQL", "Python", "sklearn", "Power BI"], tilt=1.5, accent=PINK)
    card("zomato", "Zomato Market Expansion Dashboard",
         ["Analyzed 9,542 restaurants across 15 markets to surface",
          "12+ high-potential expansion cities."],
         "9,542", "restaurants analyzed", ["Excel", "Pivot Tables"], W=940, H=240, body_y=100)
    terminal()
    footer()
    print("ok")
