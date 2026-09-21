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

/** Every :root block in the frame, FIRST definition wins, then `base`.
 *
 *  A composed frame carries one :root per distinct token block among its
 *  assets. Reading only the first meant a character could only resolve its
 *  colours if the ENVIRONMENT happened to define them: scene.block.svg carries
 *  a 50-token block, so every Streets figure on the walkway went magenta while
 *  the same figure in the kitchen (144 tokens) was fine. First-wins keeps every
 *  value that resolved before this change byte-identical; the later blocks and
 *  tokens.css only fill names that were previously unresolved. */
function readTokens(svg, base = {}) {
    const out = {};
    for (const root of svg.matchAll(/:root\s*\{([^}]*)\}/g)) {
        for (const m of root[1].matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) {
            if (out[m[1]] === undefined) out[m[1]] = m[2].trim();
        }
    }
    for (const [k, v] of Object.entries(base)) if (out[k] === undefined) out[k] = v;
    return out;
}

/** The canonical token sheet as a map, for readTokens' last-resort fill. */
function loadBaseTokens(tokensCssPath) {
    const fs = require('fs');
    if (!tokensCssPath || !fs.existsSync(tokensCssPath)) return {};
    return readTokens(fs.readFileSync(tokensCssPath, 'utf8'));
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
function flattenTokens(svg, baseTokens) {
    assertGeometryUnchanged(svg);
    const tokens = readTokens(svg, baseTokens);
    let out = svg;
    for (let pass = 0; pass < 6; pass++) {          // tokens may reference tokens
        const next = out.replace(TOKEN_RE, (_, name, fallback) =>
            tokens[name] !== undefined ? tokens[name] : (fallback || '#FF00FF').trim());
        if (next === out) break;
        out = next;
    }
    return out;
}

module.exports = { loadBaseTokens, flattenTokens, readTokens };