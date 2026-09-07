/* Negative fixtures for the scenario validator.
 *
 *   node --test tools/
 *
 * A validator with no failing fixtures is a validator nobody has proved works.
 * Every rule below gets a scenario that violates it and a scenario that does
 * not, so a rule that silently stops firing fails this file rather than passing
 * a broken scenario months later.
 *
 * Layer A tests run entirely in memory - no disk, no engine, no assets.
 * Layer B needs the engine, which loads from SCENARIOS_DIR, so those tests
 * write one temporary fixture and remove it again.
 */

const { test, describe, after } = require("node:test");
const assert = require("node:assert");
const fs = require("fs");
const path = require("path");

const A = require("./validate_scenario");
const B = require("./validate_scenario_sim");

const { Report, layerA, layerACrossScenario, SCENARIOS_DIR } = A;

// ------------------------------------------------------------ helpers

/** Minimal valid scenario. Every fixture starts here and breaks one thing, so
 *  a failure names the rule under test rather than a pile of unrelated noise. */
function base(overrides = {}) {
    return {
        id: "fixture",
        rootNode: "start",
        outcomeKey: "outcome",
        outcomeDefault: "neutral",
        stateSchema: {
            count: { type: "int", initial: 0, range: [0, 6] },
            flag: { type: "bool", initial: false },
            mood: { type: "enum", initial: "calm", values: ["calm", "tense"] },
        },
        derivedState: {
            countBand: {
                from: "count",
                bands: [
                    { min: 3, value: "high" },
                    { min: 1, value: "low" },
                    { min: -999, value: "none" },
                ],
            },
        },
        nodes: {
            start: {
                message: "opening",
                choices: [{ id: "go", setState: { count: 1 }, next: "second" }],
            },
            second: {
                message: "second",
                messageVariants: [{ when: { countBand: "low" }, message: "varied" }],
                choices: [{ id: "end", terminal: { consequence: "done" } }],
            },
        },
        outcomeRules: [{ when: { countBand: "low" }, value: "neutral" }],
        ...overrides,
    };
}

function runA(scenario, profile = "baseline") {
    const report = new Report();
    layerA(scenario, report, { profile, registries: null });
    return report;
}

function rules(report) {
    return report.failures.map((f) => f.rule);
}

function warnRules(report) {
    return report.warnings.map((f) => f.rule);
}

// ------------------------------------------------------------ Layer A

describe("Layer A - the clean fixture", () => {
    test("a valid scenario produces no failures", () => {
        const report = runA(base());
        assert.deepStrictEqual(report.failures, [], JSON.stringify(report.failures, null, 2));
    });
});

describe("Layer A - state schema and mutation", () => {
    test("A01 unknown setState key", () => {
        const s = base();
        s.nodes.start.choices[0].setState = { typo: 1 };
        assert.ok(rules(runA(s)).includes("A01"));
    });

    test("A01 does NOT fire on a declared key", () => {
        assert.ok(!rules(runA(base())).includes("A01"));
    });

    test("A16 int key set to a string", () => {
        const s = base();
        s.nodes.start.choices[0].setState = { count: "one" };
        assert.ok(rules(runA(s)).includes("A16"));
    });

    test("A16 enum key set to an undeclared value", () => {
        const s = base();
        s.nodes.start.choices[0].setState = { mood: "furious" };
        assert.ok(rules(runA(s)).includes("A16"));
    });

    test("A18 int key without a range", () => {
        const s = base();
        delete s.stateSchema.count.range;
        assert.ok(rules(runA(s)).includes("A18"));
    });
});

describe("Layer A - bands", () => {
    test("A03 band source is not declared", () => {
        const s = base();
        s.derivedState.countBand.from = "ghost";
        assert.ok(rules(runA(s)).includes("A03"));
    });

    test("A03 band source is a bool, which applyDerived cannot do arithmetic on", () => {
        const s = base();
        s.derivedState.countBand.from = "flag";
        assert.ok(rules(runA(s)).includes("A03"));
    });

    test("A04 bands not in descending order - the engine takes the FIRST match", () => {
        const s = base();
        s.derivedState.countBand.bands = [
            { min: -999, value: "none" },
            { min: 3, value: "high" },
        ];
        assert.ok(rules(runA(s)).includes("A04"));
    });

    test("A04 band list without a -999 terminator", () => {
        const s = base();
        s.derivedState.countBand.bands = [
            { min: 3, value: "high" },
            { min: 1, value: "low" },
        ];
        assert.ok(rules(runA(s)).includes("A04"));
    });
});

