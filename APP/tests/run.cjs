"use strict";

const path = require("node:path");

const scripts = [
  "../js/namespace.js",
  "../js/sha256.js",
  "../js/math64.js",
  "../js/audio.js",
  "../js/provenance.js",
  "../js/synthesis.js",
  "../js/composition.js",
  "tests.js"
];

for (const relative of scripts) require(path.join(__dirname, relative));

globalThis.QSOLIMC_TESTS(function report(outcome) {
  const symbol = outcome.passed ? "PASS" : "FAIL";
  process.stdout.write(symbol + " " + outcome.name + "\n");
  if (!outcome.passed) process.stdout.write(outcome.error + "\n");
}).then(function finished(outcomes) {
  const failures = outcomes.filter(function failed(item) { return !item.passed; });
  process.stdout.write("\n" + (outcomes.length - failures.length) + "/" + outcomes.length + " passed\n");
  if (failures.length) process.exitCode = 1;
}).catch(function crashed(error) {
  process.stderr.write(String(error && error.stack ? error.stack : error) + "\n");
  process.exitCode = 1;
});
