// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this file,
// You can obtain one at https://mozilla.org/MPL/2.0/.
// SPDX-License-Identifier: MPL-2.0
// Copyright (c) 2026 Trent Slade / QSOL-IMC.

/**
 * D4-TIA-S3-EQUIV v0.1.0 exact orbit and equivariance harness.
 *
 * The finite D4/F4 side realizes the quotient W(F4)/W(D4) ~= S3 exactly via
 * Sakai's wS and wT involutions. The binary-form side uses canonical SL2(Z)
 * representatives for the matching quotient classes in SL2(Z)/Gamma(2) ~= S3.
 * Covariant equivariance is checked upstairs in SL2(C), not by pretending the
 * six quotient classes form a literal six-element subgroup of SL2(Z).
 */

import { createHash } from "node:crypto";

import {
  POLYNOMIAL_VARIABLES,
  addPolynomials,
  buildCovariantBasis,
  buildSourceBinaryForms,
  canonicalPolynomialText,
  constantPolynomial,
  monomialPolynomial,
  multiplyPolynomials,
  polynomialSha256,
  polynomialsEqual,
  powerPolynomial,
  rational,
  rationalToString,
  scalePolynomial,
  serializePolynomial,
  zeroPolynomial,
} from "./d4-triality-covariant-engine.mjs";
import {
  SAKAI_WS_DENOMINATOR,
  SAKAI_WS_NUMERATOR,
  SAKAI_WT,
  integerIdentity,
  integerMatrixMultiply,
} from "./d4-triality-reference.mjs";

export const HARNESS_ID = "D4-TIA-S3-EQUIV";
export const HARNESS_VERSION = "0.1.0";
export const HARNESS_SCHEMA_ID = "qsol.d4-tia-s3-equivariance/v0.1";

export const S3_LABELS = Object.freeze(["e", "S", "T", "ST", "TS", "STS"]);
export const D4_ORBIT_SEED = Object.freeze([2, 4, 6, 10]);

export const MODULAR_S = Object.freeze([
  Object.freeze([0, -1]),
  Object.freeze([1, 0]),
]);
export const MODULAR_T = Object.freeze([
  Object.freeze([1, 1]),
  Object.freeze([0, 1]),
]);

const U_INDEX = POLYNOMIAL_VARIABLES.indexOf("u");
const V_INDEX = POLYNOMIAL_VARIABLES.indexOf("v");
const COEFFICIENT_COUNT = U_INDEX;

if (
  U_INDEX !== 7 ||
  V_INDEX !== 8 ||
  COEFFICIENT_COUNT !== 7 ||
  POLYNOMIAL_VARIABLES.length !== 9
) {
  throw new Error("D4-TIA-S3-EQUIV requires the frozen nine-variable covariant ABI");
}

function parseRationalText(text) {
  if (typeof text !== "string" || text.length === 0) {
    throw new TypeError("rational text must be non-empty");
  }
  const parts = text.split("/");
  if (parts.length === 1) return rational(BigInt(parts[0]));
  if (parts.length === 2) return rational(BigInt(parts[0]), BigInt(parts[1]));
  throw new TypeError(`invalid rational text: ${text}`);
}

function addRationals(left, right) {
  return rational(
    left.numerator * right.denominator + right.numerator * left.denominator,
    left.denominator * right.denominator,
  );
}

function multiplyRationals(left, right) {
  return rational(
    left.numerator * right.numerator,
    left.denominator * right.denominator,
  );
}

function rationalZero() {
  return rational(0n);
}

function rationalOne() {
  return rational(1n);
}

function rationalMatrixIdentity(dimension) {
  return Array.from({ length: dimension }, (_, row) =>
    Array.from({ length: dimension }, (_, column) =>
      row === column ? rationalOne() : rationalZero(),
    ),
  );
}

function integerMatrixToRational(matrix, denominator = 1) {
  if (!Number.isSafeInteger(denominator) || denominator <= 0) {
    throw new RangeError("matrix denominator must be a positive safe integer");
  }
  return matrix.map((row) =>
    row.map((value) => rational(BigInt(value), BigInt(denominator))),
  );
}

function validateRationalMatrix(matrix, name) {
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
    for (const value of row) {
      if (
        !value ||
        typeof value.numerator !== "bigint" ||
        typeof value.denominator !== "bigint"
      ) {
        throw new TypeError(`${name} must contain rational entries`);
      }
    }
  }
  return { rows: matrix.length, columns: width };
}

