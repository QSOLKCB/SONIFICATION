// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this file,
// You can obtain one at https://mozilla.org/MPL/2.0/.
// SPDX-License-Identifier: MPL-2.0
// Copyright (c) 2026 Trent Slade / QSOL-IMC.

import assert from "node:assert/strict";
import test from "node:test";

import { deriveEtq101ClockTuning } from "../src/etq101-tuning-fork.mjs";

import {
  buildHashimoto,
  buildTannerAdjacency,
  buildTannerLaplacian,
  canonicalDirectedEdges,
  canonicalTannerJson,
  canonicalizeTanner,
  chooseClockBinCalibration,
  clusterEigenpairs,
  deriveLaplacianClockTuning,
  identityMatrix,
  jacobiEigenpairs,
  matrixPower,
  multiplyMatrices,
  positiveLaplacianModes,
  projectorFromOrthonormalBasis,
  tannerFromDense,
  tannerSha256,
} from "../src/tanner-tuning-fork.mjs";

const P5 = [
  [1, 1, 0],
  [0, 1, 1],
];

const C6 = [
  [1, 1, 0],
  [0, 1, 1],
  [1, 0, 1],
];

const C8 = [
  [1, 1, 0, 0],
  [0, 1, 1, 0],
  [0, 0, 1, 1],
  [1, 0, 0, 1],
];

function assertClose(actual, expected, tolerance = 1e-10) {
  assert.ok(
    Math.abs(actual - expected) <= tolerance,
    `expected ${actual} to be within ${tolerance} of ${expected}`,
  );
}

function assertMatrixClose(actual, expected, tolerance = 1e-12) {
  assert.equal(actual.length, expected.length);
  for (let row = 0; row < actual.length; row += 1) {
    assert.equal(actual[row].length, expected[row].length);
    for (let column = 0; column < actual[row].length; column += 1) {
      assertClose(actual[row][column], expected[row][column], tolerance);
    }
  }
}

function zeroMatrix(size) {
  return Array.from({ length: size }, () => Array(size).fill(0));
}

test("P5 Laplacian derives phi modes and a reproducible clock-bin anchor", () => {
  const phi = (1 + Math.sqrt(5)) / 2;
  const graph = tannerFromDense(P5);
  const { values } = jacobiEigenpairs(buildTannerLaplacian(graph));
  const expected = [
    0,
    (3 - Math.sqrt(5)) / 2,
    (5 - Math.sqrt(5)) / 2,
    (3 + Math.sqrt(5)) / 2,
    (5 + Math.sqrt(5)) / 2,
  ];
  values.forEach((value, index) => assertClose(value, expected[index]));

  const modes = positiveLaplacianModes(values);
  assertClose(modes.rawRatios[0], 1 / phi);
  assertClose(modes.rawRatios[2], phi);
  assertClose(modes.rawRatios[2] / modes.rawRatios[0], phi * phi);

  const calibration = chooseClockBinCalibration({
    sampleRateHz: 48_000,
    calibrationFrameCount: 960_000,
    playbackBandHz: [40, 16_000],
    ratios: modes.rawRatios,
  });
  assert.equal(calibration.binIndex, 14_757);
  assert.deepEqual(calibration.anchorRationalHz, {
    numerator: "14757",
    denominator: "20",
  });
  assert.equal(calibration.anchorHz, 737.85);
  assert.ok(calibration.frequenciesHz.every((frequency) => frequency >= 40));
  assert.ok(calibration.frequenciesHz.every((frequency) => frequency <= 16_000));

  const exactTie = chooseClockBinCalibration({
    sampleRateHz: 100,
    calibrationFrameCount: 100,
    playbackBandHz: [1, 6],
    ratios: [1],
  });
  assert.equal(exactTie.binIndex, 2, "an exact maximin tie uses the smaller bin");

  const inputOrder = chooseClockBinCalibration({
    sampleRateHz: 100,
    calibrationFrameCount: 100,
    playbackBandHz: [1, 20],
    ratios: [2, 1],
  });
  assert.deepEqual(inputOrder.ratios, [2, 1]);
  assert.deepEqual(inputOrder.frequenciesHz, [2, 1].map((ratio) => ratio * inputOrder.anchorHz));

  assert.throws(
    () =>
      chooseClockBinCalibration({
        sampleRateHz: 48_000,
        calibrationFrameCount: 48_000,
        playbackBandHz: [100, 101],
        ratios: [1, 2],
      }),
    /no frame bin places the complete mode spectrum/,
  );
});

