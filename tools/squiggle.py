#!/usr/bin/env python3
"""
Generate the hand-drawn ("squiggly") panel outline images used by the
Sticker Book Mainsail theme, in any colours you like.

Each panel in the theme is drawn with two 9-slice `border-image`s:
  --sq-fill / --sq-fill-flat : wobbly panel fill + the same shape offset 4px (the hard shadow)
  --sq-line / --sq-line-flat : the wobbly outline on top
The "-flat" versions have straight sides and are used for collapsed panels,
which are too short to stretch the wobble nicely.

Usage:
  python3 tools/squiggle.py --outline "#2b2340" --shadow "#2b2340" --card "#ffffff"

It prints four CSS custom properties. Paste them into the matching
`.v-application.theme--light { ... }` or `.v-application.theme--dark { ... }`
block in custom.css, replacing the existing --sq-* lines.

Defaults reproduce the light theme. The dark theme uses:
  --outline "#f3e6cf" --shadow "#0e0b16" --card "#2a2338"

No dependencies beyond the Python 3 standard library.
"""
import argparse

# Tile geometry (CSS uses: inset -8px, border 30px, slice 30)
T, M, R, S = 80, 8, 18, 30          # tile size, panel-edge margin, corner radius, slice
A, B = M, T - M                      # panel edges inside the tile (8 .. 72)
C0, C1 = M + R, T - M - R            # where corner arcs meet the edges (26, 54)
S0, S1 = S, T - S - 4                # wobble zone (30 .. 46); the shadow copy lands in 34 .. 50

# Outward-positive offsets (px) for the bumps on each edge — irregular on purpose.
TOP    = [0, 1.5, -1.1, 1.7, -0.6, 1.2, -1.4, 0]
RIGHT  = [0, -1.3, 1.6, -0.5, 1.4, -1.6, 0.9, 0]
BOTTOM = [0, 1.2, -1.6, 0.8, 1.5, -1.0, 1.3, 0]
LEFT   = [0, -1.5, 0.9, 1.6, -1.2, 0.7, -1.4, 0]


def wobble(p0, p1, offs, normal):
    """Smooth curve (Catmull-Rom as cubic Béziers) from p0 to p1 through evenly
    spaced points pushed along `normal` by `offs`."""
    n = len(offs) - 1
    pts = [(p0[0] + (p1[0] - p0[0]) * i / n + normal[0] * o,
            p0[1] + (p1[1] - p0[1]) * i / n + normal[1] * o) for i, o in enumerate(offs)]
    d = (p1[0] - p0[0], p1[1] - p0[1])
    ext = [(pts[0][0] - d[0] / n, pts[0][1] - d[1] / n)] + pts + [(pts[-1][0] + d[0] / n, pts[-1][1] + d[1] / n)]
    out = []
    for i in range(1, len(ext) - 2):
        p_, a, b, q = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        c1 = (a[0] + (b[0] - p_[0]) / 6, a[1] + (b[1] - p_[1]) / 6)
        c2 = (b[0] - (q[0] - a[0]) / 6, b[1] - (q[1] - a[1]) / 6)
        out.append('C%.2f %.2f %.2f %.2f %.2f %.2f' % (*c1, *c2, *b))
    return ' '.join(out)


def path(flat_sides=False):
    right = [0] * len(RIGHT) if flat_sides else RIGHT
    left = [0] * len(LEFT) if flat_sides else LEFT
    d = 'M%d %d A17 19 0 0 1 %d %d L%d %d ' % (A, C0, C0, A, S0, A)
    d += wobble((S0, A), (S1, A), TOP, (0, -1)) + ' L%d %d A19 17 0 0 1 %d %d L%d %d ' % (C1, A, B, C0, B, S0)
    d += wobble((B, S0), (B, S1), right, (1, 0)) + ' L%d %d A18 16 0 0 1 %d %d L%d %d ' % (B, C1, C1, B, S1, B)
    d += wobble((S1, B), (S0, B), BOTTOM, (0, 1)) + ' L%d %d A16 18 0 0 1 %d %d L%d %d ' % (C0, B, A, C1, A, S1)
    d += wobble((A, S1), (A, S0), left, (-1, 0)) + ' Z'
    return d


HEAD = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 %d %d' width='%d' height='%d'>" % (T, T, T, T)


def data_uri(svg):
    return 'url("data:image/svg+xml,' + (svg.replace('%', '%25').replace('#', '%23')
                                          .replace('<', '%3C').replace('>', '%3E')) + '")'


def line_svg(d, outline):
    return HEAD + ("<path d='%s' fill='none' stroke='%s' stroke-width='3' "
                   "stroke-linejoin='round'/></svg>") % (d, outline)


def fill_svg(d, shadow, card):
    return HEAD + ("<path d='%s' transform='translate(4 4)' fill='%s'/>"
                   "<path d='%s' fill='%s'/></svg>") % (d, shadow, d, card)


def squiggles(outline, shadow, card):
    wobbly, flat = path(), path(flat_sides=True)
    return {
        'fill': data_uri(fill_svg(wobbly, shadow, card)),
        'line': data_uri(line_svg(wobbly, outline)),
        'fill-flat': data_uri(fill_svg(flat, shadow, card)),
        'line-flat': data_uri(line_svg(flat, outline)),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument('--outline', default='#2b2340', help='outline colour (default: light theme ink)')
    ap.add_argument('--shadow', default='#2b2340', help='hard shadow colour')
    ap.add_argument('--card', default='#ffffff', help='panel fill colour (match --card in custom.css)')
    ap.add_argument('--svg', metavar='DIR', help='also write the four SVGs to DIR for previewing')
    args = ap.parse_args()

    sq = squiggles(args.outline, args.shadow, args.card)
    pad = {'fill': 6, 'line': 6, 'fill-flat': 1, 'line-flat': 1}
    for name, value in sq.items():
        print('  --sq-%s:%s%s;' % (name, ' ' * pad[name], value))

    if args.svg:
        import os
        os.makedirs(args.svg, exist_ok=True)
        wobbly, flat = path(), path(flat_sides=True)
        files = {'fill.svg': fill_svg(wobbly, args.shadow, args.card), 'line.svg': line_svg(wobbly, args.outline),
                 'fill-flat.svg': fill_svg(flat, args.shadow, args.card), 'line-flat.svg': line_svg(flat, args.outline)}
        for fname, svg in files.items():
            with open(os.path.join(args.svg, fname), 'w') as f:
                f.write(svg)


if __name__ == '__main__':
    main()