export function rationalMatrixMultiply(left, right) {
  const leftShape = validateRationalMatrix(left, "left");
  const rightShape = validateRationalMatrix(right, "right");
  if (leftShape.columns !== rightShape.rows) {
    throw new RangeError("rational matrix dimensions are incompatible");
  }

  return left.map((row) =>
    Array.from({ length: rightShape.columns }, (_, column) => {
      let total = rationalZero();
      for (let index = 0; index < leftShape.columns; index += 1) {
        total = addRationals(
          total,
          multiplyRationals(row[index], right[index][column]),
        );
      }
      return total;
    }),
  );
}

function rationalMatrixPower(matrix, exponent) {
  const shape = validateRationalMatrix(matrix, "matrix");
  if (shape.rows !== shape.columns) throw new RangeError("matrix must be square");
  if (!Number.isSafeInteger(exponent) || exponent < 0) {
    throw new RangeError("matrix exponent must be a non-negative safe integer");
  }
  let result = rationalMatrixIdentity(shape.rows);
  let base = matrix;
  let power = exponent;
  while (power > 0) {
    if (power % 2 === 1) result = rationalMatrixMultiply(result, base);
    power = Math.floor(power / 2);
    if (power > 0) base = rationalMatrixMultiply(base, base);
  }
  return result;
}

function rationalMatrixKey(matrix) {
  return matrix
    .map((row) => row.map((value) => rationalToString(value)).join(","))
    .join(";");
}

function rationalMatrixToStrings(matrix) {
  return matrix.map((row) => row.map((value) => rationalToString(value)));
}

function rationalMatrixVectorMultiply(matrix, vector) {
  const shape = validateRationalMatrix(matrix, "matrix");
  if (!Array.isArray(vector) || vector.length !== shape.columns) {
    throw new RangeError("vector length does not match matrix width");
  }
  const values = vector.map((value) =>
    typeof value === "number"
      ? rational(BigInt(value))
      : typeof value === "bigint"
        ? rational(value)
        : value,
  );
  return matrix.map((row) => {
    let total = rationalZero();
    for (let index = 0; index < row.length; index += 1) {
      total = addRationals(total, multiplyRationals(row[index], values[index]));
    }
    return total;
  });
}

function rationalVectorToStrings(vector) {
  return vector.map((value) => rationalToString(value));
}

function sameRationalMatrix(left, right) {
  return rationalMatrixKey(left) === rationalMatrixKey(right);
}

function buildD4ElementMatrices() {
  const identity = rationalMatrixIdentity(4);
  const S = integerMatrixToRational(
    SAKAI_WS_NUMERATOR,
    SAKAI_WS_DENOMINATOR,
  );
  const T = integerMatrixToRational(SAKAI_WT);
  const ST = rationalMatrixMultiply(S, T);
  const TS = rationalMatrixMultiply(T, S);
  const STS = rationalMatrixMultiply(ST, S);
  return new Map([
    ["e", identity],
    ["S", S],
    ["T", T],
    ["ST", ST],
    ["TS", TS],
    ["STS", STS],
  ]);
}

function multiplicationTable(labels, elements, multiply, key) {
  const lookup = new Map(
    labels.map((label) => [key(elements.get(label)), label]),
  );
  const table = {};
  for (const leftLabel of labels) {
    table[leftLabel] = {};
    for (const rightLabel of labels) {
      const product = multiply(
        elements.get(leftLabel),
        elements.get(rightLabel),
      );
      const productLabel = lookup.get(key(product));
      if (!productLabel) {
        throw new Error(
          `group multiplication escaped the six-element set: ${leftLabel}*${rightLabel}`,
        );
      }
      table[leftLabel][rightLabel] = productLabel;
    }
  }
  return table;
}