test("C6 two-step Hashimoto clock has exact order three for qutrit phases", () => {
  const { matrix: hashimoto } = buildHashimoto(tannerFromDense(C6));
  const twoStep = multiplyMatrices(hashimoto, hashimoto);
  assert.deepEqual(matrixPower(twoStep, 3), identityMatrix(twoStep.length));
  assert.notDeepEqual(twoStep, identityMatrix(twoStep.length));
});

test("C8 two-step Hashimoto clock has exact order four for quadrature", () => {
  const { matrix: hashimoto } = buildHashimoto(tannerFromDense(C8));
  const twoStep = multiplyMatrices(hashimoto, hashimoto);
  assert.deepEqual(matrixPower(twoStep, 4), identityMatrix(twoStep.length));
  assert.notDeepEqual(matrixPower(twoStep, 2), identityMatrix(twoStep.length));
});

test("P5 tree Hashimoto operator is nilpotent rather than resonant", () => {
  const { matrix: hashimoto } = buildHashimoto(tannerFromDense(P5));
  assert.deepEqual(matrixPower(hashimoto, 4), zeroMatrix(hashimoto.length));
  assert.notDeepEqual(matrixPower(hashimoto, 3), zeroMatrix(hashimoto.length));
});

test("labelled Tanner edges canonicalize numerically under shuffled input", () => {
  const graph = canonicalizeTanner({
    field: 3,
    checks: 11,
    variables: 11,
    entries: [
      [10, 2, 1],
      [2, 10, 2],
      [0, 1, 2],
      [0, 2, 1],
    ],
  });
  assert.deepEqual(graph.entries, [
    [0, 1, 2],
    [0, 2, 1],
    [2, 10, 2],
    [10, 2, 1],
  ]);
  assert.deepEqual(canonicalDirectedEdges(graph), [
    [1, 11],
    [2, 11],
    [2, 21],
    [10, 13],
    [11, 1],
    [11, 2],
    [13, 10],
    [21, 2],
  ]);

  const reshuffled = canonicalizeTanner({
    field: 3,
    checks: 11,
    variables: 11,
    entries: [...graph.entries].reverse(),
  });
  assert.equal(canonicalTannerJson(graph), canonicalTannerJson(reshuffled));
});

test("a proper degenerate subspace projector is invariant under basis rotation", () => {
  const angle = Math.PI / 4;
  const standard = [
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 1],
  ];
  const rotated = [
    [Math.cos(angle), -Math.sin(angle), 0],
    [Math.sin(angle), Math.cos(angle), 0],
    [0, 0, 1],
  ];
  const eigenvalues = [2, 2 + 1e-12, 5];
  const standardGroups = clusterEigenpairs(eigenvalues, standard);
  const rotatedGroups = clusterEigenpairs(eigenvalues, rotated);
  assert.deepEqual(standardGroups.map((group) => group.multiplicity), [2, 1]);

  const expected = [
    [1, 0, 0],
    [0, 1, 0],
    [0, 0, 0],
  ];
  const standardProjector = standardGroups[0].projector;
  const rotatedProjector = rotatedGroups[0].projector;
  assertMatrixClose(standardProjector, expected);
  assertMatrixClose(rotatedProjector, expected);
  assertMatrixClose(standardProjector, rotatedProjector);
  assertMatrixClose(
    multiplyMatrices(standardProjector, standardProjector),
    standardProjector,
  );
  assertClose(
    standardProjector.reduce((trace, row, index) => trace + row[index], 0),
    2,
  );

  // The standalone helper remains the primitive used by the grouping path.
  assertMatrixClose(
    projectorFromOrthonormalBasis(standard.map((row) => row.slice(0, 2))),
    expected,
  );
  assert.throws(
    () =>
      clusterEigenpairs(
        [1, 2],
        [
          [1, 1],
          [0, 0],
        ],
      ),
    /basis columns must be orthonormal/,
  );
  assert.throws(
    () => positiveLaplacianModes([0, 1], { absoluteTolerance: -1 }),
    /absoluteTolerance must be finite and nonnegative/,
  );

  const zeroSeparatedBeforeGrouping = deriveLaplacianClockTuning({
    laplacian: [
      [0, 0],
      [0, 0.5],
    ],
    sampleRateHz: 100,
    calibrationFrameCount: 100,
    playbackBandHz: [0.1, 10],
    grouping: { absoluteTolerance: 1, relativeTolerance: 1e-12 },
  });
  assert.equal(zeroSeparatedBeforeGrouping.eigenspaceGroups.length, 1);
  assert.equal(zeroSeparatedBeforeGrouping.positiveEigenspaceGroups.length, 1);
  assert.deepEqual(
    zeroSeparatedBeforeGrouping.positiveEigenspaceGroups[0].sourceIndices,
    [1],
  );
  assert.deepEqual(zeroSeparatedBeforeGrouping.numerics.eigenspaceGrouping, {
    absoluteTolerance: 1,
    relativeTolerance: 1e-12,
    orthonormalTolerance: 1e-8,
  });
});

