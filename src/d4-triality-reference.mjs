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
      let total = 0;
      for (let index = 0; index < leftShape.columns; index += 1) {
        total += row[index] * right[index][column];
      }
      if (!Number.isSafeInteger(total)) {
        throw new RangeError("matrix product exceeded safe-integer range");
      }
      return total;
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
 * m is the polynomial degree in the D4 variables, k is modular weight, and
 * omega is covariant order.
 */
export function trialityInvariantGrade({
  quadraticDegree,
  cubicDegree,
  polynomialDegree,
}) {
  requireNonnegativeSafeInteger(quadraticDegree, "quadraticDegree");
  requireNonnegativeSafeInteger(cubicDegree, "cubicDegree");
  requireNonnegativeSafeInteger(polynomialDegree, "polynomialDegree");

  const covariantOrder =
    2 * quadraticDegree + 3 * cubicDegree - polynomialDegree;
  if (covariantOrder < 0) {
    throw new RangeError("the requested grades imply negative covariant order");
  }
  const modularWeight =
    4 * quadraticDegree + 6 * cubicDegree + polynomialDegree;

  return Object.freeze({
    quadraticDegree,
    cubicDegree,
    polynomialDegree,
    modularWeight,
    covariantOrder,
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