describe("Layer A - matchers", () => {
    test("A02 unknown when key", () => {
        const s = base();
        s.nodes.second.messageVariants[0].when = { nosuchkey: "low" };
        assert.ok(rules(runA(s)).includes("A02"));
    });

    test("A02 finds a when in nextRules, not just messageVariants", () => {
        const s = base();
        s.nodes.start.choices[0].nextRules = [{ when: { ghost: 1 }, next: "second" }];
        assert.ok(rules(runA(s)).includes("A02"));
    });

    test("A02 finds a when in outcomeRules", () => {
        const s = base();
        s.outcomeRules = [{ when: { ghost: "x" }, value: "neutral" }];
        assert.ok(rules(runA(s)).includes("A02"));
    });

    test("A17 band compared against a value the band never emits", () => {
        // The amaraBand:"closed" class of bug: key legal, value legal-looking, dead.
        const s = base();
        s.nodes.second.messageVariants[0].when = { countBand: "closed" };
        assert.ok(rules(runA(s)).includes("A17"));
    });

    test("A17 enum compared against an undeclared value", () => {
        const s = base();
        s.nodes.second.messageVariants[0].when = { mood: "furious" };
        assert.ok(rules(runA(s)).includes("A17"));
    });

    test("outcomeKey is accepted as a matcher key without being in stateSchema", () => {
        const s = base();
        s.aftermath = { you: [{ when: { outcome: "neutral" }, text: "x" }] };
        assert.ok(!rules(runA(s)).includes("A02"));
    });
});

describe("Layer A - requires", () => {
    test("A05 requires is not an array", () => {
        const s = base();
        s.nodes.start.choices[0].requires = { countBand: "low" };
        assert.ok(rules(runA(s)).includes("A05"));
    });

    test("A06 empty clause matches everything and defeats the gate", () => {
        const s = base();
        s.nodes.start.choices[0].requires = [{}];
        assert.ok(rules(runA(s)).includes("A06"));
    });

    test("W01 empty requires array warns but does not fail", () => {
        const s = base();
        s.nodes.start.choices[0].requires = [];
        const r = runA(s);
        assert.ok(warnRules(r).includes("W01"));
        assert.strictEqual(r.failures.length, 0);
    });

    test("multi-pair clause is legal - DNF, AND within a clause", () => {
        // On a NON-root node: a band reference at the root is A07 by design.
        const s = base();
        s.nodes.second.choices[0].requires = [{ countBand: "none", mood: "calm" }];
        assert.strictEqual(runA(s).failures.length, 0);
    });
});

describe("Layer A - routing", () => {
    test("A08 next points at a node that does not exist", () => {
        const s = base();
        s.nodes.start.choices[0].next = "nowhere";
        assert.ok(rules(runA(s)).includes("A08"));
    });

    test("A09 rootNode is not in nodes", () => {
        const s = base();
        s.rootNode = "missing";
        assert.ok(rules(runA(s)).includes("A09"));
    });

    test("A19 choice goes nowhere and does not terminate", () => {
        const s = base();
        delete s.nodes.start.choices[0].next;
        assert.ok(rules(runA(s)).includes("A19"));
    });

    test("A15 duplicate choice id within a node", () => {
        const s = base();
        s.nodes.start.choices.push({ id: "go", next: "second" });
        assert.ok(rules(runA(s)).includes("A15"));
    });
});

describe("Layer A - the root node derived-state trap", () => {
    test("A07 root node gates on a band, which does not exist until the first /respond", () => {
        const s = base();
        s.nodes.start.choices[0].requires = [{ countBand: "none" }];
        assert.ok(rules(runA(s)).includes("A07"));
    });

    test("A07 fires on a root messageVariant too", () => {
        const s = base();
        s.nodes.start.messageVariants = [{ when: { countBand: "none" }, message: "x" }];
        assert.ok(rules(runA(s)).includes("A07"));
    });

    test("A07 does NOT fire on a non-root node", () => {
        assert.ok(!rules(runA(base())).includes("A07"));
    });

    test("A07 does NOT fire on a raw enum key at the root - those do exist", () => {
        const s = base();
        s.nodes.start.choices[0].requires = [{ mood: "calm" }];
        assert.ok(!rules(runA(s)).includes("A07"));
    });
});

