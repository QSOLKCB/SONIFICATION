// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this file,
// You can obtain one at https://mozilla.org/MPL/2.0/.
// SPDX-License-Identifier: MPL-2.0
// Copyright (c) 2026 Trent Slade / QSOL-IMC.

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import test from "node:test";

import {
  CANONICAL_GENERATOR_WEIGHTS,
  D4_TRIALITY_NUMERATOR,
  DIMENSIONLESS_STEP_DELTA,
  MIDI_NOTE_MAXIMUM,
  MIDI_NOTE_MINIMUM,
  OUROBOROS_DIMENSION,
  PHASE_THETA_RAD,
  QUTRIT_ROOT_OF_UNITY,
  SCL_STENCIL,
  applyPermutationIndex,
  applyTriality,
  basisIndexFromMidiNote,
  buildGraphLaplacian,
  buildRootAdjacency,
  buildTernaryMidiCodebook,
  canonicalGeneratorMatrix,
  centeredQutritNumberDiagonal,
  classifyTrialityOrbits,
  complexIdentity,
  complexMatrixMultiply,
  complexMatrixPower,
  complexMultiply,
  curvatureDiagonal,
  dot,
  generateE8Roots,
  graphDegreePotential,
  graphSummary,
  maxComplexMatrixDifference,
  permuteDiagonal,
  phaseKickDiagonal,
  qutritHoppingLaplacian,
  qutritNumberDiagonal,
  qutritOperators,
  selectEtq101Basis,
  ternaryOuroborosState,
  trialityPermutation,
  twistedQutritStep,
  vectorKey,
} from "../src/etq-model.mjs";

const EXPECTED_BASIS_SHA256 =
  "97cfd1f087745422fd66d3640c7b86c3209593c4b53741018c08a5e9cdb15f6f";
const EXPECTED_ADJACENCY_SHA256 =
  "29ae0af5b1090c9de30f1efc25789060fb1791eb175d2afcd6888847f7fe6324";

function sha256(value) {
  return createHash("sha256").update(JSON.stringify(value)).digest("hex");
}

function assertClose(actual, expected, tolerance = 1e-12) {
  assert.ok(
    Math.abs(actual - expected) <= tolerance,
    `Expected ${actual} to be within ${tolerance} of ${expected}`,
  );
}

test("standard doubled-coordinate E8 construction has 240 exact roots", () => {
  const roots = generateE8Roots();
  assert.equal(roots.length, 240);
  assert.equal(new Set(roots.map(vectorKey)).size, 240);
  assert.deepEqual(new Set(roots.map((root) => dot(root, root))), new Set([8]));

  const integerRoots = roots.filter((root) => root.some((value) => value === 0));
  const halfIntegerRoots = roots.filter((root) => root.every((value) => value !== 0));
  assert.equal(integerRoots.length, 112);
  assert.equal(halfIntegerRoots.length, 128);
});

test("embedded D4 x D4 triality is orthogonal, order three, and E8-preserving", () => {
  // H H^T = 4I for A=H/2.
  for (let row = 0; row < 4; row += 1) {
    for (let column = 0; column < 4; column += 1) {
      assert.equal(
        dot(D4_TRIALITY_NUMERATOR[row], D4_TRIALITY_NUMERATOR[column]),
        row === column ? 4 : 0,
      );
    }
  }

  const roots = generateE8Roots();
  const rootSet = new Set(roots.map(vectorKey));
  for (const root of roots) {
    const once = applyTriality(root);
    const twice = applyTriality(once);
    const thrice = applyTriality(twice);
    assert.ok(rootSet.has(vectorKey(once)));
    assert.deepEqual(thrice, root);
  }
});

test("triality decomposition and canonical 101-state selector are stable", () => {
  const roots = generateE8Roots();
  const { fixed, triples } = classifyTrialityOrbits(roots);
  assert.equal(fixed.length, 12);
  assert.equal(triples.length, 76);
  assert.equal(fixed.length + 3 * triples.length, 240);

  const basis = selectEtq101Basis(roots);
  assert.equal(basis.length, OUROBOROS_DIMENSION);
  assert.equal(new Set(basis.map(vectorKey)).size, OUROBOROS_DIMENSION);
  assert.equal(sha256(basis), EXPECTED_BASIS_SHA256);

  const permutation = trialityPermutation();
  for (let index = 0; index < basis.length; index += 1) {
    const mappedIndex = permutation[index];
    assert.deepEqual(basis[mappedIndex], applyTriality(basis[index]));
    assert.equal(applyPermutationIndex(permutation, index, 3), index);
  }
});

