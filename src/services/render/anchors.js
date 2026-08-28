'use strict';
const fs = require('fs');
const path = require('path');

/** Loads the visual contract once. anchors.json is the placement contract;
 *  registries.json maps scenario character ids to asset bases. Neither is
 *  scenario data - the renderer never reads the scenario. */
function loadContract(assetsDir, registriesPath) {
    const anchors = JSON.parse(fs.readFileSync(path.join(assetsDir, 'anchors.json'), 'utf8'));
    const registries = JSON.parse(fs.readFileSync(registriesPath, 'utf8'));
    return { anchors, registries };
}
module.exports = { loadContract };