// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this file,
// You can obtain one at https://mozilla.org/MPL/2.0/.
// SPDX-License-Identifier: MPL-2.0
// Copyright (c) 2026 Trent Slade / QSOL-IMC.

/**
 * D4-TIA-COV v0.1.0 exact classical covariant algebra engine.
 *
 * Implements the binary quadratic/cubic convention and normalized
 * transvectant of Sakai, arXiv:2504.00546v2, eqs. (4.1), (5.1),
 * (5.7)-(5.10), and Theorem 5.2. Arithmetic is exact over Q.
 */

import { createHash } from "node:crypto";

import {
  D4_TRIALITY_INVARIANT_GENERATORS,
} from "./d4-triality-reference.mjs";

export const ENGINE_ID = "D4-TIA-COV";
export const ENGINE_VERSION = "0.1.0";
export const ENGINE_SUMMARY_SCHEMA_ID = "qsol.d4-tia-cov.engine-summary/v0.1";

export const POLYNOMIAL_VARIABLES = Object.freeze([
  "a0",
  "a1",
  "a2",
  "b0",
  "b1",
  "b2",
  "b3",
  "u",
  "v",
]);

const A_INDICES = Object.freeze([0, 1, 2]);
const B_INDICES = Object.freeze([3, 4, 5, 6]);
const U_INDEX = 7;
const V_INDEX = 8;
const UV_INDICES = Object.freeze([U_INDEX, V_INDEX]);

function absBigInt(value) {
  return value < 0n ? -value : value;
}

function gcdBigInt(left, right) {
  let a = absBigInt(left);
  let b = absBigInt(right);
  while (b !== 0n) [a, b] = [b, a % b];
  return a;
}

export function rational(numerator, denominator = 1n) {
  if (typeof numerator !== "bigint" || typeof denominator !== "bigint") {
    throw new TypeError("rational numerator and denominator must be bigint");
  }
  if (denominator === 0n) throw new RangeError("rational denominator must be nonzero");
  if (numerator === 0n) return Object.freeze({ numerator: 0n, denominator: 1n });

  const sign = denominator < 0n ? -1n : 1n;
  const divisor = gcdBigInt(numerator, denominator);
  return Object.freeze({
    numerator: sign * (numerator / divisor),
    denominator: absBigInt(denominator) / divisor,
  });
}

function asRational(value) {
  if (typeof value === "bigint") return rational(value);
  if (
    value &&
    typeof value === "object" &&
    typeof value.numerator === "bigint" &&
    typeof value.denominator === "bigint"
  ) {
    return rational(value.numerator, value.denominator);
  }
  throw new TypeError("coefficient must be bigint or rational");
}

function rationalAdd(left, right) {
  return rational(
    left.numerator * right.denominator + right.numerator * left.denominator,
    left.denominator * right.denominator,
  );
}

function rationalMultiply(left, right) {
  return rational(
    left.numerator * right.numerator,
    left.denominator * right.denominator,
  );
}

function rationalNegate(value) {
  return rational(-value.numerator, value.denominator);
}

function rationalIsZero(value) {
  return value.numerator === 0n;
}

export function rationalToString(value) {
  const normalized = asRational(value);
  return normalized.denominator === 1n
    ? normalized.numerator.toString()
    : `${normalized.numerator}/${normalized.denominator}`;
}

function zeroExponents() {
  return Array(POLYNOMIAL_VARIABLES.length).fill(0);
}

function validateExponents(exponents) {
  if (!Array.isArray(exponents) || exponents.length !== POLYNOMIAL_VARIABLES.length) {
    throw new TypeError(
      `exponents must have length ${POLYNOMIAL_VARIABLES.length}`,
    );
  }
  for (const exponent of exponents) {
    if (!Number.isSafeInteger(exponent) || exponent < 0) {
      throw new RangeError("polynomial exponents must be non-negative safe integers");
    }
  }
  return exponents;
}

function exponentKey(exponents) {
  return validateExponents(exponents).join(",");
}

function exponentsFromKey(key) {
  return key.split(",").map((value) => Number.parseInt(value, 10));
}

function addTerm(terms, exponents, coefficient) {
  const value = asRational(coefficient);
  if (rationalIsZero(value)) return;

  const key = exponentKey(exponents);
  const previous = terms.get(key);
  const next = previous ? rationalAdd(previous, value) : value;
  if (rationalIsZero(next)) terms.delete(key);
  else terms.set(key, next);
}

export function zeroPolynomial() {
  return new Map();
}