test("permutation powers derive the selected orbit length and reject invalid input", () => {
  const fourCycle = [1, 2, 3, 0];
  assert.equal(applyPermutationIndex(fourCycle, 0, 3), 3);
  assert.equal(applyPermutationIndex(fourCycle, 0, 4), 0);
  assert.equal(applyPermutationIndex(fourCycle, 0, -1), 3);

  const mixedCycles = [1, 0, 3, 4, 2];
  assert.equal(applyPermutationIndex(mixedCycles, 0, 7), 1);
  assert.equal(applyPermutationIndex(mixedCycles, 2, 7), 3);

  assert.throws(() => applyPermutationIndex([], 0), /non-empty array/);
  assert.throws(() => applyPermutationIndex([1, 1], 0), /bijection/);
  assert.throws(() => applyPermutationIndex([1, 0], 2), /outside/);
  assert.throws(() => applyPermutationIndex([1, 0], 0, 0.5), /safe integer/);
});

test("selected E8 root graph matches the canonical fixtures", () => {
  const basis = selectEtq101Basis();
  const adjacency = buildRootAdjacency(basis);
  assert.equal(sha256(adjacency), EXPECTED_ADJACENCY_SHA256);
  assert.deepEqual(graphSummary(adjacency), {
    vertices: 101,
    edges: 1687,
    minimumDegree: 22,
    maximumDegree: 55,
    connected: true,
  });

  const permutation = trialityPermutation();
  for (let left = 0; left < adjacency.length; left += 1) {
    assert.equal(adjacency[left][left], 0);
    for (let right = 0; right < adjacency.length; right += 1) {
      assert.equal(adjacency[left][right], adjacency[right][left]);
      assert.equal(
        adjacency[permutation[left]][permutation[right]],
        adjacency[left][right],
      );
    }
  }

  const laplacian = buildGraphLaplacian(adjacency);
  for (const row of laplacian) {
    assert.equal(row.reduce((sum, value) => sum + value, 0), 0);
  }

  // Regression Rayleigh checks. A graph Laplacian is PSD analytically; these
  // vectors also catch sign errors in an implementation.
  const vectors = [
    Array.from({ length: 101 }, (_, index) => (index % 7) - 3),
    Array.from({ length: 101 }, (_, index) => Math.sin(index * 0.37)),
    Array.from({ length: 101 }, (_, index) => (index === 42 ? 1 : 0)),
  ];
  for (const vector of vectors) {
    let quadraticForm = 0;
    for (let row = 0; row < 101; row += 1) {
      for (let column = 0; column < 101; column += 1) {
        quadraticForm += vector[row] * laplacian[row][column] * vector[column];
      }
    }
    assert.ok(quadraticForm >= -1e-10);
  }
});

test("selected-graph degree potential is exact, centered, and triality invariant", () => {
  const adjacency = buildRootAdjacency(selectEtq101Basis());
  const potential = graphDegreePotential(adjacency);
  assert.equal(potential.degreeSum, 3374);
  assert.deepEqual(potential.meanDegree, { numerator: 3374, denominator: 101 });
  assert.equal(potential.normalizationDenominator, 2181);
  assert.equal(potential.numerators.reduce((sum, value) => sum + value, 0), 0);
  assert.equal(Math.max(...potential.numerators.map(Math.abs)), 2181);
  assertClose(Math.max(...potential.diagonal.map(Math.abs)), 1);

  const degreeDistribution = new Map();
  for (const degree of potential.degrees) {
    degreeDistribution.set(degree, (degreeDistribution.get(degree) ?? 0) + 1);
  }
  assert.deepEqual(Object.fromEntries(degreeDistribution), {
    22: 12,
    23: 6,
    30: 12,
    32: 24,
    33: 12,
    34: 6,
    40: 6,
    42: 12,
    43: 6,
    44: 3,
    55: 2,
  });

  const permutation = trialityPermutation();
  for (let index = 0; index < OUROBOROS_DIMENSION; index += 1) {
    assert.equal(
      potential.numerators[permutation[index]],
      potential.numerators[index],
    );
  }

  assert.ok(
    adjacency.some((row, rowIndex) =>
      row.some(
        (edge, columnIndex) =>
          edge === 1 &&
          potential.numerators[rowIndex] !== potential.numerators[columnIndex],
      ),
    ),
    "the diagonal degree potential should not commute with the irregular graph Laplacian",
  );
});

