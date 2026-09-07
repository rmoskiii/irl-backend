#!/usr/bin/env node
/* IRX scenario validator - CLI.
 *
 *   node tools/validate.js                        every scenario, auto profile
 *   node tools/validate.js the_streets            one scenario
 *   node tools/validate.js --profile=streets      force the strict profile
 *   node tools/validate.js --layer=a              static only, no simulation
 *   node tools/validate.js --json                 machine-readable
 *   node tools/validate.js --cap=50000            simulation step cap
 *
 * Exit 0 = no failures. Exit 1 = at least one FAIL.
 */

const fs = require("fs");
const path = require("path");

const A = require("./validate_scenario");
const B = require("./validate_scenario_sim");

const { Report, FAIL, SCENARIOS_DIR, VISUAL_DIR } = A;

function parseArgs(argv) {
    const opts = { scenarios: [], profile: null, layer: "all", json: false, cap: B.DEFAULT_CAP };
    for (const arg of argv) {
        if (arg.startsWith("--profile=")) opts.profile = arg.split("=")[1];
        else if (arg.startsWith("--layer=")) opts.layer = arg.split("=")[1].toLowerCase();
        else if (arg.startsWith("--cap=")) opts.cap = parseInt(arg.split("=")[1], 10);
        else if (arg === "--json") opts.json = true;
        else if (!arg.startsWith("--")) opts.scenarios.push(arg);
    }
    return opts;
}

function profileFor(scenarioId, forced) {
    if (forced) return forced;
    return scenarioId === "the_streets" ? "streets" : "baseline";
}

function loadRegistries() {
    const p = path.join(VISUAL_DIR, "registries.json");
    if (!fs.existsSync(p)) return null;
    try {
        return JSON.parse(fs.readFileSync(p, "utf-8"));
    } catch {
        return null;
    }
}

function discover() {
    return fs
        .readdirSync(SCENARIOS_DIR)
        .filter((f) => f.endsWith(".json"))
        .map((f) => f.replace(/\.json$/, ""));
}

function main() {
    const opts = parseArgs(process.argv.slice(2));
    const ids = opts.scenarios.length ? opts.scenarios : discover();
    const registries = loadRegistries();
    const report = new Report();

    const loaded = [];
    for (const id of ids) {
        const file = path.join(SCENARIOS_DIR, `${id}.json`);
        if (!fs.existsSync(file)) {
            report.fail("LOAD", id, file, "scenario file not found");
            continue;
        }
        try {
            const scenario = JSON.parse(fs.readFileSync(file, "utf-8"));
            scenario.id = scenario.id || id;
            loaded.push(scenario);
        } catch (e) {
            report.fail("LOAD", id, file, `unparseable JSON: ${e.message}`);
        }
    }

    const profiles = {};
    for (const scenario of loaded) {
        const profile = profileFor(scenario.id, opts.profile);
        profiles[scenario.id] = profile;
        const ctx = { profile, registries, cap: opts.cap };

        A.layerA(scenario, report, ctx);
        A.layerAConfig(scenario, report, ctx);

        if (opts.layer !== "a") {
            try {
                B.layerB(scenario, report, ctx);
            } catch (e) {
                report.fail("B00", scenario.id, "simulation", `simulation threw: ${e.message}`);
            }
        }
    }

    if (loaded.length) A.layerACrossScenario(loaded, report);

    if (opts.json) {
        console.log(JSON.stringify({ profiles, findings: report.findings }, null, 2));
        process.exit(report.failures.length ? 1 : 0);
    }

    const byScenario = new Map();
    for (const f of report.findings) {
        if (!byScenario.has(f.scenario)) byScenario.set(f.scenario, []);
        byScenario.get(f.scenario).push(f);
    }

    console.log("");
    console.log("IRX scenario validator");
    console.log("─".repeat(72));
    for (const scenario of loaded) {
        console.log(
            `  ${scenario.id.padEnd(20)} profile=${profiles[scenario.id].padEnd(9)} ` +
            `nodes=${Object.keys(scenario.nodes || {}).length}`
        );
    }
    console.log("─".repeat(72));

    for (const [scenario, findings] of byScenario) {
        console.log("");
        console.log(`  ${scenario}`);
        for (const f of findings) {
            const tag = f.severity === FAIL ? "FAIL" : "warn";
            console.log(`    ${tag}  ${f.rule.padEnd(4)}  ${f.where}`);
            console.log(`              ${f.message}`);
        }
    }

    console.log("");
    console.log("─".repeat(72));
    const fails = report.failures.length;
    const warns = report.warnings.length;
    console.log(`  ${fails} failure${fails === 1 ? "" : "s"}, ${warns} warning${warns === 1 ? "" : "s"}`);
    console.log("");
    process.exit(fails ? 1 : 0);
}

if (require.main === module) main();

module.exports = { profileFor, parseArgs };