describe("Layer A - dead keys", () => {
    test("W02 key never written", () => {
        const s = base();
        s.stateSchema.orphan = { type: "bool", initial: false };
        assert.ok(warnRules(runA(s)).includes("W02"));
    });

    test("W03 key never read and feeding no band", () => {
        const s = base();
        s.stateSchema.orphan = { type: "bool", initial: false };
        s.nodes.start.choices[0].setState.orphan = true;
        assert.ok(warnRules(runA(s)).includes("W03"));
    });

    test("W03 does NOT fire on a key that only feeds a band", () => {
        // `count` is never read by a when directly - countBand is. Still live.
        // Assert on the specific key, not on the presence of any W03 at all:
        // the fixture also carries `flag` and `mood`, which are genuinely unread.
        const report = runA(base());
        const flagged = report.warnings.filter((w) => w.rule === "W03").map((w) => w.where);
        assert.ok(!flagged.includes("stateSchema.count"), flagged.join(", "));
    });
});

describe("Layer A - trajectories", () => {
    test("A10 declared trajectory that no rule yields", () => {
        const s = base();
        s.trajectories = ["neutral", "unreachable_by_rule"];
        assert.ok(rules(runA(s)).includes("A10"));
    });

    test("A10 rule yielding a trajectory that is not declared", () => {
        const s = base();
        s.trajectories = ["neutral"];
        s.outcomeRules.push({ when: { countBand: "high" }, value: "undeclared" });
        assert.ok(rules(runA(s)).includes("A10"));
    });
});

describe("Layer A - the streets profile", () => {
    function streetsBase() {
        const s = base();
        s.id = "the_streets";
        s.nodes = {
            d1_start: {
                day: 1,
                message: "x",
                choices: [{ id: "go", setState: { count: 1 }, next: "d7_end" }],
            },
            d7_end: {
                day: 7,
                message: "y",
                messageVariants: [{ when: { countBand: "low" }, message: "v" }],
                choices: [{ id: "fin", terminal: { consequence: "done" } }],
            },
        };
        s.rootNode = "d1_start";
        return s;
    }

    test("the streets fixture is clean under its own profile", () => {
        const r = runA(streetsBase(), "streets");
        assert.deepStrictEqual(r.failures, [], JSON.stringify(r.failures, null, 2));
    });

    test("S01 raw integer in a when", () => {
        const s = streetsBase();
        s.nodes.d7_end.messageVariants[0].when = { count: 1 };
        assert.ok(rules(runA(s, "streets")).includes("S01"));
    });

    test("S01 does NOT fire under the baseline profile", () => {
        const s = streetsBase();
        s.nodes.d7_end.messageVariants[0].when = { count: 1 };
        assert.ok(!rules(runA(s, "baseline")).includes("S01"));
    });

    test("S02 more than three message variants", () => {
        const s = streetsBase();
        s.nodes.d7_end.messageVariants = [1, 2, 3, 4].map((n) => ({
            when: { countBand: "low" },
            message: `v${n}`,
        }));
        assert.ok(rules(runA(s, "streets")).includes("S02"));
    });

    test("S05 node without a day", () => {
        const s = streetsBase();
        delete s.nodes.d7_end.day;
        assert.ok(rules(runA(s, "streets")).includes("S05"));
    });

    test("S06 terminal block before day 7", () => {
        const s = streetsBase();
        s.nodes.d1_start.choices.push({ id: "early", terminal: { consequence: "no" } });
        assert.ok(rules(runA(s, "streets")).includes("S06"));
    });

    test("S07 node id missing its day prefix", () => {
        const s = streetsBase();
        s.nodes.wrongname = s.nodes.d7_end;
        delete s.nodes.d7_end;
        s.nodes.d1_start.choices[0].next = "wrongname";
        assert.ok(rules(runA(s, "streets")).includes("S07"));
    });

    test("S08 native message over the guidance length warns, does not fail", () => {
        const s = streetsBase();
        s.nodes.d7_end.message = "x".repeat(A.LIMITS.nativeChars + 1);
        const r = runA(s, "streets");
        assert.ok(warnRules(r).includes("S08"));
        assert.ok(!rules(r).includes("S08"));
    });
});