export function monomialPolynomial(exponents, coefficient = 1n) {
  const result = zeroPolynomial();
  addTerm(result, [...validateExponents(exponents)], coefficient);
  return result;
}

export function constantPolynomial(value = 1n) {
  return monomialPolynomial(zeroExponents(), value);
}

export function addPolynomials(...polynomials) {
  const result = zeroPolynomial();
  for (const polynomial of polynomials) {
    if (!(polynomial instanceof Map)) throw new TypeError("polynomial must be a Map");
    for (const [key, coefficient] of polynomial.entries()) {
      addTerm(result, exponentsFromKey(key), coefficient);
    }
  }
  return result;
}

export function scalePolynomial(polynomial, scalar) {
  if (!(polynomial instanceof Map)) throw new TypeError("polynomial must be a Map");
  const factor = asRational(scalar);
  if (rationalIsZero(factor)) return zeroPolynomial();

  const result = zeroPolynomial();
  for (const [key, coefficient] of polynomial.entries()) {
    addTerm(
      result,
      exponentsFromKey(key),
      rationalMultiply(coefficient, factor),
    );
  }
  return result;
}

export function multiplyPolynomials(left, right) {
  if (!(left instanceof Map) || !(right instanceof Map)) {
    throw new TypeError("polynomial must be a Map");
  }
  const result = zeroPolynomial();
  for (const [leftKey, leftCoefficient] of left.entries()) {
    const leftExponents = exponentsFromKey(leftKey);
    for (const [rightKey, rightCoefficient] of right.entries()) {
      const rightExponents = exponentsFromKey(rightKey);
      const exponents = leftExponents.map(
        (value, index) => value + rightExponents[index],
      );
      addTerm(
        result,
        exponents,
        rationalMultiply(leftCoefficient, rightCoefficient),
      );
    }
  }
  return result;
}

export function powerPolynomial(polynomial, exponent) {
  if (!Number.isSafeInteger(exponent) || exponent < 0) {
    throw new RangeError("polynomial exponent must be a non-negative safe integer");
  }
  let result = constantPolynomial(1n);
  let base = polynomial;
  let power = exponent;
  while (power > 0) {
    if (power % 2 === 1) result = multiplyPolynomials(result, base);
    power = Math.floor(power / 2);
    if (power > 0) base = multiplyPolynomials(base, base);
  }
  return result;
}

function fallingFactorial(value, count) {
  let result = 1n;
  for (let index = 0; index < count; index += 1) {
    result *= BigInt(value - index);
  }
  return result;
}

export function differentiatePolynomial(polynomial, variableIndex, count = 1) {
  if (!(polynomial instanceof Map)) throw new TypeError("polynomial must be a Map");
  if (
    !Number.isSafeInteger(variableIndex) ||
    variableIndex < 0 ||
    variableIndex >= POLYNOMIAL_VARIABLES.length
  ) {
    throw new RangeError("variableIndex is outside the polynomial variable set");
  }
  if (!Number.isSafeInteger(count) || count < 0) {
    throw new RangeError("derivative count must be a non-negative safe integer");
  }
  if (count === 0) return addPolynomials(polynomial);

  const result = zeroPolynomial();
  for (const [key, coefficient] of polynomial.entries()) {
    const exponents = exponentsFromKey(key);
    const exponent = exponents[variableIndex];
    if (exponent < count) continue;
    exponents[variableIndex] -= count;
    addTerm(
      result,
      exponents,
      rationalMultiply(coefficient, rational(fallingFactorial(exponent, count))),
    );
  }
  return result;
}

function homogeneousDegree(polynomial, indices, name) {
  if (!(polynomial instanceof Map) || polynomial.size === 0) {
    throw new RangeError(`${name} is undefined for the zero polynomial`);
  }
  let degree = null;
  for (const key of polynomial.keys()) {
    const exponents = exponentsFromKey(key);
    const value = indices.reduce((sum, index) => sum + exponents[index], 0);
    if (degree === null) degree = value;
    else if (degree !== value) {
      throw new Error(`polynomial is not homogeneous in ${name}`);
    }
  }
  return degree;
}

export function covariantOrder(polynomial) {
  return homogeneousDegree(polynomial, UV_INDICES, "u,v");
}

function factorial(value) {
  if (!Number.isSafeInteger(value) || value < 0) {
    throw new RangeError("factorial requires a non-negative safe integer");
  }
  let result = 1n;
  for (let factor = 2; factor <= value; factor += 1) {
    result *= BigInt(factor);
  }
  return result;
}

