#!/usr/bin/env node
/* IRX scenario validator.
 *
 * Build-time only. Nothing here runs in the service, and nothing here is
 * required by the service. Two layers, per SPEC v1.1:
 *
 *   Layer A  static structural  - single pass, no traversal, runs on save
 *   Layer B  graph + state      - reachability and state simulation, on commit
 *
 * Layer B drives the REAL engine (evaluationService.resolveChoice) rather than
 * reimplementing setState/derivedState/matcher semantics. A validator that
 * models the engine is a second engine, and the two drift. This one cannot.
 *
 * Rule profiles
 *   baseline  correctness rules that hold for any scenario, any district
 *   streets   baseline + the SPEC v1.1 authoring policy for The Streets
 *
 * The split is not cosmetic. the_instruction.json legitimately carries five
 * raw-integer `when` references and three nodes above the 3-variant cap. Those
 * are Streets policy rules the Career scenario predates and was never bound by;
 * the engine handles both correctly. Applying them universally would fail a
 * shipped scenario, which SPEC v1.1 forbids.
 *
 *   node tools/validate_scenario.js                    all scenarios, baseline
 *   node tools/validate_scenario.js the_streets        one scenario
 *   node tools/validate_scenario.js --profile=streets  force a profile
 *   node tools/validate_scenario.js --layer=a          skip simulation
 *   node tools/validate_scenario.js --json             machine-readable
 *
 * Exit 0 = no failures. Exit 1 = at least one FAIL. Warnings never fail a build
 * but are always printed and always counted.
 */

const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const SCENARIOS_DIR = path.join(ROOT, "src", "data", "scenarios");
const VISUAL_DIR = path.join(__dirname, "visual");

const FAIL = "FAIL";
const WARN = "WARN";

// Streets policy limits. Single source so a spec change is a one-line edit.
const LIMITS = {
    messageVariants: 3,
    bubblesPerNode: 3,
    bubbleChars: 120,
    bubbleNodes: 8,
    montagePanels: 3,
    captionChars: 40,
    exitBeats: 1,
    nativeChars: 700,
    complementClauses: 3,
    finalDay: 7,
};

// ---------------------------------------------------------------- findings

class Report {
    constructor() {
        this.findings = [];
    }

    add(severity, rule, scenario, where, message) {
        this.findings.push({ severity, rule, scenario, where, message });
    }

    fail(rule, scenario, where, message) {
        this.add(FAIL, rule, scenario, where, message);
    }

    warn(rule, scenario, where, message) {
        this.add(WARN, rule, scenario, where, message);
    }

    get failures() {
        return this.findings.filter((f) => f.severity === FAIL);
    }

    get warnings() {
        return this.findings.filter((f) => f.severity === WARN);
    }
}

// ------------------------------------------------------------- inspection

/** Every `when` object in a scenario, with the path that reached it.
 *
 *  The engine runs one matcher (personaService.matchesAll) from six call
 *  sites - messageVariants, threadVariants, requires, nextRules, outcomeRules,
 *  and the reflection/aftermath/finalMessage pickers. A rule that binds `when`
 *  must bind all of them or it is not a rule, it is a suggestion. So this walks
 *  the whole document rather than the sites someone remembered to list.
 */
function eachWhen(scenario, visit) {
    const walk = (node, where) => {
        if (!node || typeof node !== "object") return;
        if (Array.isArray(node)) {
            node.forEach((item, i) => walk(item, `${where}[${i}]`));
            return;
        }
        for (const [key, value] of Object.entries(node)) {
            const next = where ? `${where}.${key}` : key;
            if (key === "when" && value && typeof value === "object" && !Array.isArray(value)) {
                visit(value, next);
            }
            walk(value, next);
        }
    };
    walk(scenario, "");
}

/** Every choice, with its node id. */
function eachChoice(scenario, visit) {
    for (const [nodeId, node] of Object.entries(scenario.nodes || {})) {
        (node.choices || []).forEach((choice, i) =>
            visit(choice, nodeId, node, `nodes.${nodeId}.choices[${i}]`)
        );
    }
}

function stateKeyTypes(scenario) {
    const types = {};
    for (const [key, field] of Object.entries(scenario.stateSchema || {})) {
        types[key] = field.type;
    }
    return types;
}

