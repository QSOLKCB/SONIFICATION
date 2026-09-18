// SPDX-License-Identifier: MPL-2.0

import assert from "node:assert/strict";

import {
  HARNESS_ID,
  HARNESS_SCHEMA_ID,
  HARNESS_VERSION,
  S3_LABELS,
  buildS3EquivarianceHarnessSummary,
} from "../src/d4-triality-s3-equivariance.mjs";

const summary = buildS3EquivarianceHarnessSummary();

assert.equal(summary.schema, HARNESS_SCHEMA_ID);
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