export function buildD4S3Orbit() {
  const elements = buildD4ElementMatrices();
  if (
    new Set([...elements.values()].map(rationalMatrixKey)).size !==
    S3_LABELS.length
  ) {
    throw new Error("D4 triality generators do not produce six distinct elements");
  }

  const identity = elements.get("e");
  if (!sameRationalMatrix(rationalMatrixPower(elements.get("S"), 2), identity)) {
    throw new Error("D4 triality S involution failed");
  }
  if (!sameRationalMatrix(rationalMatrixPower(elements.get("T"), 2), identity)) {
    throw new Error("D4 triality T involution failed");
  }
  if (!sameRationalMatrix(rationalMatrixPower(elements.get("ST"), 3), identity)) {
    throw new Error("D4 triality (ST)^3 relation failed");
  }

  const table = multiplicationTable(
    S3_LABELS,
    elements,
    rationalMatrixMultiply,
    rationalMatrixKey,
  );

  const orbit = S3_LABELS.map((label) => ({
    label,
    vector: rationalVectorToStrings(
      rationalMatrixVectorMultiply(elements.get(label), D4_ORBIT_SEED),
    ),
  }));
  if (new Set(orbit.map((entry) => entry.vector.join(","))).size !== 6) {
    throw new Error("chosen D4 orbit seed does not have a six-element orbit");
  }

  return {
    generators: {
      S: rationalMatrixToStrings(elements.get("S")),
      T: rationalMatrixToStrings(elements.get("T")),
    },
    elements: S3_LABELS.map((label) => ({
      label,
      matrix: rationalMatrixToStrings(elements.get(label)),
    })),
    multiplicationTable: table,
    seed: [...D4_ORBIT_SEED],
    orbit,
  };
}

function assertIntegerMatrix2(matrix, name) {
  if (
    !Array.isArray(matrix) ||
    matrix.length !== 2 ||
    !matrix.every(
      (row) =>
        Array.isArray(row) &&
        row.length === 2 &&
        row.every(Number.isSafeInteger),
    )
  ) {
    throw new TypeError(`${name} must be a 2x2 safe-integer matrix`);
  }
  const determinant =
    BigInt(matrix[0][0]) * BigInt(matrix[1][1]) -
    BigInt(matrix[0][1]) * BigInt(matrix[1][0]);
  if (determinant !== 1n) {
    throw new RangeError(`${name} must have determinant one`);
  }
  return matrix;
}

function mod2(value) {
  return ((value % 2) + 2) % 2;
}

function mod2Key(matrix) {
  return assertIntegerMatrix2(matrix, "matrix")
    .flat()
    .map(mod2)
    .join("");
}

function buildModularRepresentativeMatrices() {
  const e = integerIdentity(2);
  const S = MODULAR_S.map((row) => [...row]);
  const T = MODULAR_T.map((row) => [...row]);
  const ST = integerMatrixMultiply(S, T);
  const TS = integerMatrixMultiply(T, S);
  const STS = integerMatrixMultiply(ST, S);
  return new Map([
    ["e", e],
    ["S", S],
    ["T", T],
    ["ST", ST],
    ["TS", TS],
    ["STS", STS],
  ]);
}

export function buildModularS3QuotientRepresentatives() {
  const elements = buildModularRepresentativeMatrices();
  for (const [label, matrix] of elements) {
    assertIntegerMatrix2(matrix, label);
  }

  const keys = S3_LABELS.map((label) => mod2Key(elements.get(label)));
  if (new Set(keys).size !== 6) {
    throw new Error("modular representatives do not cover six distinct mod-2 classes");
  }

  const lookup = new Map(
    S3_LABELS.map((label) => [mod2Key(elements.get(label)), label]),
  );
  const table = {};
  for (const leftLabel of S3_LABELS) {
    table[leftLabel] = {};
    for (const rightLabel of S3_LABELS) {
      const product = integerMatrixMultiply(
        elements.get(leftLabel),
        elements.get(rightLabel),
      );
      const productLabel = lookup.get(mod2Key(product));
      if (!productLabel) {
        throw new Error("modular quotient multiplication escaped S3");
      }
      table[leftLabel][rightLabel] = productLabel;
    }
  }

  return {
    generators: {
      S: elements.get("S").map((row) => [...row]),
      T: elements.get("T").map((row) => [...row]),
    },
    representatives: S3_LABELS.map((label) => ({
      label,
      matrix: elements.get(label).map((row) => [...row]),
      mod2Key: mod2Key(elements.get(label)),
    })),
    multiplicationTable: table,
  };
}

function variablePolynomial(variableIndex, coefficient = 1n) {
  const exponents = Array(POLYNOMIAL_VARIABLES.length).fill(0);
  exponents[variableIndex] = 1;
  return monomialPolynomial(exponents, coefficient);
}

