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
  DIMENSIONLESS_STEP_DENOMINATOR,
  MIDI_NOTE_MAXIMUM,
  MIDI_NOTE_MINIMUM,
  OUROBOROS_DIMENSION,
  PHASE_THETA_RAD,
  QUTRIT_DIMENSION,
  QUTRIT_ROOT_OF_UNITY,
  QUTRIT_SUBSPACE_DIMENSION,
  SCL_STENCIL,
  SELECTED_FIXED_ROOTS,
  SELECTED_TRIALITY_ORBITS,
  TERNARY_MIDI_LAYOUT,
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
  midiNoteForTernaryState,
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
    vertices: OUROBOROS_DIMENSION,
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
    Array.from({ length: OUROBOROS_DIMENSION }, (_, index) => (index % 7) - 3),
    Array.from(
      { length: OUROBOROS_DIMENSION },
      (_, index) => Math.sin(index * 0.37),
    ),
    Array.from(
      { length: OUROBOROS_DIMENSION },
      (_, index) => (index === 42 ? 1 : 0),
    ),
  ];
  for (const vector of vectors) {
    let quadraticForm = 0;
    for (let row = 0; row < OUROBOROS_DIMENSION; row += 1) {
      for (let column = 0; column < OUROBOROS_DIMENSION; column += 1) {
        quadraticForm += vector[row] * laplacian[row][column] * vector[column];
      }
    }
    assert.ok(quadraticForm >= -1e-10);
  }
});

