import assert from "node:assert/strict";
import test from "node:test";

import { D4_TRIALITY_NUMERATOR } from "../src/etq-model.mjs";
import {
  D4_TRIALITY_INVARIANT_GENERATORS,
  SAKAI_TRIALITY_CYCLE_DENOMINATOR,
  SAKAI_TRIALITY_CYCLE_NUMERATOR,
  SAKAI_WS_DENOMINATOR,
  SAKAI_WS_NUMERATOR,
  SAKAI_WT,
  integerIdentity,
  integerMatrixMultiply,
  trialityInvariantGrade,
} from "../src/d4-triality-reference.mjs";

function multiplyMany(...matrices) {
  return matrices.reduce((left, right) => integerMatrixMultiply(left, right));
}

test("ETQ D4 triality is exactly Sakai's wS wT three-cycle", () => {
  assert.equal(SAKAI_TRIALITY_CYCLE_DENOMINATOR, 2);
  assert.deepEqual(SAKAI_TRIALITY_CYCLE_NUMERATOR, D4_TRIALITY_NUMERATOR);

  assert.deepEqual(
    integerMatrixMultiply(SAKAI_WT, SAKAI_WT),
    integerIdentity(4),
  );
  assert.deepEqual(
    integerMatrixMultiply(SAKAI_WS_NUMERATOR, SAKAI_WS_NUMERATOR),
    integerIdentity(4, SAKAI_WS_DENOMINATOR ** 2),
  );
  assert.deepEqual(
    multiplyMany(
      SAKAI_TRIALITY_CYCLE_NUMERATOR,
      SAKAI_TRIALITY_CYCLE_NUMERATOR,
      SAKAI_TRIALITY_CYCLE_NUMERATOR,
    ),
    integerIdentity(4, SAKAI_TRIALITY_CYCLE_DENOMINATOR ** 3),
  );
});

test("integer matrix multiplication keeps exact intermediates", () => {
  const M = Number.MAX_SAFE_INTEGER;
  assert.deepEqual(
    integerMatrixMultiply([[M, 1, -M]], [[2], [1], [2]]),
    [[1]],
  );
  assert.throws(
    () => integerMatrixMultiply([[M]], [[2]]),
    /matrix product exceeded safe-integer range/,
  );
});

test("D4 triality invariant grade relations are internally exact", () => {
  const grade = trialityInvariantGrade({
    quadraticDegree: 1,
    cubicDegree: 1,
    polynomialDegree: 2,
  });
  assert.deepEqual(grade, {
    quadraticDegree: 1,
    cubicDegree: 1,
    polynomialDegree: 2,
    modularWeight: 12,
    covariantOrder: 3,
  });
  assert.equal(
    grade.covariantOrder,
    (grade.modularWeight - 3 * grade.polynomialDegree) / 2,
  );

  assert.throws(
    () =>
      trialityInvariantGrade({
        quadraticDegree: 0,
        cubicDegree: 0,
        polynomialDegree: 2,
      }),
    /negative covariant order/,
  );
  assert.throws(
    () =>
      trialityInvariantGrade({
        quadraticDegree: Number.MAX_SAFE_INTEGER,
        cubicDegree: 0,
        polynomialDegree: 1,
      }),
    /modularWeight exceeded safe-integer range/,
  );
});

test("the published minimal D4 triality-invariant basis has 15 graded generators", () => {
  assert.equal(D4_TRIALITY_INVARIANT_GENERATORS.length, 15);
  assert.equal(
    new Set(D4_TRIALITY_INVARIANT_GENERATORS.map((entry) => entry.label)).size,
    15,
  );

  const degreeCounts = new Map();
  for (const generator of D4_TRIALITY_INVARIANT_GENERATORS) {
    assert.equal(
      generator.modularWeight,
      4 * generator.quadraticDegree +
        6 * generator.cubicDegree +
        generator.polynomialDegree,
    );
    assert.equal(
      generator.covariantOrder,
      2 * generator.quadraticDegree +
        3 * generator.cubicDegree -
        generator.polynomialDegree,
    );
    assert.equal(
      generator.modularWeight,
      3 * generator.polynomialDegree + 2 * generator.covariantOrder,
    );
    degreeCounts.set(
      generator.polynomialDegree,
      (degreeCounts.get(generator.polynomialDegree) ?? 0) + 1,
    );
  }

  assert.deepEqual([...degreeCounts.entries()], [
    [0, 2],
    [2, 1],
    [4, 3],
    [6, 3],
    [8, 1],
    [10, 1],
    [12, 3],
    [18, 1],
  ]);
});
