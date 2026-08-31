'use strict';

/** Removes paint the client renderer cannot resolve.
 *
 *  flutter_svg supports linear and radial gradients but not `<pattern>` and
 *  not `<filter>`. Every environment carries one of each: a wallpaper or tile
 *  pattern at low opacity, and an feTurbulence grain rect over the whole
 *  canvas. An unresolvable `url(#…)` paint is enough to take the frame down,
 *  which is why the montage rendered and every room did not - the montage is
 *  flat fills and has neither.
 *
 *  Both are texture overlays, not structure. Removing them costs a little
 *  surface grain and nothing else; the wallpaper sits at opacity 0.4 over a
 *  wall that is already the right colour, and the grain at 0.10. Gradients
 *  survive, so the vignette, keylight and cool spill - which do most of the
 *  atmospheric work - are untouched.
 *
 *  The whole ELEMENT goes, not just the attribute. Stripping `filter` from a
 *  full-canvas rect would leave a flat rect covering the scene; stripping a
 *  pattern fill would leave it black. Removing the element is the only
 *  correct simplification.
 */
const SUPPORTED_PAINT = new Set(['linearGradient', 'radialGradient', 'clipPath', 'mask']);

function defKinds(svg) {
    const kinds = {};
    for (const m of svg.matchAll(
        /<(pattern|filter|radialGradient|linearGradient|mask|clipPath)\b[^>]*id="([^"]+)"/g)) {
        kinds[m[2]] = m[1];
    }
    return kinds;
}

/** ids whose definition the client cannot use */
function unsupportedIds(svg) {
    const kinds = defKinds(svg);
    return new Set(Object.entries(kinds)
        .filter(([, kind]) => !SUPPORTED_PAINT.has(kind))
        .map(([id]) => id));
}

function simplifyForClient(svg) {
    const bad = unsupportedIds(svg);
    if (bad.size === 0) return svg;

    const referencesBad = (tagText) => {
        for (const m of tagText.matchAll(/url\(#([^")]+)\)/g)) {
            if (bad.has(m[1])) return true;
        }
        return false;
    };

    // self-closing and empty-content elements only; every consumer of these
    // defs in the asset set is a single <path> or <rect> overlay
    let out = svg.replace(/<([\w:-]+)([^>]*?)\/>/g,
        (whole, tag, attrs) => (referencesBad(attrs) ? '' : whole));

    out = out.replace(/<([\w:-]+)([^>]*?)>\s*<\/\1>/g,
        (whole, tag, attrs) => (referencesBad(attrs) ? '' : whole));

    // drop the now-unreferenced definitions
    for (const id of bad) {
        out = out.replace(
            new RegExp(`<(pattern|filter)\\b[^>]*id="${id}"[\\s\\S]*?</\\1>`, 'g'), '');
    }
    return out.replace(/<defs>\s*<\/defs>/g, '');
}

module.exports = { simplifyForClient, unsupportedIds };