'use strict';

/** Resolves the `<style>` block into per-element presentation attributes.
 *
 *  flattenTokens fixed `var(--irx-*)`; this fixes the other half. The fills
 *  live in CSS class rules (`.cab { fill: ... }`) inside a `<style>` element
 *  nested in `<defs>`, and flutter_svg resolves neither the selector nor the
 *  nesting - so every path falls back to default fill, which is black. That is
 *  the black 16:9 box.
 *
 *  Inline presentation attributes are the lowest common denominator: every SVG
 *  renderer in existence supports them. So delivery emits those, and the
 *  composition keeps its stylesheet, which is what the fixtures assert.
 *
 *  Only styling is touched. Geometry attributes are never written.
 */
const STYLED = new Set([
    'fill', 'stroke', 'stroke-width', 'stroke-linecap', 'stroke-linejoin',
    'stroke-dasharray', 'stroke-opacity', 'fill-opacity', 'opacity',
    'font-family', 'font-size', 'font-weight', 'letter-spacing', 'text-anchor',
    'mix-blend-mode', 'filter',
]);

/** Parses `.a, .b { prop: val; }` rules. Deliberately only class selectors:
 *  the asset set uses nothing else, and quietly mis-handling a selector we do
 *  not use would be worse than refusing to see it. */
function parseRules(css) {
    const rules = new Map();
    const body = css.replace(/\/\*[\s\S]*?\*\//g, '');
    for (const m of body.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
        const selectors = m[1].split(',').map(s => s.trim());
        const decls = {};
        for (const d of m[2].split(';')) {
            const i = d.indexOf(':');
            if (i < 0) continue;
            const prop = d.slice(0, i).trim();
            const val = d.slice(i + 1).trim();
            if (STYLED.has(prop) && val) decls[prop] = val;
        }
        if (!Object.keys(decls).length) continue;
        for (const sel of selectors) {
            if (!/^\.[\w-]+$/.test(sel)) continue;          // class selectors only
            const name = sel.slice(1);
            rules.set(name, { ...(rules.get(name) || {}), ...decls });
        }
    }
    return rules;
}

function collectCss(svg) {
    let css = '';
    for (const m of svg.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)) css += m[1] + '\n';
    return css;
}

function serialiseAttrs(attrs) {
    return Object.entries(attrs)
        .map(([k, v]) => `${k}="${String(v).replace(/"/g, '&quot;')}"`)
        .join(' ');
}

/** Rewrites every element carrying a `class`, merging the class declarations
 *  into its attributes and dropping the class. CSS wins over a presentation
 *  attribute of the same name, which is what the cascade does — inlining must
 *  not silently change which value applies. */
function inlineStyles(svg) {
    const rules = parseRules(collectCss(svg));
    if (rules.size === 0) return stripStyle(svg);

    const out = svg.replace(/<([\w:-]+)((?:\s+[\w:-]+\s*=\s*"[^"]*")*)\s*(\/?)>/g,
        (whole, tag, attrText, selfClose) => {
            const attrs = {};
            for (const a of attrText.matchAll(/([\w:-]+)\s*=\s*"([^"]*)"/g)) attrs[a[1]] = a[2];
            const cls = attrs.class;
            if (!cls) return whole;
            delete attrs.class;
            for (const name of cls.split(/\s+/).filter(Boolean)) {
                Object.assign(attrs, rules.get(name) || {});
            }
            const s = serialiseAttrs(attrs);
            return `<${tag}${s ? ' ' + s : ''}${selfClose ? ' /' : ''}>`;
        });

    return stripStyle(out);
}

/** The stylesheet has done its job by this point and every renderer would have
 *  to parse it for nothing. */
function stripStyle(svg) {
    return svg.replace(/<style[^>]*>[\s\S]*?<\/style>/g, '')
        .replace(/<defs>\s*<\/defs>/g, '');
}

module.exports = { inlineStyles, parseRules };