function derivedValues(scenario) {
    const values = {};
    for (const [key, spec] of Object.entries(scenario.derivedState || {})) {
        values[key] = new Set((spec.bands || []).map((b) => b.value));
    }
    return values;
}

function isStreets(scenario, profile) {
    return profile === "streets";
}

// ---------------------------------------------------------------- Layer A

function layerA(scenario, report, ctx) {
    const id = scenario.id;
    const types = stateKeyTypes(scenario);
    const derived = scenario.derivedState || {};
    const dValues = derivedValues(scenario);
    const nodes = scenario.nodes || {};
    const streets = isStreets(scenario, ctx.profile);

    const knownState = new Set(Object.keys(types));
    const knownDerived = new Set(Object.keys(derived));

    // outcomeKey is written into state by the engine at terminal, before
    // aftermath and finalMessage resolve, so it is a legitimate matcher key even
    // though it is not in stateSchema. resolveOutcome does this, not the author.
    const engineWritten = new Set();
    if (scenario.outcomeKey) engineWritten.add(scenario.outcomeKey);
    const written = new Set();
    const read = new Set();

    // A09 - root node exists
    if (!scenario.rootNode || !nodes[scenario.rootNode]) {
        report.fail("A09", id, "rootNode", `rootNode "${scenario.rootNode}" is not in nodes`);
    }

    // A18 - int keys declare a range, or clamping silently does nothing
    for (const [key, field] of Object.entries(scenario.stateSchema || {})) {
        if (field.type === "int" && !Array.isArray(field.range)) {
            report.fail("A18", id, `stateSchema.${key}`, "int key has no range; clamping is a no-op");
        }
        if (field.type === "enum" && !Array.isArray(field.values)) {
            report.fail("A18", id, `stateSchema.${key}`, "enum key declares no values");
        }
    }

    // A03/A04 - band sources and band ordering
    for (const [band, spec] of Object.entries(derived)) {
        for (const ref of ["from", "minus"]) {
            const key = spec[ref];
            if (key === undefined) continue;
            if (!knownState.has(key)) {
                report.fail("A03", id, `derivedState.${band}.${ref}`, `references undeclared key "${key}"`);
            } else if (types[key] !== "int") {
                report.fail(
                    "A03",
                    id,
                    `derivedState.${band}.${ref}`,
                    `references "${key}" of type ${types[key]}; band sources must be int ` +
                    `(applyDerived does arithmetic on the value)`
                );
            }
        }
        const bands = spec.bands || [];
        if (bands.length === 0) {
            report.fail("A04", id, `derivedState.${band}`, "declares no bands");
            continue;
        }
        for (let i = 1; i < bands.length; i++) {
            if (!(bands[i].min < bands[i - 1].min)) {
                report.fail(
                    "A04",
                    id,
                    `derivedState.${band}.bands[${i}]`,
                    `min ${bands[i].min} is not below the previous ${bands[i - 1].min}; ` +
                    `the engine takes the FIRST match, so an unsorted list returns the wrong band`
                );
            }
        }
        const last = bands[bands.length - 1];
        if (last.min > -999) {
            report.fail(
                "A04",
                id,
                `derivedState.${band}.bands`,
                `terminal band min is ${last.min}, not -999; values below it resolve to null`
            );
        }
    }

    // A01/A16 - setState keys and value types
    eachChoice(scenario, (choice, nodeId, node, where) => {
        for (const [key, value] of Object.entries(choice.setState || {})) {
            written.add(key);
            if (!knownState.has(key)) {
                report.fail(
                    "A01",
                    id,
                    `${where}.setState.${key}`,
                    `key is not in stateSchema; evaluationService.js:16 drops it silently`
                );
                continue;
            }
            const type = types[key];
            if (type === "int" && typeof value !== "number") {
                report.fail("A16", id, `${where}.setState.${key}`, `int key set to ${typeof value}`);
            }
            if (type === "bool" && typeof value !== "boolean") {
                report.fail("A16", id, `${where}.setState.${key}`, `bool key set to ${typeof value}`);
            }
            if (type === "enum") {
                const allowed = scenario.stateSchema[key].values || [];
                if (!allowed.includes(value)) {
                    report.fail(
                        "A16",
                        id,
                        `${where}.setState.${key}`,
                        `value ${JSON.stringify(value)} is not in the declared enum [${allowed.join(", ")}]`
                    );
                }
            }
        }

        // A05/A06/W01 - requires shape
        if ("requires" in choice) {
            if (!Array.isArray(choice.requires)) {
                report.fail("A05", id, `${where}.requires`, "requires must be an array of when objects");
            } else {
                if (choice.requires.length === 0) {
                    report.warn(
                        "W01",
                        id,
                        `${where}.requires`,
                        "empty array matches everything; usually a deleted condition"
                    );
                }
                choice.requires.forEach((clause, i) => {
                    if (!clause || typeof clause !== "object" || Array.isArray(clause)) {
                        report.fail("A05", id, `${where}.requires[${i}]`, "clause is not an object");
                    } else if (Object.keys(clause).length === 0) {
                        report.fail(
                            "A06",
                            id,
                            `${where}.requires[${i}]`,
                            "empty clause matches everything, defeating the gate"
                        );
                    }
                });
                if (choice.requires.length > LIMITS.complementClauses) {
                    report.warn(
                        "W04",
                        id,
                        `${where}.requires`,
                        `${choice.requires.length} clauses; prefer a flag or a narrower enum`
                    );
                }
            }
        }

        // A08 - routing targets exist
        if (choice.next && !nodes[choice.next]) {
            report.fail("A08", id, `${where}.next`, `points at missing node "${choice.next}"`);
        }
        (choice.nextRules || []).forEach((rule, i) => {
            if (rule.next && !nodes[rule.next]) {
                report.fail("A08", id, `${where}.nextRules[${i}].next`, `points at missing node "${rule.next}"`);
            }
        });

        // A19 - a choice must go somewhere or end the run
        const goes = choice.next || (choice.nextRules || []).some((r) => r.next);
        if (!goes && !choice.terminal) {
            report.fail("A19", id, where, "choice has neither next/nextRules nor a terminal block");
        }
    });

    // A15 - choice ids unique within a node
    for (const [nodeId, node] of Object.entries(nodes)) {
        const seen = new Set();
        for (const choice of node.choices || []) {
            if (seen.has(choice.id)) {
                report.fail("A15", id, `nodes.${nodeId}`, `duplicate choice id "${choice.id}"`);
            }
            seen.add(choice.id);
        }
    }

    // A02/A17/S01 - every when, from every call site
    eachWhen(scenario, (when, where) => {
        for (const [key, value] of Object.entries(when)) {
            read.add(key);

            if (engineWritten.has(key)) continue;

            if (!knownState.has(key) && !knownDerived.has(key)) {
                report.fail(
                    "A02",
                    id,
                    `${where}.${key}`,
                    "key is in neither stateSchema nor derivedState; matchesAll returns false forever"
                );
                continue;
            }

            // A17 - value must be one the key can actually hold. Catches typos like
            // gating amaraBand on "closed" when the band emits broken/frayed/steady/tight.
            if (knownDerived.has(key)) {
                const allowed = dValues[key];
                if (allowed && allowed.size && !allowed.has(value)) {
                    report.fail(
                        "A17",
                        id,
                        `${where}.${key}`,
                        `value ${JSON.stringify(value)} is not emitted by band "${key}" ` +
                        `[${[...allowed].join(", ")}]`
                    );
                }
            } else if (types[key] === "enum") {
                const allowed = scenario.stateSchema[key].values || [];
                if (allowed.length && !allowed.includes(value)) {
                    report.fail(
                        "A17",
                        id,
                        `${where}.${key}`,
                        `value ${JSON.stringify(value)} is not in enum [${allowed.join(", ")}]`
                    );
                }
            } else if (types[key] === "bool" && typeof value !== "boolean") {
                report.fail("A17", id, `${where}.${key}`, `bool key compared against ${typeof value}`);
            }

            // S01 - Streets only. Raw integers work, but they break on any rebalance
            // and cannot be audited. Bands name their thresholds once.
            if (streets && types[key] === "int") {
                report.fail(
                    "S01",
                    id,
                    `${where}.${key}`,
                    "raw integer reference; Streets gates on bands only"
                );
            }
        }
    });

    // A07 - the root node runs against state that never passed through
    // applyDerived, so a band key is absent and matchesAll returns false. Silent:
    // the default message, every time, no error. Verified against the running
    // engine - initialState() emits stateSchema initials and seed, nothing else.
    const root = nodes[scenario.rootNode];
    if (root) {
        const rootWhens = [];
        for (const key of ["messageVariants", "threadVariants"]) {
            (root[key] || []).forEach((v, i) => {
                if (v.when) rootWhens.push([v.when, `nodes.${scenario.rootNode}.${key}[${i}].when`]);
            });
        }
        (root.choices || []).forEach((c, i) => {
            // requires may be malformed - A05 reports that; this must not crash on it.
            (Array.isArray(c.requires) ? c.requires : []).forEach((clause, j) => {
                rootWhens.push([clause, `nodes.${scenario.rootNode}.choices[${i}].requires[${j}]`]);
            });
        });
        for (const [when, where] of rootWhens) {
            for (const key of Object.keys(when)) {
                if (knownDerived.has(key)) {
                    report.fail(
                        "A07",
                        id,
                        `${where}.${key}`,
                        "root node references a derived key; bands do not exist until the first /respond"
                    );
                }
            }
        }
    }

    // W02/W03 - dead keys
    for (const key of knownState) {
        if (engineWritten.has(key)) continue;
        if (!written.has(key)) {
            report.warn("W02", id, `stateSchema.${key}`, "never written by any choice");
        }
        if (!read.has(key)) {
            const usedByBand = Object.values(derived).some((s) => s.from === key || s.minus === key);
            if (!usedByBand) {
                report.warn("W03", id, `stateSchema.${key}`, "never read by any when and feeds no band");
            }
        }
    }
    for (const band of knownDerived) {
        if (!read.has(band)) {
            report.warn("W03", id, `derivedState.${band}`, "declared but never referenced");
        }
    }

    // A10 - outcome coverage
    const declared = scenario.trajectories || null;
    const produced = new Set((scenario.outcomeRules || []).map((r) => r.value));
    if (scenario.outcomeDefault) produced.add(scenario.outcomeDefault);
    if (declared) {
        for (const t of declared) {
            if (!produced.has(t)) {
                report.fail("A10", id, `trajectories.${t}`, "declared but no outcome rule or default yields it");
            }
        }
        for (const t of produced) {
            if (!declared.includes(t)) {
                report.fail("A10", id, "outcomeRules", `rule yields "${t}", which is not in trajectories`);
            }
        }
    }

    if (streets) layerAStreets(scenario, report, ctx);
}

