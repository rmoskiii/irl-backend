/* The three approved context additions to The Streets, applied in place.
 * Run once from the irl-backend repo root:  node apply-streets-context.js
 * Then delete this file. Idempotent: a second run changes nothing.
 *
 * Edits the raw JSON text rather than re-serialising it, so the diff is only
 * the three additions and the revision bump - no reformatting, and no chance
 * of the double-escaping that a hand paste introduced last time. */
const fs = require('fs');
const path = 'src/data/scenarios/the_streets.json';

let raw = fs.readFileSync(path, 'utf8');
const before = raw;
// JSON-escape a string exactly as it appears inside the file (em dashes and
// curly quotes stay literal, as the file already has them)
const esc = s => JSON.stringify(s).slice(1, -1);

const edits = [
    {
        name: 'Tunde - s1d1_walkway',
        find: esc("Tunde's message arrives while Jay is talking. *Cage, eight. You coming or not.*"),
        add:  esc("\n\nTunde trains most nights. He asks direct questions, too."),
    },
    {
        name: 'Kai - s1d3_stop',
        find: esc("and his phone is up, and it has been up since about the second sentence."),
        add:  esc(" He isn't filming this for himself. The three or four are why the phone is up."),
    },
];

for (const e of edits) {
    if (raw.includes(e.find + e.add)) { console.log(`already applied: ${e.name}`); continue; }
    const n = raw.split(e.find).length - 1;
    if (n !== 1) throw new Error(`${e.name}: expected 1 match, found ${n} - nothing written`);
    raw = raw.replace(e.find, e.find + e.add);
    console.log(`applied: ${e.name}`);
}

// Amara - a narration segment in the day-1 thread, after the line that says
// her two messages went unanswered. Matched on that segment plus the one that
// follows it, so it cannot land in the day-3 thread, which repeats her texts.
{
    const name = 'Amara - s1d1_close thread';
    const anchorRe = /(\{\s*"narration":\s*"Twenty minutes between them\. You haven't answered either\."\s*\},)(\s*)(\{\s*"narration":\s*"And a number you don't have saved\.")/;
    const seg = '{\n          "narration": "Amara asks once and leaves it with you. She doesn\'t ask twice."\n        },';
    if (raw.includes("Amara asks once and leaves it with you.")) {
        console.log(`already applied: ${name}`);
    } else {
        const m = raw.match(anchorRe);
        if (!m) throw new Error(`${name}: anchor not found - nothing written`);
        raw = raw.replace(anchorRe, `$1$2${seg}$2$3`);
        console.log(`applied: ${name}`);
    }
}

// revision: content changed, so a run saved against the old text is retired
// on resume rather than replayed against prose it was not written for
raw = raw.replace(/"contentRevision": 3,/, '"contentRevision": 4,');

const parsed = JSON.parse(raw); // refuse to write anything unparseable
if (raw !== before) fs.writeFileSync(path, raw);
console.log(`contentRevision: ${parsed.contentRevision}`);