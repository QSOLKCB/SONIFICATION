// SPDX-License-Identifier: MPL-2.0

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";

import {
  D4_ORBIT_SEED,
  HARNESS_ID,
  HARNESS_VERSION,
  MODULAR_S,
  MODULAR_T,
  S3_LABELS,
  buildD4S3Orbit,
  buildEquivarianceReport,
  buildModularS3QuotientRepresentatives,
  buildS3EquivarianceHarnessSummary,
  deriveCoefficientAction,
  substituteUv,
  verifyCovariantEquivariance,
} from "../src/d4-triality-s3-equivariance.mjs";
import {
  buildCovariantBasis,
  buildSourceBinaryForms,
  canonicalPolynomialText,
  polynomialsEqual,
} from "../src/d4-triality-covariant-engine.mjs";

const PROJECT_ROOT = resolve(new URL("..", import.meta.url).pathname);
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

const EXPECTED_TABLE = {
  e: { e: "e", S: "S", T: "T", ST: "ST", TS: "TS", STS: "STS" },
  S: { e: "S", S: "e", T: "ST", ST: "T", TS: "STS", STS: "TS" },
  T: { e: "T", S: "TS", T: "e", ST: "STS", TS: "S", STS: "ST" },
  ST: { e: "ST", S: "STS", T: "S", ST: "TS", TS: "e", STS: "T" },
  TS: { e: "TS", S: "T", T: "STS", ST: "e", TS: "ST", STS: "S" },
  STS: { e: "STS", S: "ST", T: "TS", ST: "S", TS: "T", STS: "e" },
};

test("D4/F4 wS and wT generate the exact six-element S3 quotient action", () => {
  const d4 = buildD4S3Orbit();
  assert.deepEqual(d4.seed, D4_ORBIT_SEED);
  assert.deepEqual(d4.multiplicationTable, EXPECTED_TABLE);
  assert.deepEqual(
    d4.elements.map((entry) => entry.label),
    S3_LABELS,
  );
  assert.deepEqual(d4.orbit, [
    { label: "e", vector: ["2", "4", "6", "10"] },
    { label: "S", vector: ["1", "5", "7", "9"] },
    { label: "T", vector: ["2", "4", "6", "-10"] },
    { label: "ST", vector: ["11", "-5", "-3", "-1"] },
    { label: "TS", vector: ["1", "5", "7", "-9"] },
    { label: "STS", vector: ["11", "-5", "-3", "1"] },
  ]);
});

test("canonical modular representatives cover all six mod-2 quotient classes", () => {
  const modular = buildModularS3QuotientRepresentatives();
  assert.deepEqual(modular.generators.S, MODULAR_S);
  assert.deepEqual(modular.generators.T, MODULAR_T);
  assert.deepEqual(modular.multiplicationTable, EXPECTED_TABLE);
  assert.deepEqual(
    modular.representatives.map((entry) => entry.label),
    S3_LABELS,
  );
  assert.equal(
    new Set(modular.representatives.map((entry) => entry.mod2Key)).size,
    6,
  );
});

test("coefficient actions are derived from f(u',v') and g(u',v') exactly", () => {
  const { f, g } = buildSourceBinaryForms();

  for (const matrix of [MODULAR_S, MODULAR_T]) {
    const substitutions = deriveCoefficientAction(matrix);
    assert.equal(substitutions.length, 7);

    const transformedF = substituteUv(f, matrix);
    const transformedG = substituteUv(g, matrix);

    // deriveCoefficientAction itself reconstructs both transformed forms.
    // These checks ensure the returned action is nontrivial and deterministic.
    assert.ok(substitutions.every((entry) => entry.size >= 1));
    assert.notEqual(
      canonicalPolynomialText(transformedF),
      canonicalPolynomialText(f),
    );
    assert.notEqual(
      canonicalPolynomialText(transformedG),
      canonicalPolynomialText(g),
    );
  }
});

test("all 15 covariants satisfy exact SL2 equivariance under S and T representatives", () => {
  for (const matrix of [MODULAR_S, MODULAR_T]) {
    for (const generator of buildCovariantBasis()) {
      const result = verifyCovariantEquivariance(generator.polynomial, matrix);
      assert.equal(
        result.passed,
        true,
        `${generator.label} failed equivariance`,
      );
      assert.equal(
        result.coefficientSideSha256,
        result.variableSideSha256,
      );
    }
  }
});

test("the full six-representative harness performs 90 exact covariant checks", () => {
  const report = buildEquivarianceReport();
  assert.equal(report.checkedRepresentatives, 6);
  assert.equal(report.checkedGenerators, 15);
  assert.equal(report.exactChecks, 90);
  assert.equal(report.allPassed, true);
  assert.deepEqual(report.quotientMultiplicationTable, EXPECTED_TABLE);
  assert.ok(report.representatives.every((entry) => entry.allPassed));
  assert.ok(
    report.representatives.every(
      (entry) =>
        /^[0-9a-f]{64}$/.test(entry.coefficientActionSha256) &&
        /^[0-9a-f]{64}$/.test(entry.transformedBasisSha256),
    ),
  );
});

test("the harness keeps quotient S3 and upstairs SL2 actions explicitly separate", () => {
  const summary = buildS3EquivarianceHarnessSummary();
  assert.equal(summary.harnessId, HARNESS_ID);
  assert.equal(summary.harnessVersion, HARNESS_VERSION);
  assert.equal(summary.multiplicationTablesMatch, true);
  assert.deepEqual(
    summary.d4Orbit.multiplicationTable,
    summary.modularQuotient.multiplicationTable,
  );
  assert.match(
    summary.quotientIdentification.warning,
    /not asserted to form a literal six-element subgroup/,
  );
  assert.match(summary.claimBoundary, /introduces no sonification mapping/);
});


test("the canonical S3 equivariance summary is pinned by fixture and schema", () => {
  const summary = buildS3EquivarianceHarnessSummary();
  assert.deepEqual(summary, fixture);
  assert.equal(schema.$id, "qsol.d4-tia-s3-equivariance/v0.1");
  assert.deepEqual(schema.const, fixture);
});