function binomial(n, k) {
  if (
    !Number.isSafeInteger(n) ||
    !Number.isSafeInteger(k) ||
    n < 0 ||
    k < 0 ||
    k > n
  ) {
    throw new RangeError("invalid binomial arguments");
  }
  return factorial(n) / (factorial(k) * factorial(n - k));
}

/**
 * Sakai eq. (5.1):
 * (F,G)_r = ((m-r)!(n-r)!)/(m!n!) *
 * sum_j (-1)^j C(r,j)
 * d_u^(r-j)d_v^j F * d_u^j d_v^(r-j) G.
 */
export function transvectant(left, right, r) {
  if (!Number.isSafeInteger(r) || r < 0) {
    throw new RangeError("transvectant order must be a non-negative safe integer");
  }
  const m = covariantOrder(left);
  const n = covariantOrder(right);
  if (r > Math.min(m, n)) {
    throw new RangeError("transvectant order exceeds one of the binary-form orders");
  }

  let sum = zeroPolynomial();
  for (let j = 0; j <= r; j += 1) {
    const leftDerivative = differentiatePolynomial(
      differentiatePolynomial(left, U_INDEX, r - j),
      V_INDEX,
      j,
    );
    const rightDerivative = differentiatePolynomial(
      differentiatePolynomial(right, U_INDEX, j),
      V_INDEX,
      r - j,
    );
    const sign = j % 2 === 0 ? 1n : -1n;
    const scalar = rational(sign * binomial(r, j));
    sum = addPolynomials(
      sum,
      scalePolynomial(
        multiplyPolynomials(leftDerivative, rightDerivative),
        scalar,
      ),
    );
  }

  const normalization = rational(
    factorial(m - r) * factorial(n - r),
    factorial(m) * factorial(n),
  );
  return scalePolynomial(sum, normalization);
}

function sourceCoefficientTerm(variableIndex, uExponent, vExponent) {
  const exponents = zeroExponents();
  exponents[variableIndex] = 1;
  exponents[U_INDEX] = uExponent;
  exponents[V_INDEX] = vExponent;
  return monomialPolynomial(exponents);
}

export function buildSourceBinaryForms() {
  const f = addPolynomials(
    sourceCoefficientTerm(0, 2, 0),
    sourceCoefficientTerm(1, 1, 1),
    sourceCoefficientTerm(2, 0, 2),
  );
  const g = addPolynomials(
    sourceCoefficientTerm(3, 3, 0),
    sourceCoefficientTerm(4, 2, 1),
    sourceCoefficientTerm(5, 1, 2),
    sourceCoefficientTerm(6, 0, 3),
  );
  return { f, g };
}

function compareExponentArrays(left, right) {
  for (let index = 0; index < left.length; index += 1) {
    const difference = left[index] - right[index];
    if (difference !== 0) return difference;
  }
  return 0;
}

export function serializePolynomial(polynomial) {
  if (!(polynomial instanceof Map)) throw new TypeError("polynomial must be a Map");
  return [...polynomial.entries()]
    .map(([key, coefficient]) => ({
      exponents: exponentsFromKey(key),
      coefficient: rationalToString(coefficient),
    }))
    .sort((left, right) =>
      compareExponentArrays(left.exponents, right.exponents),
    );
}

export function canonicalPolynomialText(polynomial) {
  return serializePolynomial(polynomial)
    .map(
      (term) => `${term.coefficient}|${term.exponents.join(",")}`,
    )
    .join("\n");
}

export function polynomialSha256(polynomial) {
  return createHash("sha256")
    .update(canonicalPolynomialText(polynomial), "utf8")
    .digest("hex");
}

export function isZeroPolynomial(polynomial) {
  return polynomial instanceof Map && polynomial.size === 0;
}

export function polynomialsEqual(left, right) {
  return canonicalPolynomialText(left) === canonicalPolynomialText(right);
}

export function deriveCovariantGrade(polynomial) {
  const quadraticDegree = homogeneousDegree(polynomial, A_INDICES, "alpha coefficients");
  const cubicDegree = homogeneousDegree(polynomial, B_INDICES, "beta coefficients");
  const order = covariantOrder(polynomial);
  const covariantDegree = quadraticDegree + cubicDegree;
  const polynomialDegree = 2 * quadraticDegree + 3 * cubicDegree - order;
  if (polynomialDegree < 0) {
    throw new Error("derived D4 polynomial degree is negative");
  }
  const modularWeight =
    4 * quadraticDegree + 6 * cubicDegree + polynomialDegree;

  return Object.freeze({
    quadraticDegree,
    cubicDegree,
    covariantDegree,
    polynomialDegree,
    modularWeight,
    covariantOrder: order,
  });
}