function layerAStreets(scenario, report, ctx) {
    const id = scenario.id;
    const nodes = scenario.nodes || {};

    for (const [nodeId, node] of Object.entries(nodes)) {
        // S02 - variant cap. Variant prose, not node count, is where content cost
        // actually accumulates.
        const variants = (node.messageVariants || []).length;
        if (variants > LIMITS.messageVariants) {
            report.fail(
                "S02",
                id,
                `nodes.${nodeId}.messageVariants`,
                `${variants} variants exceeds the cap of ${LIMITS.messageVariants}`
            );
        }

        // S05 - every node declares its day; the boundary is detected from it
        if (typeof node.day !== "number") {
            report.fail("S05", id, `nodes.${nodeId}.day`, "node does not declare a day");
        } else if (node.day < 1 || node.day > LIMITS.finalDay) {
            report.fail("S05", id, `nodes.${nodeId}.day`, `day ${node.day} is outside 1..${LIMITS.finalDay}`);
        }

        // S07 - scenario-qualified node id prefix: s<scenario>d<day>_<descriptor>.
        //
        // Node ids are a GLOBAL namespace across scenarios - renderBlocks.js keys on
        // nodeId alone, and blockFor falls back `node[key] || node.default || null`,
        // so a collision does not throw. It silently returns another scenario's
        // artwork. The Streets is a set of independent seven-day scenarios that each
        // have their own Day 1, so an unqualified "d1_open" collides by construction.
        // The scenario number in the prefix is what prevents that, and A11 remains
        // the backstop rather than being relaxed.
        if (typeof node.day === "number" &&
            !new RegExp(`^s\\d+d${node.day}_`).test(nodeId)) {
            report.fail("S07", id, `nodes.${nodeId}`,
                `id does not match the scenario-qualified convention s<n>d${node.day}_<descriptor>`);
        }

        // S06 - no terminal before the final day
        const hasTerminal = (node.choices || []).some((c) => c.terminal);
        if (hasTerminal && node.day !== LIMITS.finalDay) {
            report.fail(
                "S06",
                id,
                `nodes.${nodeId}`,
                `terminal block on day ${node.day}; only day ${LIMITS.finalDay} may terminate`
            );
        }

        // S08 - native prose guidance
        const messages = [node.message, ...(node.messageVariants || []).map((v) => v.message)];
        messages.filter(Boolean).forEach((m, i) => {
            if (m.length > LIMITS.nativeChars) {
                report.warn(
                    "S08",
                    id,
                    `nodes.${nodeId}.message[${i}]`,
                    `${m.length} chars exceeds the ~${LIMITS.nativeChars} guidance`
                );
            }
        });
    }
}