function linearUvForms(matrix) {
  assertIntegerMatrix2(matrix, "SL2 matrix");
  return {
    uPrime: addPolynomials(
      variablePolynomial(U_INDEX, BigInt(matrix[0][0])),
      variablePolynomial(V_INDEX, BigInt(matrix[0][1])),
    ),
    vPrime: addPolynomials(
      variablePolynomial(U_INDEX, BigInt(matrix[1][0])),
      variablePolynomial(V_INDEX, BigInt(matrix[1][1])),
    ),
  };
}

export function substituteUv(polynomial, matrix) {
  const { uPrime, vPrime } = linearUvForms(matrix);
  let result = zeroPolynomial();

  for (const term of serializePolynomial(polynomial)) {
    const exponents = [...term.exponents];
    const uExponent = exponents[U_INDEX];
    const vExponent = exponents[V_INDEX];
    exponents[U_INDEX] = 0;
    exponents[V_INDEX] = 0;

    let transformedTerm = monomialPolynomial(
      exponents,
      parseRationalText(term.coefficient),
    );
    if (uExponent > 0) {
      transformedTerm = multiplyPolynomials(
        transformedTerm,
        powerPolynomial(uPrime, uExponent),
      );
    }
    if (vExponent > 0) {
      transformedTerm = multiplyPolynomials(
        transformedTerm,
        powerPolynomial(vPrime, vExponent),
      );
    }
    result = addPolynomials(result, transformedTerm);
  }
  return result;
}

function binaryCoefficientPolynomial(polynomial, order, position) {
  if (
    !Number.isSafeInteger(order) ||
    order < 0 ||
    !Number.isSafeInteger(position) ||
    position < 0 ||
    position > order
  ) {
    throw new RangeError("invalid binary coefficient request");
  }

  let result = zeroPolynomial();
  for (const term of serializePolynomial(polynomial)) {
    const exponents = [...term.exponents];
    if (exponents[U_INDEX] + exponents[V_INDEX] !== order) {
      throw new Error("transformed source form is not homogeneous in u,v");
    }
    if (
      exponents[U_INDEX] !== order - position ||
      exponents[V_INDEX] !== position
    ) {
      continue;
    }
    exponents[U_INDEX] = 0;
    exponents[V_INDEX] = 0;
    result = addPolynomials(
      result,
      monomialPolynomial(
        exponents,
        parseRationalText(term.coefficient),
      ),
    );
  }
  if (result.size === 0) {
    throw new Error("binary coefficient extraction produced zero unexpectedly");
  }
  return result;
}

export function deriveCoefficientAction(matrix) {
  assertIntegerMatrix2(matrix, "SL2 matrix");
  const { f, g } = buildSourceBinaryForms();
  const transformedF = substituteUv(f, matrix);
  const transformedG = substituteUv(g, matrix);

  const substitutions = [
    binaryCoefficientPolynomial(transformedF, 2, 0),
    binaryCoefficientPolynomial(transformedF, 2, 1),
    binaryCoefficientPolynomial(transformedF, 2, 2),
    binaryCoefficientPolynomial(transformedG, 3, 0),
    binaryCoefficientPolynomial(transformedG, 3, 1),
    binaryCoefficientPolynomial(transformedG, 3, 2),
    binaryCoefficientPolynomial(transformedG, 3, 3),
  ];

  if (!polynomialsEqual(
    substituteCoefficientVariables(f, substitutions),
    transformedF,
  )) {
    throw new Error("derived quadratic coefficient action does not reconstruct f'");
  }
  if (!polynomialsEqual(
    substituteCoefficientVariables(g, substitutions),
    transformedG,
  )) {
    throw new Error("derived cubic coefficient action does not reconstruct g'");
  }

  return substitutions;
}

export function substituteCoefficientVariables(polynomial, substitutions) {
  if (
    !Array.isArray(substitutions) ||
    substitutions.length !== COEFFICIENT_COUNT
  ) {
    throw new RangeError(
      `coefficient substitutions must have length ${COEFFICIENT_COUNT}`,
    );
  }

  const caches = substitutions.map(() => new Map([[0, constantPolynomial(1n)]]));
  function substitutionPower(index, exponent) {
    const cache = caches[index];
    if (!cache.has(exponent)) {
      cache.set(exponent, powerPolynomial(substitutions[index], exponent));
    }
    return cache.get(exponent);
  }

  let result = zeroPolynomial();
  for (const term of serializePolynomial(polynomial)) {
    const exponents = [...term.exponents];
    const receiverExponents = Array(POLYNOMIAL_VARIABLES.length).fill(0);
    receiverExponents[U_INDEX] = exponents[U_INDEX];
    receiverExponents[V_INDEX] = exponents[V_INDEX];

    let transformedTerm = monomialPolynomial(
      receiverExponents,
      parseRationalText(term.coefficient),
    );
    for (let index = 0; index < COEFFICIENT_COUNT; index += 1) {
      const exponent = exponents[index];
      if (exponent > 0) {
        transformedTerm = multiplyPolynomials(
          transformedTerm,
          substitutionPower(index, exponent),
        );
      }
    }
    result = addPolynomials(result, transformedTerm);
  }
  return result;
}