test("selected-graph degree potential is exact, centered, and triality invariant", () => {
  const adjacency = buildRootAdjacency(selectEtq101Basis());
  const potential = graphDegreePotential(adjacency);
  const summary = graphSummary(adjacency);
  assert.equal(potential.degreeSum, 2 * summary.edges);
  assert.deepEqual(potential.meanDegree, {
    numerator: potential.degreeSum,
    denominator: OUROBOROS_DIMENSION,
  });
  assert.equal(potential.traceNumerator, 0);
  assert.equal(
    potential.numerators.reduce((sum, value) => sum + value, 0),
    potential.traceNumerator,
  );
  assert.equal(
    potential.normalizationDenominator,
    Math.max(...potential.numerators.map(Math.abs)),
  );
  assert.equal(
    potential.maximumAbsoluteNumerator,
    potential.normalizationDenominator,
  );
  assertClose(Math.max(...potential.diagonal.map(Math.abs)), 1);

  const degreeDistribution = new Map();
  for (const degree of potential.degrees) {
    degreeDistribution.set(degree, (degreeDistribution.get(degree) ?? 0) + 1);
  }
  const expectedDistribution = [...degreeDistribution.entries()].sort(
    ([left], [right]) => left - right,
  );
  assert.deepEqual(potential.degreeDistribution, expectedDistribution);
  assert.equal(
    potential.degreeDistribution.reduce(
      (count, [, multiplicity]) => count + multiplicity,
      0,
    ),
    OUROBOROS_DIMENSION,
  );
  assert.equal(
    potential.expression,
    `V_degree[j,j]=(${OUROBOROS_DIMENSION}*degree_j-` +
      `${potential.degreeSum})/${potential.normalizationDenominator}`,
  );

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
  assertClose(
    DIMENSIONLESS_STEP_DELTA,
    (2 * Math.PI) / DIMENSIONLESS_STEP_DENOMINATOR,
  );

  const qutritLaplacian = qutritHoppingLaplacian();
  for (let row = 0; row < SELECTED_FIXED_ROOTS; row += 1) {
    assert.ok(qutritLaplacian[row].every((value) => value === 0));
  }
  for (let row = SELECTED_FIXED_ROOTS; row < OUROBOROS_DIMENSION; row += 1) {
    const orbitStart =
      SELECTED_FIXED_ROOTS +
      QUTRIT_DIMENSION *
        Math.floor((row - SELECTED_FIXED_ROOTS) / QUTRIT_DIMENSION);
    assertClose(qutritLaplacian[row].reduce((sum, value) => sum + value, 0), 0);
    for (let column = 0; column < OUROBOROS_DIMENSION; column += 1) {
      const inOrbit =
        column >= orbitStart && column < orbitStart + QUTRIT_DIMENSION;
      const expected = !inOrbit
        ? 0
        : row === column
          ? (QUTRIT_DIMENSION - 1) / QUTRIT_DIMENSION
          : -1 / QUTRIT_DIMENSION;
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
  assert.equal(number.length, OUROBOROS_DIMENSION);
  assert.equal(curvature.length, OUROBOROS_DIMENSION);
  assert.equal(curvature.reduce((sum, value) => sum + value, 0), 0);

  const multiplicities = new Map();
  for (const value of curvature) {
    multiplicities.set(value, (multiplicities.get(value) ?? 0) + 1);
  }
  const expectedMultiplicities = new Map([[0, SELECTED_FIXED_ROOTS]]);
  for (const value of SCL_STENCIL) {
    expectedMultiplicities.set(
      value,
      (expectedMultiplicities.get(value) ?? 0) + SELECTED_TRIALITY_ORBITS,
    );
  }
  assert.deepEqual(
    [...multiplicities.entries()].sort(([a], [b]) => a - b),
    [...expectedMultiplicities.entries()].sort(([a], [b]) => a - b),
  );

  for (let index = 0; index < OUROBOROS_DIMENSION; index += 1) {
    const projector = index < SELECTED_FIXED_ROOTS ? 0 : 1;
    assert.equal(
      curvature[index],
      QUTRIT_DIMENSION * (number[index] - projector) ** 2 -
        (QUTRIT_DIMENSION - 1) * projector,
    );
    assert.equal(centered[index], number[index] - projector);
  }

  const permutation = trialityPermutation();
  const orbitZero = curvature;
  const orbitOne = permuteDiagonal(curvature, permutation, 1);
  const orbitTwo = permuteDiagonal(curvature, permutation, 2);
  for (let index = 0; index < OUROBOROS_DIMENSION; index += 1) {
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
  const identity = complexIdentity(QUTRIT_DIMENSION);
  assert.ok(
    maxComplexMatrixDifference(
      complexMatrixPower(X, QUTRIT_DIMENSION),
      identity,
    ) < 1e-12,
  );
  assert.ok(
    maxComplexMatrixDifference(
      complexMatrixPower(Z, QUTRIT_DIMENSION),
      identity,
    ) < 1e-12,
  );

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
  const cubed = complexMatrixPower(step, QUTRIT_DIMENSION);
  assert.ok(
    maxComplexMatrixDifference(cubed, complexIdentity(QUTRIT_DIMENSION)) <
      1e-12,
  );
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

  for (let qutritLabel = 0; qutritLabel < QUTRIT_DIMENSION; qutritLabel += 1) {
    const expectedPhase =
      (2 * Math.PI * qutritLabel) / QUTRIT_DIMENSION -
      PHASE_THETA_RAD * SCL_STENCIL[qutritLabel];
    const index = SELECTED_FIXED_ROOTS + qutritLabel;
    assertClose(state[index].re * scale, Math.cos(expectedPhase));
    assertClose(state[index].im * scale, Math.sin(expectedPhase));
  }
});

test("ternary MIDI codebook is a bijective symbolic encoding of all selected states", () => {
  const codebook = buildTernaryMidiCodebook();
  assert.equal(codebook.length, OUROBOROS_DIMENSION);
  const occupiedNotes = new Set(codebook.map((entry) => entry.midiNote));
  assert.equal(occupiedNotes.size, OUROBOROS_DIMENSION);
  assert.ok(
    codebook.every(
      (entry) =>
        entry.midiNote >= MIDI_NOTE_MINIMUM && entry.midiNote <= MIDI_NOTE_MAXIMUM,
    ),
  );
  assert.deepEqual(
    codebook
      .filter((entry) => entry.stateType === "fixed-singlet")
      .map((entry) => entry.midiNote),
    TERNARY_MIDI_LAYOUT.fixedSingletNotes,
  );
  assert.equal(
    TERNARY_MIDI_LAYOUT.windowMinimum,
    MIDI_NOTE_MINIMUM +
      Math.floor(
        (TERNARY_MIDI_LAYOUT.noteCount - TERNARY_MIDI_LAYOUT.stateCount) / 2,
      ),
  );
  assert.equal(
    TERNARY_MIDI_LAYOUT.windowMaximum -
      TERNARY_MIDI_LAYOUT.windowMinimum +
      1,
    OUROBOROS_DIMENSION,
  );

  for (const lane of TERNARY_MIDI_LAYOUT.lanes) {
    const notes = codebook
      .filter((entry) => entry.lane === lane.name)
      .map((entry) => entry.midiNote);
    assert.equal(notes.length, TERNARY_MIDI_LAYOUT.laneStride);
    assert.deepEqual(
      [Math.min(...notes), Math.max(...notes)],
      lane.midiNoteRange,
    );
  }

  for (const entry of codebook) {
    assert.equal(basisIndexFromMidiNote(entry.midiNote), entry.basisIndex);
    if (entry.qutritLabel !== null) {
      assert.equal(
        entry.midiNote,
        midiNoteForTernaryState(entry.orbitIndex, entry.qutritLabel),
      );
    }
  }
  for (let note = MIDI_NOTE_MINIMUM; note <= MIDI_NOTE_MAXIMUM; note += 1) {
    if (!occupiedNotes.has(note)) {
      assert.equal(basisIndexFromMidiNote(note), null);
    }
  }

  const byBasis = new Map(codebook.map((entry) => [entry.basisIndex, entry]));
  const permutation = trialityPermutation();
  for (const entry of codebook.filter((candidate) => candidate.qutritLabel !== null)) {
    const mapped = byBasis.get(permutation[entry.basisIndex]);
    const offset = entry.midiNote - TERNARY_MIDI_LAYOUT.firstQutritNote;
    const mappedOffset =
      mapped.midiNote - TERNARY_MIDI_LAYOUT.firstQutritNote;
    assert.equal(
      mappedOffset,
      (offset + TERNARY_MIDI_LAYOUT.trialityShift) %
        QUTRIT_SUBSPACE_DIMENSION,
    );
  }
});