test("GF(3) coefficient labels change instrument hash without changing topology", async () => {
  const coefficientOne = tannerFromDense([[1]], { field: 3 });
  const coefficientTwo = tannerFromDense([[2]], { field: 3 });
  assert.deepEqual(buildTannerAdjacency(coefficientOne), buildTannerAdjacency(coefficientTwo));
  assert.notEqual(canonicalTannerJson(coefficientOne), canonicalTannerJson(coefficientTwo));
  assert.equal(
    canonicalTannerJson(coefficientOne),
    '{"checks":1,"entries":[[0,0,1]],"field":3,"schema":"qsol.tanner-instrument/v1","variables":1}',
  );

  const hashOne = await tannerSha256(coefficientOne);
  const hashTwo = await tannerSha256(coefficientTwo);
  assert.equal(hashOne, "a55bab3b24e9542fe35a243cec4b9365a15b224b01e8410fa1bf9d22f9b047dc");
  assert.equal(hashTwo, "d412c38c659c5c2aea9cd318be3d376f996903509e93dbfb20bfb6ffa230fd52");
  assert.notEqual(hashOne, hashTwo);
});

test("ETQ-101 E8 root graph derives a calibrated spectrum without a 432 anchor", () => {
  const tuning = deriveEtq101ClockTuning({
    sampleRateHz: 48_000,
    calibrationFrameCount: 960_000,
    playbackBandHz: [40, 16_000],
  });
  assert.equal(tuning.profile.profileId, "etq101-e8-root-laplacian-frame-bin-v1");
  assert.equal(tuning.graph.vertices, 101);
  assert.equal(tuning.graph.connected, true);
  assert.equal(tuning.eigenpairs.values.length, 101);
  assert.equal(tuning.modes.rawRatios.length, 100);
  assert.equal(
    tuning.invariantPositiveEigenspaces.length,
    tuning.positiveEigenspaceGroups.length,
  );
  assert.ok(
    tuning.invariantPositiveEigenspaces.every(
      (group) => group.basis === undefined && group.sourceIndices === undefined,
    ),
  );
  assert.deepEqual(tuning.numerics, {
    abi: "ieee754-binary64-cyclic-jacobi-v1",
    eigensolver: {
      absoluteTolerance: 1e-13,
      relativeTolerance: 1e-13,
      maxSweeps: 128,
    },
    eigenspaceGrouping: {
      absoluteTolerance: 1e-10,
      relativeTolerance: 1e-10,
      orthonormalTolerance: 1e-8,
    },
    zeroModeClassification: {
      absoluteTolerance: 1e-12,
      relativeTolerance: 1e-10,
    },
  });
  assert.equal(tuning.calibration.binIndex, 3_028);
  assert.deepEqual(tuning.calibration.anchorRationalHz, {
    numerator: "757",
    denominator: "5",
  });
  assert.notEqual(tuning.calibration.anchorHz, 432);
  assert.ok(
    tuning.calibration.frequenciesHz.every(
      (frequency) => frequency >= 40 && frequency <= 16_000,
    ),
  );
});