test("canonical v2 generator is real symmetric and triality invariant", () => {
  assert.deepEqual(CANONICAL_GENERATOR_WEIGHTS, {
    e8RootGraph: 11 / 20,
    qutritHopping: 1 / 4,
    graphDegreePotential: 1 / 5,
    sclStatic: 0,
    qutritNumber: 0,
    ouroborosRing: 0,
  });
  assertClose(DIMENSIONLESS_STEP_DELTA, (2 * Math.PI) / 303);

  const qutritLaplacian = qutritHoppingLaplacian();
  assert.ok(qutritLaplacian[0].every((value) => value === 0));
  assert.ok(qutritLaplacian[1].every((value) => value === 0));
  for (let row = 2; row < OUROBOROS_DIMENSION; row += 1) {
    const orbitStart = 2 + 3 * Math.floor((row - 2) / 3);
    assertClose(qutritLaplacian[row].reduce((sum, value) => sum + value, 0), 0);
    for (let column = 0; column < OUROBOROS_DIMENSION; column += 1) {
      const inOrbit = column >= orbitStart && column < orbitStart + 3;
      const expected = !inOrbit ? 0 : row === column ? 2 / 3 : -1 / 3;
      assertClose(qutritLaplacian[row][column], expected);
    }
  }

  const generator = canonicalGeneratorMatrix();
  const permutation = trialityPermutation();
  assert.equal(generator.length, OUROBOROS_DIMENSION);
  for (let row = 0; row < OUROBOROS_DIMENSION; row += 1) {
    assert.equal(generator[row].length, OUROBOROS_DIMENSION);
    for (let column = 0; column < OUROBOROS_DIMENSION; column += 1) {
      assert.ok(Number.isFinite(generator[row][column]));
      assertClose(generator[row][column], generator[column][row], 1e-15);
      assertClose(
        generator[permutation[row]][permutation[column]],
        generator[row][column],
        1e-15,
      );
    }
  }
});

test("qutrit number and SCL curvature operators obey the declared identity", () => {
  assert.deepEqual(SCL_STENCIL, [1, -2, 1]);
  const number = qutritNumberDiagonal();
  const centered = centeredQutritNumberDiagonal();
  const curvature = curvatureDiagonal();
  assert.equal(number.length, 101);
  assert.equal(curvature.length, 101);
  assert.equal(curvature.reduce((sum, value) => sum + value, 0), 0);

  const multiplicities = new Map();
  for (const value of curvature) {
    multiplicities.set(value, (multiplicities.get(value) ?? 0) + 1);
  }
  assert.deepEqual(
    Object.fromEntries([...multiplicities.entries()].sort(([a], [b]) => a - b)),
    { "-2": 33, "0": 2, "1": 66 },
  );

  for (let index = 0; index < 101; index += 1) {
    const projector = index < 2 ? 0 : 1;
    assert.equal(
      curvature[index],
      3 * (number[index] - projector) ** 2 - 2 * projector,
    );
    assert.equal(centered[index], number[index] - projector);
  }

  const permutation = trialityPermutation();
  const orbitZero = curvature;
  const orbitOne = permuteDiagonal(curvature, permutation, 1);
  const orbitTwo = permuteDiagonal(curvature, permutation, 2);
  for (let index = 0; index < 101; index += 1) {
    assert.equal(orbitZero[index] + orbitOne[index] + orbitTwo[index], 0);
  }
});

test("complex matrix multiplication rejects malformed and incompatible shapes", () => {
  const one = { re: 1, im: 0 };
  assert.throws(() => complexMatrixMultiply([], [[one]]), /non-empty matrix/);
  assert.throws(
    () => complexMatrixMultiply([[one], [one, one]], [[one]]),
    /rectangular/,
  );
  assert.throws(
    () => complexMatrixMultiply([[one, one]], [[one]]),
    /incompatible matrix dimensions 1x2 and 1x1/,
  );
});

