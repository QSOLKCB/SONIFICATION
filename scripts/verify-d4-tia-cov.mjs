// SPDX-License-Identifier: MPL-2.0

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import {
  ENGINE_ID,
  ENGINE_SUMMARY_SCHEMA_ID,
  ENGINE_VERSION,
  buildCovariantEngineSummary,
  cubicSyzygyResidual,
  isZeroPolynomial,
} from "../src/d4-triality-covariant-engine.mjs";

const PROJECT_ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const fixture = JSON.parse(
  readFileSync(
    resolve(PROJECT_ROOT, "examples/d4-tia-cov.v0.1.canonical.json"),
    "utf8",
  ),
);
const schema = JSON.parse(
  readFileSync(
    resolve(PROJECT_ROOT, "spec/d4-tia-cov.v0.1.schema.json"),
    "utf8",
  ),
);

const summary = buildCovariantEngineSummary();

assert.equal(summary.schema, ENGINE_SUMMARY_SCHEMA_ID);
assert.equal(summary.engineId, ENGINE_ID);
assert.equal(summary.engineVersion, ENGINE_VERSION);
assert.equal(summary.generatorCount, 15);
assert.equal(isZeroPolynomial(cubicSyzygyResidual()), true);
assert.deepEqual(summary, fixture);

assert.equal(schema.$id, ENGINE_SUMMARY_SCHEMA_ID);
assert.equal(schema.properties.engineId.const, ENGINE_ID);
assert.equal(schema.properties.engineVersion.const, ENGINE_VERSION);
assert.equal(schema.properties.generatorCount.const, 15);
assert.equal(schema.properties.generators.minItems, 15);
assert.equal(schema.properties.generators.maxItems, 15);

for (const generator of summary.generators) {
  const grade = generator.grade;
  assert.equal(
    grade.covariantDegree,
    grade.quadraticDegree + grade.cubicDegree,
  );
  assert.equal(
    grade.polynomialDegree,
    2 * grade.quadraticDegree +
      3 * grade.cubicDegree -
      grade.covariantOrder,
  );
  assert.equal(
    grade.modularWeight,
    4 * grade.quadraticDegree +
      6 * grade.cubicDegree +
      grade.polynomialDegree,
  );
  assert.match(generator.polynomialSha256, /^[0-9a-f]{64}$/);
}

console.log(
  JSON.stringify(
    {
      status: "PASS",
      engine: `${ENGINE_ID}@${ENGINE_VERSION}`,
      generatorCount: summary.generatorCount,
      cubicSyzygy: summary.cubicSyzygy,
      generatorHashes: summary.generators.map((entry) => ({
        index: entry.index,
        label: entry.label,
        sha256: entry.polynomialSha256,
      })),
    },
    null,
    2,
  ),
);