// -------------------------------------------------- Layer A, cross-scenario

function layerACrossScenario(scenarios, report) {
    // A11 - node ids are globally significant to render-block lookup. A duplicate
    // silently renders another scenario's artwork.
    const owner = new Map();
    for (const scenario of scenarios) {
        for (const nodeId of Object.keys(scenario.nodes || {})) {
            if (owner.has(nodeId)) {
                report.fail(
                    "A11",
                    scenario.id,
                    `nodes.${nodeId}`,
                    `node id also used by "${owner.get(nodeId)}"; render blocks key on nodeId alone`
                );
            } else {
                owner.set(nodeId, scenario.id);
            }
        }
    }

    // A12 - duplicate render-block keys in the merged file. No byte-identical
    // exception: two scenarios producing the same key is a node-id collision
    // regardless of whether the payloads currently agree.
    let perScenario;
    try {
        perScenario = fs
            .readdirSync(VISUAL_DIR)
            .filter((f) => /^render_blocks\..+\.json$/.test(f));
    } catch {
        return;
    }
    const seen = new Map();
    for (const file of perScenario) {
        let blocks;
        try {
            blocks = JSON.parse(fs.readFileSync(path.join(VISUAL_DIR, file), "utf-8"));
        } catch (e) {
            report.fail("A12", file, file, `unreadable: ${e.message}`);
            continue;
        }
        for (const key of Object.keys(blocks)) {
            if (seen.has(key)) {
                report.fail("A12", file, key, `render-block key also in ${seen.get(key)}`);
            } else {
                seen.set(key, file);
            }
        }
    }

    const mergedPath = path.join(VISUAL_DIR, "render_blocks.json");
    if (fs.existsSync(mergedPath) && seen.size) {
        const merged = JSON.parse(fs.readFileSync(mergedPath, "utf-8"));
        for (const key of seen.keys()) {
            if (!(key in merged)) {
                report.fail("A12", "render_blocks.json", key, "present per-scenario but missing from the merged file");
            }
        }
        for (const key of Object.keys(merged)) {
            if (!seen.has(key)) {
                report.warn("A12", "render_blocks.json", key, "in the merged file but in no per-scenario file");
            }
        }
    }
}

