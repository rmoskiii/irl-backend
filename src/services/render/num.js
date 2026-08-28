'use strict';

/** printf("%g") — the Python composer formats transforms and tail geometry with
 *  `:g`, so the port has to match it exactly or every transform string differs. */
function g(x, sig = 6) {
    if (!Number.isFinite(x)) return String(x);
    if (x === 0) return '0';
    const exp = Math.floor(Math.log10(Math.abs(x)));
    let s;
    if (exp < -4 || exp >= sig) {
        s = x.toExponential(sig - 1).replace(/\.?0+e/, 'e').replace(/e([+-])(\d)$/, 'e$10$2');
    } else {
        s = x.toFixed(Math.max(0, sig - 1 - exp));
        if (s.includes('.')) s = s.replace(/\.?0+$/, '');
    }
    return s;
}

/** Python str(float): keeps a trailing .0 on integral floats, unlike JS. */
function pyFloat(x) {
    return Number.isInteger(x) ? `${x}.0` : String(x);
}
module.exports = { g, pyFloat };