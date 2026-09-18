// SPDX-License-Identifier: MPL-2.0

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import test from "node:test";

import {
  ENGINE_ID,
  ENGINE_VERSION,
  addPolynomials,
  buildCovariantBasis,
  buildCovariantEngineSummary,
  buildSourceBinaryForms,
  canonicalPolynomialText,
  cubicSyzygyResidual,
  deriveCovariantGrade,
  isZeroPolynomial,
  multiplyPolynomials,
  polynomialSha256,
  powerPolynomial,
  rational,
  rationalToString,
  transvectant,
} from "../src/d4-triality-covariant-engine.mjs";
import {
  D4_TRIALITY_INVARIANT_GENERATORS,
} from "../src/d4-triality-reference.mjs";

const PROJECT_ROOT = resolve(new URL("..", import.meta.url).pathname);
const fixture = JSON.parse(
  readFileSync(
    resolve(PROJECT_ROOT, "examples/d4-tia-cov.v0.1.canonical.json"),
    "utf8",
  ),
);

test("exact rational arithmetic normalizes signs and common factors", () => {
  assert.equal(rationalToString(rational(6n, -8n)), "-3/4");
  assert.equal(rationalToString(rational(-6n, -8n)), "3/4");
  assert.equal(rationalToString(rational(0n, -99n)), "0");
});

test("source forms use Sakai's unweighted coefficient convention", () => {
  const { f, g } = buildSourceBinaryForms();
  assert.equal(
    canonicalPolynomialText(f),
    [
      "1|0,0,1,0,0,0,0,0,2",
      "1|0,1,0,0,0,0,0,1,1",
      "1|1,0,0,0,0,0,0,2,0",
    ].join("\n"),
  );
  assert.equal(f.size, 3);
  assert.equal(g.size, 4);
  assert.deepEqual(deriveCovariantGrade(f), {
    quadraticDegree: 1,
    cubicDegree: 0,
    covariantDegree: 1,
    polynomialDegree: 0,
    modularWeight: 4,
    covariantOrder: 2,
  });
  assert.deepEqual(deriveCovariantGrade(g), {
    quadraticDegree: 0,
    cubicDegree: 1,
    covariantDegree: 1,
    polynomialDegree: 0,
    modularWeight: 6,
    covariantOrder: 3,
  });
});

test("normalized transvectant reproduces the quadratic discriminant", () => {
  const { f } = buildSourceBinaryForms();
  const discriminant = transvectant(f, f, 2);
  assert.equal(
    canonicalPolynomialText(discriminant),
    [
      "-1/2|0,2,0,0,0,0,0,0,0",
      "2|1,0,1,0,0,0,0,0,0",
    ].join("\n"),
  );
  assert.equal(
    polynomialSha256(discriminant),
    "f1f5c4af36401c96f38d1a351d0750ef2380472d66251ef228c1dd8a6a1faea4",
  );
});

test("cubic Hessian, cubic covariant, and discriminant satisfy Sakai's syzygy", () => {
  assert.equal(isZeroPolynomial(cubicSyzygyResidual()), true);
});

test("all 15 covariants are constructed from transvectants and derive the published grades", () => {
  const basis = buildCovariantBasis();
  assert.equal(basis.length, 15);
  assert.equal(D4_TRIALITY_INVARIANT_GENERATORS.length, 15);

  for (let index = 0; index < basis.length; index += 1) {
    const actual = basis[index];
    const expected = D4_TRIALITY_INVARIANT_GENERATORS[index];
    assert.equal(actual.index, expected.index);
    assert.equal(actual.label, expected.label);
    assert.equal(actual.grade.quadraticDegree, expected.quadraticDegree);
    assert.equal(actual.grade.cubicDegree, expected.cubicDegree);
    assert.equal(actual.grade.polynomialDegree, expected.polynomialDegree);
    assert.equal(actual.grade.modularWeight, expected.modularWeight);
    assert.equal(actual.grade.covariantOrder, expected.covariantOrder);
    assert.equal(
      actual.grade.covariantDegree,
      expected.quadraticDegree + expected.cubicDegree,
    );
  }
});

test("the symbolic basis is pinned by independent term counts and SHA-256 fixtures", () => {
  const summary = buildCovariantEngineSummary();
  assert.equal(summary.engineId, ENGINE_ID);
  assert.equal(summary.engineVersion, ENGINE_VERSION);
  assert.deepEqual(summary, fixture);
});

test("polynomial products remain exact and deterministic", () => {
  const { f, g } = buildSourceBinaryForms();
  const fSquaredA = powerPolynomial(f, 2);
  const fSquaredB = multiplyPolynomials(f, f);
  assert.equal(
    canonicalPolynomialText(fSquaredA),
    canonicalPolynomialText(fSquaredB),
  );

  const doubled = addPolynomials(fSquaredA, fSquaredB);
  assert.notEqual(
    polynomialSha256(doubled),
    polynomialSha256(fSquaredA),
  );

  assert.throws(() => transvectant(f, g, 3), /exceeds/);
});
