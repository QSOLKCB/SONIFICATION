// SPDX-License-Identifier: MPL-2.0

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import {
  HARNESS_ID,
  HARNESS_SCHEMA_ID,
  HARNESS_VERSION,
  S3_LABELS,
  buildS3EquivarianceHarnessSummary,
} from "../src/d4-triality-s3-equivariance.mjs";

const PROJECT_ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const fixture = JSON.parse(
  readFileSync(
    resolve(PROJECT_ROOT, "examples/d4-tia-s3-equivariance.v0.1.canonical.json"),
    "utf8",
  ),
);
const schema = JSON.parse(
  readFileSync(
    resolve(PROJECT_ROOT, "spec/d4-tia-s3-equivariance.v0.1.schema.json"),
    "utf8",
  ),
);

const summary = buildS3EquivarianceHarnessSummary();

assert.equal(summary.schema, HARNESS_SCHEMA_ID);
assert.deepEqual(summary, fixture);
assert.equal(schema.$id, HARNESS_SCHEMA_ID);
assert.deepEqual(schema.const, fixture);
assert.equal(summary.harnessId, HARNESS_ID);
assert.equal(summary.harnessVersion, HARNESS_VERSION);
assert.equal(summary.d4Orbit.elements.length, 6);
assert.equal(summary.d4Orbit.orbit.length, 6);
assert.equal(summary.modularQuotient.representatives.length, 6);
assert.equal(summary.multiplicationTablesMatch, true);
assert.equal(summary.equivariance.checkedRepresentatives, 6);
assert.equal(summary.equivariance.checkedGenerators, 15);
assert.equal(summary.equivariance.exactChecks, 90);
assert.equal(summary.equivariance.allPassed, true);
assert.deepEqual(
  summary.d4Orbit.multiplicationTable,
  summary.modularQuotient.multiplicationTable,
);
assert.deepEqual(
  summary.d4Orbit.elements.map((entry) => entry.label),
  S3_LABELS,
);
assert.deepEqual(
  summary.modularQuotient.representatives.map((entry) => entry.label),
  S3_LABELS,
);
assert.ok(
  summary.equivariance.representatives.every(
    (entry) =>
      entry.checkedGenerators === 15 &&
      entry.allPassed === true &&
      /^[0-9a-f]{64}$/.test(entry.coefficientActionSha256) &&
      /^[0-9a-f]{64}$/.test(entry.transformedBasisSha256),
  ),
);

console.log(JSON.stringify({ status: "PASS", ...summary }, null, 2));