export function buildCovariantBasis() {
  const { f, g } = buildSourceBinaryForms();
  const quadraticDiscriminant = transvectant(f, f, 2);
  const P = transvectant(g, g, 2);
  const Q = transvectant(g, P, 1);
  const cubicDiscriminant = transvectant(P, P, 2);

  const f2 = powerPolynomial(f, 2);
  const f3 = powerPolynomial(f, 3);
  const g2 = powerPolynomial(g, 2);

  const basis = [
    ["f", f],
    ["g", g],
    ["(f,g)_1", transvectant(f, g, 1)],
    ["quadratic-discriminant", quadraticDiscriminant],
    ["(f,g)_2", transvectant(f, g, 2)],
    ["P=(g,g)_2", P],
    ["(f^2,g)_3", transvectant(f2, g, 3)],
    ["(f,P)_1", transvectant(f, P, 1)],
    ["Q=(g,P)_1", Q],
    ["(f,P)_2", transvectant(f, P, 2)],
    ["(f,Q)_2", transvectant(f, Q, 2)],
    ["(f^3,g^2)_6", transvectant(f3, g2, 6)],
    ["cubic-discriminant=(P,P)_2", cubicDiscriminant],
    ["(f^2,Q)_3", transvectant(f2, Q, 3)],
    ["(f^3,gQ)_6", transvectant(f3, multiplyPolynomials(g, Q), 6)],
  ].map(([label, polynomial], index) => ({
    index: index + 1,
    label,
    polynomial,
    grade: deriveCovariantGrade(polynomial),
  }));

  if (basis.length !== D4_TRIALITY_INVARIANT_GENERATORS.length) {
    throw new Error("covariant basis and reference ledger have different lengths");
  }
  for (let index = 0; index < basis.length; index += 1) {
    const actual = basis[index];
    const expected = D4_TRIALITY_INVARIANT_GENERATORS[index];
    if (actual.label !== expected.label || actual.index !== expected.index) {
      throw new Error(`covariant basis order mismatch at row ${index + 1}`);
    }
    const gradePairs = [
      ["quadraticDegree", expected.quadraticDegree],
      ["cubicDegree", expected.cubicDegree],
      ["polynomialDegree", expected.polynomialDegree],
      ["modularWeight", expected.modularWeight],
      ["covariantOrder", expected.covariantOrder],
    ];
    for (const [field, expectedValue] of gradePairs) {
      if (actual.grade[field] !== expectedValue) {
        throw new Error(
          `${actual.label} derived ${field}=${actual.grade[field]} but ledger records ${expectedValue}`,
        );
      }
    }
  }

  return basis;
}

export function cubicSyzygyResidual() {
  const basis = buildCovariantBasis();
  const byLabel = new Map(basis.map((entry) => [entry.label, entry.polynomial]));
  const g = byLabel.get("g");
  const P = byLabel.get("P=(g,g)_2");
  const Q = byLabel.get("Q=(g,P)_1");
  const D = byLabel.get("cubic-discriminant=(P,P)_2");
  return addPolynomials(
    scalePolynomial(powerPolynomial(Q, 2), 2n),
    powerPolynomial(P, 3),
    multiplyPolynomials(powerPolynomial(g, 2), D),
  );
}

export function buildCovariantEngineSummary() {
  const basis = buildCovariantBasis();
  if (!isZeroPolynomial(cubicSyzygyResidual())) {
    throw new Error("published cubic syzygy failed");
  }

  return {
    schema: ENGINE_SUMMARY_SCHEMA_ID,
    engineId: ENGINE_ID,
    engineVersion: ENGINE_VERSION,
    sourceConvention: {
      quadratic: "f=sum_{i=0}^2 alpha_i u^(2-i) v^i",
      cubic: "g=sum_{i=0}^3 beta_i u^(3-i) v^i",
      transvectant:
        "(F,G)_r=((m-r)!(n-r)!)/(m!n!)*sum_{j=0}^r(-1)^j*C(r,j)*d_u^(r-j)d_v^j F*d_u^j d_v^(r-j) G",
    },
    generatorCount: basis.length,
    cubicSyzygy: "2*Q^2+P^3+g^2*D_g=0",
    generators: basis.map((entry) => ({
      index: entry.index,
      label: entry.label,
      grade: { ...entry.grade },
      termCount: entry.polynomial.size,
      polynomialSha256: polynomialSha256(entry.polynomial),
    })),
  };
}