export function verifyCovariantEquivariance(polynomial, matrix) {
  const substitutions = deriveCoefficientAction(matrix);
  const coefficientSide = substituteCoefficientVariables(
    polynomial,
    substitutions,
  );
  const variableSide = substituteUv(polynomial, matrix);
  return {
    passed: polynomialsEqual(coefficientSide, variableSide),
    coefficientSideSha256: polynomialSha256(coefficientSide),
    variableSideSha256: polynomialSha256(variableSide),
  };
}

function sha256Lines(lines) {
  return createHash("sha256")
    .update(lines.join("\n"), "utf8")
    .digest("hex");
}

export function buildEquivarianceReport() {
  const modular = buildModularS3QuotientRepresentatives();
  const matrices = buildModularRepresentativeMatrices();
  const basis = buildCovariantBasis();
  const perRepresentative = [];

  for (const label of S3_LABELS) {
    const matrix = matrices.get(label);
    const substitutions = deriveCoefficientAction(matrix);
    const substitutionHash = sha256Lines(
      substitutions.map(canonicalPolynomialText),
    );
    const transformedHashes = [];

    for (const generator of basis) {
      const coefficientSide = substituteCoefficientVariables(
        generator.polynomial,
        substitutions,
      );
      const variableSide = substituteUv(generator.polynomial, matrix);
      if (!polynomialsEqual(coefficientSide, variableSide)) {
        throw new Error(
          `covariant equivariance failed for ${generator.label} under ${label}`,
        );
      }
      transformedHashes.push(
        `${generator.index}:${generator.label}:${polynomialSha256(variableSide)}`,
      );
    }

    perRepresentative.push({
      label,
      modularMatrix: matrix.map((row) => [...row]),
      mod2Key: mod2Key(matrix),
      coefficientActionSha256: substitutionHash,
      transformedBasisSha256: sha256Lines(transformedHashes),
      checkedGenerators: basis.length,
      allPassed: true,
    });
  }

  return {
    law: "Psi(alpha';u,v)=Psi(alpha;u',v')",
    representatives: perRepresentative,
    checkedRepresentatives: perRepresentative.length,
    checkedGenerators: basis.length,
    exactChecks: perRepresentative.length * basis.length,
    allPassed: true,
    quotientMultiplicationTable: modular.multiplicationTable,
  };
}

export function buildS3EquivarianceHarnessSummary() {
  const d4 = buildD4S3Orbit();
  const modular = buildModularS3QuotientRepresentatives();
  if (
    JSON.stringify(d4.multiplicationTable) !==
    JSON.stringify(modular.multiplicationTable)
  ) {
    throw new Error("D4/F4 and modular quotient multiplication tables disagree");
  }

  const equivariance = buildEquivarianceReport();
  return {
    schema: HARNESS_SCHEMA_ID,
    harnessId: HARNESS_ID,
    harnessVersion: HARNESS_VERSION,
    quotientIdentification: {
      modular: "SL2(Z)/Gamma(2)~=S3",
      d4: "W(F4)/W(D4)~=S3",
      generatorCorrespondence: ["gS<->wS", "gT<->wT"],
      warning:
        "The six modular matrices are canonical SL2(Z) representatives of quotient classes; they are not asserted to form a literal six-element subgroup upstairs.",
    },
    d4Orbit: d4,
    modularQuotient: modular,
    multiplicationTablesMatch: true,
    equivariance,
    claimBoundary:
      "The harness verifies the exact six-element D4/F4 triality quotient orbit and exact SL2(C) covariant equivariance for the 15 constructed binary covariants under six canonical SL2(Z) representatives. It does not claim that the quotient classes themselves are a six-element subgroup of SL2(Z), and it introduces no sonification mapping.",
  };
}