// ---------------------------------------------------- Layer A, config refs

/** Load mapping.<scenario>.json - the district bridge between authored prose
 *  and asset tokens. Prop and setting names in a scenario are PROSE, resolved
 *  through propSynonyms / settingTokens / unrenderableProps before they ever
 *  reach an asset. Checking raw authored strings against registries.json
 *  without this config produces a wall of false positives. */
function loadMapping(scenarioId) {
    const p = path.join(VISUAL_DIR, `mapping.${scenarioId}.json`);
    if (!fs.existsSync(p)) return null;
    try {
        return JSON.parse(fs.readFileSync(p, "utf-8"));
    } catch {
        return null;
    }
}

function layerAConfig(scenario, report, ctx) {
    if (!ctx.registries) return;
    const id = scenario.id;
    const mapping = ctx.mapping || loadMapping(id);
    const synonyms = (mapping && mapping.propSynonyms) || {};
    const unrenderable = new Set((mapping && mapping.unrenderableProps) || []);
    const settingTokens = (mapping && mapping.settingTokens) || {};
    const modes = new Set(Object.keys(ctx.registries.modes || {}));
    const characters = new Set(Object.keys(ctx.registries.characters || {}));
    const scenes = new Set(Object.keys(ctx.registries.scenes || {}));
    const props = new Set(Object.keys(ctx.registries.props || {}));
    if (!modes.size) return;

    const overrides = (mapping && mapping.modeOverrides) || {};
    // Modes that compose no artwork. Their `visual` block is authored context
    // that never reaches the composer, so asset references inside it are not
    // claims about assets. mapping.the_instruction.json says as much about
    // ask4_ownership, which is `messages` and carries a setting of "phone".
    const ARTLESS = new Set(["messages", "none"]);

    for (const [nodeId, node] of Object.entries(scenario.nodes || {})) {
        const resolvedMode =
            overrides[nodeId] ||
            node.presentation?.data?.visual?.mode ||
            (node.presentation?.type === "messages" ? "messages" : null);
        if (ARTLESS.has(resolvedMode)) continue;

        const visuals = [node.presentation?.data?.visual, ...(node.messageVariants || []).map((v) => v.visual)];
        visuals.filter(Boolean).forEach((visual, i) => {
            const where = `nodes.${nodeId}.visual[${i}]`;

            // A13 - render mode must be one the composer knows
            if (visual.mode && !modes.has(visual.mode)) {
                report.fail("A13", id, `${where}.mode`, `unknown render mode "${visual.mode}"`);
            }

            // A14 - character and register references. Registers are declared per
            // character; a node cannot ask for one the character does not have.
            for (const member of visual.cast || []) {
                const charId = `char.${member.id}`;
                if (!characters.has(charId)) {
                    if (characters.size) {
                        report.fail("A14", id, `${where}.cast.${member.id}`, "character not in registries.json");
                    }
                    continue;
                }
                const declared = ctx.registries.characters[charId].registers || [];
                if (member.register && declared.length && !declared.includes(member.register)) {
                    report.fail(
                        "A14",
                        id,
                        `${where}.cast.${member.id}.register`,
                        `register "${member.register}" is not declared for this character [${declared.join(", ")}]`
                    );
                }
                const wardrobes = ctx.registries.characters[charId].wardrobe || [];
                if (member.wardrobe && wardrobes.length && !wardrobes.includes(member.wardrobe)) {
                    report.fail(
                        "A14",
                        id,
                        `${where}.cast.${member.id}.wardrobe`,
                        `wardrobe "${member.wardrobe}" is not declared for this character`
                    );
                }
            }

            // Settings resolve through mapping.settingTokens first. A setting with no
            // mapping entry AND no direct token is genuinely unresolvable.
            if (visual.setting && scenes.size) {
                const mapped = settingTokens[visual.setting];
                const token = mapped || (visual.setting.startsWith("scene.") ? visual.setting : `scene.${visual.setting}`);
                if (!scenes.has(token)) {
                    report.fail(
                        "A14",
                        id,
                        `${where}.setting`,
                        mapped
                            ? `mapping resolves "${visual.setting}" to "${mapped}", which is not in registries.json`
                            : `setting "${visual.setting}" has no settingTokens entry and no scene token`
                    );
                }
            }

            // Props are prose. Resolve synonyms, honour the unrenderable list, and
            // only then ask whether an asset exists.
            for (const prop of visual.props || []) {
                if (unrenderable.has(prop)) continue;
                const mapped = synonyms[prop];
                const token = mapped || (prop.startsWith("prop.") ? prop : `prop.${prop.replace(/ /g, "_")}`);
                if (!props.size) continue;
                if (!props.has(token)) {
                    if (mapped) {
                        report.fail(
                            "A14",
                            id,
                            `${where}.props`,
                            `propSynonyms maps "${prop}" to "${mapped}", which is not in registries.json`
                        );
                    } else {
                        report.warn(
                            "A14",
                            id,
                            `${where}.props`,
                            `"${prop}" is neither a propSynonyms entry, an unrenderableProps entry, nor a token`
                        );
                    }
                }
            }
        });
    }
}

module.exports = {
    Report,
    loadMapping,
    layerA,
    layerAStreets,
    layerACrossScenario,
    layerAConfig,
    eachWhen,
    eachChoice,
    LIMITS,
    FAIL,
    WARN,
    SCENARIOS_DIR,
    VISUAL_DIR,
};