describe("Layer A - cross scenario", () => {
    test("A11 node id used by two scenarios", () => {
        const one = base();
        one.id = "alpha";
        const two = base();
        two.id = "beta";
        const report = new Report();
        layerACrossScenario([one, two], report);
        assert.ok(rules(report).includes("A11"));
    });

    test("A11 does not fire when node ids are distinct", () => {
        const one = base();
        one.id = "alpha";
        const two = base();
        two.id = "beta";
        two.nodes = { b_start: two.nodes.start, b_second: two.nodes.second };
        const report = new Report();
        layerACrossScenario([one, two], report);
        assert.ok(!rules(report).includes("A11"));
    });
});

// ------------------------------------------------------------ Layer B

describe("Layer B - simulation against the engine", () => {
    const written = [];

    function install(name, scenario) {
        const file = path.join(SCENARIOS_DIR, `${name}.json`);
        scenario.id = name;
        fs.writeFileSync(file, JSON.stringify(scenario, null, 1));
        written.push(file);
        return scenario;
    }

    after(() => {
        for (const file of written) {
            try {
                fs.unlinkSync(file);
            } catch {
                /* nothing to clean */
            }
        }
    });

    test("B01 unreachable node", () => {
        const s = install("__fixture_unreachable", base());
        s.nodes.orphan = { message: "nobody comes here", choices: [{ id: "x", terminal: { consequence: "" } }] };
        const report = new Report();
        B.layerB(s, report, { profile: "baseline", cap: 20000 });
        assert.ok(rules(report).includes("B01"));
    });

    test("B02 choice that can never be offered", () => {
        const s = install("__fixture_deadchoice", base());
        // count can only ever reach 1, so "high" is unreachable and this gate is dead.
        s.nodes.second.choices.push({
            id: "impossible",
            requires: [{ countBand: "high" }],
            terminal: { consequence: "" },
        });
        const report = new Report();
        B.layerB(s, report, { profile: "baseline", cap: 20000 });
        assert.ok(rules(report).includes("B02"));
    });

    test("B08 a condition no reachable state satisfies", () => {
        const s = install("__fixture_deadwhen", base());
        s.nodes.second.messageVariants = [{ when: { countBand: "high" }, message: "never seen" }];
        const report = new Report();
        B.layerB(s, report, { profile: "baseline", cap: 20000 });
        assert.ok(rules(report).includes("B08"));
    });

    test("B04 trajectory no path produces", () => {
        const s = install("__fixture_deadtraj", base());
        s.outcomeRules.push({ when: { countBand: "high" }, value: "never_happens" });
        const report = new Report();
        B.layerB(s, report, { profile: "baseline", cap: 20000 });
        assert.ok(rules(report).includes("B04"));
    });

    test("a sound scenario produces no Layer B failures", () => {
        const s = install("__fixture_clean", base());
        const report = new Report();
        B.layerB(s, report, { profile: "baseline", cap: 20000 });
        assert.deepStrictEqual(report.failures, [], JSON.stringify(report.failures, null, 2));
    });
});

// -------------------------------------------- the precondition from SPEC v1.1

describe("SPEC v1.1 precondition - shipped scenarios pass unmodified", () => {
    test("the_instruction is clean under the baseline profile", () => {
        const file = path.join(SCENARIOS_DIR, "the_instruction.json");
        if (!fs.existsSync(file)) {
            console.log("      (skipped: the_instruction.json not present)");
            return;
        }
        const scenario = JSON.parse(fs.readFileSync(file, "utf-8"));
        scenario.id = "the_instruction";
        const report = new Report();
        layerA(scenario, report, { profile: "baseline", registries: null });
        assert.deepStrictEqual(report.failures, [], JSON.stringify(report.failures, null, 2));
    });

    test("the_secret is clean under the baseline profile", () => {
        const file = path.join(SCENARIOS_DIR, "the_secret.json");
        if (!fs.existsSync(file)) {
            console.log("      (SKIPPED: the_secret.json not present in this checkout)");
            return;
        }
        const scenario = JSON.parse(fs.readFileSync(file, "utf-8"));
        scenario.id = "the_secret";
        const report = new Report();
        layerA(scenario, report, { profile: "baseline", registries: null });
        assert.deepStrictEqual(report.failures, [], JSON.stringify(report.failures, null, 2));
    });
});