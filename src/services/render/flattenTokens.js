'use strict';

/** Resolves `var(--irx-*)` to literal colours for client delivery.
 *
 *  WHY THIS IS NOT IN composeFrame: the composed SVG is the signed-off 2B
 *  composition and the fixtures assert it exactly. Flattening there would
 *  change every fill attribute and break Level 2 parity for a reason that has
 *  nothing to do with composition. So composition stays canonical and delivery
 *  adapts - the split the port was designed around.
 *
 *  WHY IT IS NEEDED: flutter_svg does not resolve CSS custom properties, the
 *  same limitation that made cairosvg render every frame as a black rectangle
 *  during the 2B audit. Unflattened, the client gets an unstyled silhouette.
 *
 *  SAFETY: verified across all 41 composed frames during 2B - `var()` appears
 *  only in `fill` and `stroke`, in zero geometry attributes (d, x, y, cx, cy,
 *  r, width, height, transform, points, viewBox). Substitution therefore
 *  cannot move a single path. assertGeometryUnchanged() re-checks that per
 *  call rather than trusting the historical result.
 */
const TOKEN_RE = /var\(\s*(--[\w-]+)\s*(?:,\s*([^)]*))?\)/g;

function readTokens(svg) {
    const root = /:root\s*\{([^}]*)\}/.exec(svg);
    if (!root) return {};
    const out = {};
    for (const m of root[1].matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) {
        out[m[1]] = m[2].trim();
    }
    return out;
}

const GEOMETRY = /\s(d|x|y|x1|y1|x2|y2|cx|cy|r|rx|ry|width|height|transform|points|viewBox|offset)\s*=\s*"[^"]*var\(/;

function assertGeometryUnchanged(svg) {
    if (GEOMETRY.test(svg)) {
        throw new Error('flattenTokens: a geometry attribute references var() - ' +
            'refusing to substitute, since this could move artwork');
    }
}

/** Returns the SVG with every var() reference replaced by its literal value.
 *  Unknown tokens fall back to their declared fallback, then to magenta, which
 *  is deliberately hideous: a missing token should be obvious on screen, not
 *  quietly rendered as black. */
function flattenTokens(svg) {
    assertGeometryUnchanged(svg);
    const tokens = readTokens(svg);
    let out = svg;
    for (let pass = 0; pass < 6; pass++) {          // tokens may reference tokens
        const next = out.replace(TOKEN_RE, (_, name, fallback) =>
            tokens[name] !== undefined ? tokens[name] : (fallback || '#FF00FF').trim());
        if (next === out) break;
        out = next;
    }
    return out;
}

module.exports = { flattenTokens, readTokens };