test("qutrit Weyl operators satisfy X^3=Z^3=I and ZX=zeta XZ", () => {
  const { X, Z } = qutritOperators();
  const identity = complexIdentity(3);
  assert.ok(maxComplexMatrixDifference(complexMatrixPower(X, 3), identity) < 1e-12);
  assert.ok(maxComplexMatrixDifference(complexMatrixPower(Z, 3), identity) < 1e-12);

  const ZX = complexMatrixMultiply(Z, X);
  const XZ = complexMatrixMultiply(X, Z).map((row) =>
    row.map((value) => complexMultiply(QUTRIT_ROOT_OF_UNITY, value)),
  );
  assert.ok(maxComplexMatrixDifference(ZX, XZ) < 1e-12);
});

test("theta=pi/2 phase kick is unitary and twisted qutrit step has order three", () => {
  for (const value of phaseKickDiagonal(PHASE_THETA_RAD)) {
    assertClose(Math.hypot(value.re, value.im), 1);
  }

  const step = twistedQutritStep(PHASE_THETA_RAD);
  const cubed = complexMatrixPower(step, 3);
  assert.ok(maxComplexMatrixDifference(cubed, complexIdentity(3)) < 1e-12);
});

test("ternary/SCL Ouroboros state is normalized with explicit singlet phases", () => {
  const state = ternaryOuroborosState();
  const normSquared = state.reduce(
    (sum, amplitude) => sum + amplitude.re ** 2 + amplitude.im ** 2,
    0,
  );
  assertClose(normSquared, 1);

  const scale = Math.sqrt(OUROBOROS_DIMENSION);
  assertClose(state[0].re * scale, 1);
  assertClose(state[0].im * scale, 0);
  assertClose(state[1].re * scale, 1);
  assertClose(state[1].im * scale, 0);

  const expectedPhases = [
    -PHASE_THETA_RAD,
    (2 * Math.PI) / 3 + 2 * PHASE_THETA_RAD,
    (4 * Math.PI) / 3 - PHASE_THETA_RAD,
  ];
  for (let qutritLabel = 0; qutritLabel < 3; qutritLabel += 1) {
    assertClose(state[2 + qutritLabel].re * scale, Math.cos(expectedPhases[qutritLabel]));
    assertClose(state[2 + qutritLabel].im * scale, Math.sin(expectedPhases[qutritLabel]));
  }
});

test("ternary MIDI codebook is a bijective symbolic encoding of all 101 states", () => {
  const codebook = buildTernaryMidiCodebook();
  assert.equal(codebook.length, OUROBOROS_DIMENSION);
  assert.equal(new Set(codebook.map((entry) => entry.midiNote)).size, 101);
  assert.ok(
    codebook.every(
      (entry) =>
        entry.midiNote >= MIDI_NOTE_MINIMUM && entry.midiNote <= MIDI_NOTE_MAXIMUM,
    ),
  );
  assert.deepEqual(
    codebook.slice(0, 2).map((entry) => entry.midiNote),
    [13, 113],
  );

  const expectedLanes = {
    low: [14, 46],
    mid: [47, 79],
    high: [80, 112],
  };
  for (const [lane, expectedRange] of Object.entries(expectedLanes)) {
    const notes = codebook
      .filter((entry) => entry.lane === lane)
      .map((entry) => entry.midiNote);
    assert.equal(notes.length, 33);
    assert.deepEqual([Math.min(...notes), Math.max(...notes)], expectedRange);
  }

  for (const entry of codebook) {
    assert.equal(basisIndexFromMidiNote(entry.midiNote), entry.basisIndex);
  }
  for (const note of [0, 12, 114, 127]) {
    assert.equal(basisIndexFromMidiNote(note), null);
  }

  const byBasis = new Map(codebook.map((entry) => [entry.basisIndex, entry]));
  const permutation = trialityPermutation();
  for (const entry of codebook.filter((candidate) => candidate.qutritLabel !== null)) {
    const mapped = byBasis.get(permutation[entry.basisIndex]);
    const offset = entry.midiNote - 14;
    const mappedOffset = mapped.midiNote - 14;
    assert.equal(mappedOffset, (offset + 33) % 99);
  }
});
