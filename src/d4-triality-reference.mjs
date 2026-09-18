// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this file,
// You can obtain one at https://mozilla.org/MPL/2.0/.
// SPDX-License-Identifier: MPL-2.0
// Copyright (c) 2026 Trent Slade / QSOL-IMC.

/**
 * Noncanonical literature-alignment helpers for D4 triality.
 *
 * This module records exact matrices and grading relations from Kazuhiro
 * Sakai's D4/F4 triality papers. It does not alter ETQ-101 or ETQ-303 protocol
 * identity, receiver mappings, canonical fixtures, or scientific claims.
 */

function freezeMatrix(matrix) {
  return Object.freeze(matrix.map((row) => Object.freeze([...row])));
}

export const SAKAI_WT = freezeMatrix([
  [1, 0, 0, 0],
  [0, 1, 0, 0],
  [0, 0, 1, 0],
  [0, 0, 0, -1],
]);

export const SAKAI_WS_NUMERATOR = freezeMatrix([
  [1, 1, 1, -1],
  [1, 1, -1, 1],
  [1, -1, 1, 1],
  [-1, 1, 1, 1],
]);

export const SAKAI_WS_DENOMINATOR = 2;

function validateIntegerMatrix(matrix, name) {
  if (!Array.isArray(matrix) || matrix.length === 0) {
    throw new TypeError(`${name} must be a non-empty matrix`);
  }
  const width = matrix[0]?.length;
  if (!Number.isSafeInteger(width) || width <= 0) {
    throw new TypeError(`${name} must have non-empty rows`);
  }
  for (const row of matrix) {
    if (!Array.isArray(row) || row.length !== width) {
      throw new RangeError(`${name} must be rectangular`);
    }
    if (!row.every(Number.isSafeInteger)) {
      throw new TypeError(`${name} entries must be safe integers`);
    }
  }
  return { rows: matrix.length, columns: width };
}

const MAX_SAFE_BIGINT = BigInt(Number.MAX_SAFE_INTEGER);
const MIN_SAFE_BIGINT = -MAX_SAFE_BIGINT;

function exactSafeNumber(value, context) {
  if (typeof value !== "bigint") {
    throw new TypeError(`${context} must be a bigint`);
  }
  if (value < MIN_SAFE_BIGINT || value > MAX_SAFE_BIGINT) {
    throw new RangeError(`${context} exceeded safe-integer range`);
  }
  return Number(value);
}

export function integerMatrixMultiply(left, right) {
  const leftShape = validateIntegerMatrix(left, "left");
  const rightShape = validateIntegerMatrix(right, "right");
  if (leftShape.columns !== rightShape.rows) {
    throw new RangeError(
      `incompatible matrix dimensions ${leftShape.rows}x${leftShape.columns} and ` +
        `${rightShape.rows}x${rightShape.columns}`,
    );
  }

  return left.map((row) =>
    Array.from({ length: rightShape.columns }, (_, column) => {
      let total = 0n;
      for (let index = 0; index < leftShape.columns; index += 1) {
        total += BigInt(row[index]) * BigInt(right[index][column]);
      }
      return exactSafeNumber(total, "matrix product");
    }),
  );
}

export function integerIdentity(dimension, scale = 1) {
  if (!Number.isSafeInteger(dimension) || dimension <= 0) {
    throw new RangeError("dimension must be a positive safe integer");
  }
  if (!Number.isSafeInteger(scale)) {
    throw new TypeError("scale must be a safe integer");
  }
  return Array.from({ length: dimension }, (_, row) =>
    Array.from({ length: dimension }, (_, column) =>
      row === column ? scale : 0,
    ),
  );
}

export const SAKAI_TRIALITY_CYCLE_NUMERATOR = freezeMatrix(
  integerMatrixMultiply(SAKAI_WS_NUMERATOR, SAKAI_WT),
);
export const SAKAI_TRIALITY_CYCLE_DENOMINATOR = SAKAI_WS_DENOMINATOR;

function requireNonnegativeSafeInteger(value, name) {
  if (!Number.isSafeInteger(value) || value < 0) {
    throw new RangeError(`${name} must be a non-negative safe integer`);
  }
}

/**
 * Compute Sakai's trigrading relations for D4 triality invariants.
 *
 * da and db are the refined degrees in the binary quadratic and binary cubic,
 * m is the homogeneous polynomial degree in the D4 variables used by Sakai's
 * 2026 D4-triality-invariant ring, k is modular weight, and omega is covariant
 * order. This m is distinct from the Jacobi-form index used in the earlier
 * triality-invariant Jacobi-form construction.
 */
export function trialityInvariantGrade({
  quadraticDegree,
  cubicDegree,
  polynomialDegree,
}) {
  requireNonnegativeSafeInteger(quadraticDegree, "quadraticDegree");
  requireNonnegativeSafeInteger(cubicDegree, "cubicDegree");
  requireNonnegativeSafeInteger(polynomialDegree, "polynomialDegree");

  const da = BigInt(quadraticDegree);
  const db = BigInt(cubicDegree);
  const m = BigInt(polynomialDegree);
  const covariantOrderExact = 2n * da + 3n * db - m;
  if (covariantOrderExact < 0n) {
    throw new RangeError("the requested grades imply negative covariant order");
  }
  const modularWeightExact = 4n * da + 6n * db + m;

  return Object.freeze({
    quadraticDegree,
    cubicDegree,
    polynomialDegree,
    modularWeight: exactSafeNumber(modularWeightExact, "modularWeight"),
    covariantOrder: exactSafeNumber(covariantOrderExact, "covariantOrder"),
  });
}

const generatorDefinitions = [
  ["f", 1, 0, 0],
  ["g", 0, 1, 0],
  ["(f,g)_1", 1, 1, 2],
  ["quadratic-discriminant", 2, 0, 4],
  ["(f,g)_2", 1, 1, 4],
  ["P=(g,g)_2", 0, 2, 4],
  ["(f^2,g)_3", 2, 1, 6],
  ["(f,P)_1", 1, 2, 6],
  ["Q=(g,P)_1", 0, 3, 6],
  ["(f,P)_2", 1, 2, 8],
  ["(f,Q)_2", 1, 3, 10],
  ["(f^3,g^2)_6", 3, 2, 12],
  ["cubic-discriminant=(P,P)_2", 0, 4, 12],
  ["(f^2,Q)_3", 2, 3, 12],
  ["(f^3,gQ)_6", 3, 4, 18],
];

export const D4_TRIALITY_INVARIANT_GENERATORS = Object.freeze(
  generatorDefinitions.map(
    ([label, quadraticDegree, cubicDegree, polynomialDegree], index) =>
      Object.freeze({
        index: index + 1,
        label,
        ...trialityInvariantGrade({
          quadraticDegree,
          cubicDegree,
          polynomialDegree,
        }),
      }),
  ),
);
