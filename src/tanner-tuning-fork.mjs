// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this file,
// You can obtain one at https://mozilla.org/MPL/2.0/.
// SPDX-License-Identifier: MPL-2.0
// Copyright (c) 2026 Trent Slade / QSOL-IMC.

/**
 * Dependency-free Tanner-graph spectral tuning primitives.
 *
 * The graph supplies dimensionless ratios. Absolute placement is conditional
 * on a declared nominal sample clock, calibration-frame count, playback band,
 * and bin-selection policy. It is not an E8-, QEC-, or Tanner-derived physical
 * frequency claim.
 */

export const TANNER_INSTRUMENT_SCHEMA = "qsol.tanner-instrument/v1";
export const TUNING_PROFILE_ID = "tanner-laplacian-frame-bin-v1";
export const CLOCK_BIN_POLICY_ID = "clock-bin-maximin-log-margin-v1";
export const NUMERIC_ABI = "ieee754-binary64-cyclic-jacobi-v1";

const DEFAULT_EIGENSOLVER = Object.freeze({
  absoluteTolerance: 1e-13,
  relativeTolerance: 1e-13,
  maxSweeps: 128,
});

const DEFAULT_GROUPING = Object.freeze({
  absoluteTolerance: 1e-10,
  relativeTolerance: 1e-10,
  orthonormalTolerance: 1e-8,
});

const DEFAULT_ZERO_CLASSIFICATION = Object.freeze({
  absoluteTolerance: 1e-12,
  relativeTolerance: 1e-10,
});

function requireSafeInteger(value, name, minimum = Number.MIN_SAFE_INTEGER) {
  if (!Number.isSafeInteger(value) || value < minimum) {
    throw new RangeError(`${name} must be a safe integer >= ${minimum}`);
  }
  return value;
}

function requireFinite(value, name) {
  if (!Number.isFinite(value)) {
    throw new TypeError(`${name} must be finite`);
  }
  return value;
}

function requireNonnegativeTolerance(value, name) {
  if (!Number.isFinite(value) || value < 0) {
    throw new RangeError(`${name} must be finite and nonnegative`);
  }
  return value;
}

function resolveTolerances(overrides, defaults, includeMaxSweeps = false) {
  const source = overrides ?? {};
  const result = {
    absoluteTolerance: requireNonnegativeTolerance(
      source.absoluteTolerance ?? defaults.absoluteTolerance,
      "absoluteTolerance",
    ),
    relativeTolerance: requireNonnegativeTolerance(
      source.relativeTolerance ?? defaults.relativeTolerance,
      "relativeTolerance",
    ),
  };
  if (includeMaxSweeps) {
    result.maxSweeps = requireSafeInteger(
      source.maxSweeps ?? defaults.maxSweeps,
      "maxSweeps",
      1,
    );
  }
  return result;
}

function resolveGrouping(overrides = {}) {
  return {
    ...resolveTolerances(overrides, DEFAULT_GROUPING),
    orthonormalTolerance: requireNonnegativeTolerance(
      overrides.orthonormalTolerance ?? DEFAULT_GROUPING.orthonormalTolerance,
      "orthonormalTolerance",
    ),
  };
}

function numericLexicographic(left, right) {
  const length = Math.min(left.length, right.length);
  for (let index = 0; index < length; index += 1) {
    if (left[index] !== right[index]) {
      return left[index] - right[index];
    }
  }
  return left.length - right.length;
}

function matrixShape(matrix, name, { allowEmpty = false } = {}) {
  if (!Array.isArray(matrix)) {
    throw new TypeError(`${name} must be a matrix`);
  }
  if (matrix.length === 0) {
    if (allowEmpty) {
      return { rows: 0, columns: 0 };
    }
    throw new RangeError(`${name} must be non-empty`);
  }
  if (!Array.isArray(matrix[0]) || matrix[0].length === 0) {
    throw new RangeError(`${name} must contain non-empty rows`);
  }
  const columns = matrix[0].length;
  for (let row = 0; row < matrix.length; row += 1) {
    if (!Array.isArray(matrix[row]) || matrix[row].length !== columns) {
      throw new RangeError(`${name} must be rectangular`);
    }
    for (let column = 0; column < columns; column += 1) {
      if (!Number.isFinite(matrix[row][column])) {
        throw new TypeError(`${name} entries must be finite numbers`);
      }
    }
  }
  return { rows: matrix.length, columns };
}

function assertSquareMatrix(matrix, name, options) {
  const shape = matrixShape(matrix, name, options);
  if (shape.rows !== shape.columns) {
    throw new RangeError(`${name} must be square`);
  }
  return shape.rows;
}

/** Validate and canonicalize a labelled sparse parity-check matrix. */
export function canonicalizeTanner(graph) {
  if (graph === null || typeof graph !== "object" || Array.isArray(graph)) {
    throw new TypeError("Tanner graph must be an object");
  }
  const field = requireSafeInteger(graph.field, "field", 2);
  if (field !== 2 && field !== 3) {
    throw new RangeError("field must be 2 or 3");
  }
  const checks = requireSafeInteger(graph.checks, "checks", 1);
  const variables = requireSafeInteger(graph.variables, "variables", 1);
  if (!Array.isArray(graph.entries)) {
    throw new TypeError("entries must be an array of sparse triples");
  }

  const seen = new Set();
  const entries = graph.entries.map((entry, index) => {
    if (!Array.isArray(entry) || entry.length !== 3) {
      throw new TypeError(`entries[${index}] must be [check, variable, coefficient]`);
    }
    const check = requireSafeInteger(entry[0], `entries[${index}].check`, 0);
    const variable = requireSafeInteger(entry[1], `entries[${index}].variable`, 0);
    const coefficient = requireSafeInteger(
      entry[2],
      `entries[${index}].coefficient`,
      1,
    );
    if (check >= checks || variable >= variables) {
      throw new RangeError(`entries[${index}] lies outside the declared matrix shape`);
    }
    if (coefficient >= field) {
      throw new RangeError(`entries[${index}].coefficient must be nonzero in GF(${field})`);
    }
    const key = `${check},${variable}`;
    if (seen.has(key)) {
      throw new RangeError(`duplicate Tanner entry at check ${check}, variable ${variable}`);
    }
    seen.add(key);
    return [check, variable, coefficient];
  });
  entries.sort(numericLexicographic);
  return { field, checks, variables, entries };
}

/** Convert a dense GF(2) or GF(3) parity-check matrix to sparse form. */
export function tannerFromDense(matrix, { field = 2 } = {}) {
  const shape = matrixShape(matrix, "dense Tanner matrix");
  requireSafeInteger(field, "field", 2);
  if (field !== 2 && field !== 3) {
    throw new RangeError("field must be 2 or 3");
  }
  const entries = [];
  for (let check = 0; check < shape.rows; check += 1) {
    for (let variable = 0; variable < shape.columns; variable += 1) {
      const coefficient = matrix[check][variable];
      if (!Number.isSafeInteger(coefficient) || coefficient < 0 || coefficient >= field) {
        throw new RangeError(`dense entry [${check},${variable}] is not in GF(${field})`);
      }
      if (coefficient !== 0) {
        entries.push([check, variable, coefficient]);
      }
    }
  }
  return canonicalizeTanner({
    field,
    checks: shape.rows,
    variables: shape.columns,
    entries,
  });
}

function canonicalTannerPayload(graph) {
  const canonical = canonicalizeTanner(graph);
  // Keys are deliberately emitted in recursive lexicographic order. Arrays
  // retain their canonical numeric ordering.
  return {
    checks: canonical.checks,
    entries: canonical.entries,
    field: canonical.field,
    schema: TANNER_INSTRUMENT_SCHEMA,
    variables: canonical.variables,
  };
}

/** Canonical UTF-8 identity text; compact, no BOM, no trailing newline. */
export function canonicalTannerJson(graph) {
  return JSON.stringify(canonicalTannerPayload(graph));
}

/** SHA-256 of the exact canonical Tanner identity bytes. */
export async function tannerSha256(graph) {
  const bytes = new TextEncoder().encode(canonicalTannerJson(graph));
  if (globalThis.crypto?.subtle) {
    const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
    return Array.from(new Uint8Array(digest), (byte) =>
      byte.toString(16).padStart(2, "0"),
    ).join("");
  }
  const { createHash } = await import("node:crypto");
  return createHash("sha256").update(bytes).digest("hex");
}

/** Unweighted bipartite support adjacency, variables before checks. */
export function buildTannerAdjacency(graph) {
  const canonical = canonicalizeTanner(graph);
  const dimension = canonical.variables + canonical.checks;
  const adjacency = Array.from({ length: dimension }, () => Array(dimension).fill(0));
  for (const [check, variable] of canonical.entries) {
    const checkNode = canonical.variables + check;
    adjacency[variable][checkNode] = 1;
    adjacency[checkNode][variable] = 1;
  }
  return adjacency;
}

export function buildTannerLaplacian(graph) {
  const adjacency = buildTannerAdjacency(graph);
  return adjacency.map((row, rowIndex) => {
    const degree = row.reduce((sum, value) => sum + value, 0);
    return row.map((value, columnIndex) =>
      rowIndex === columnIndex ? degree : -value,
    );
  });
}

export function canonicalDirectedEdges(graph) {
  const canonical = canonicalizeTanner(graph);
  const edges = [];
  for (const [check, variable] of canonical.entries) {
    const checkNode = canonical.variables + check;
    edges.push([variable, checkNode], [checkNode, variable]);
  }
  edges.sort(numericLexicographic);
  return edges;
}

/** Exact Hashimoto transition matrix B[j][i]. */
export function buildHashimoto(graph) {
  const directedEdges = canonicalDirectedEdges(graph);
  const matrix = Array.from(
    { length: directedEdges.length },
    () => Array(directedEdges.length).fill(0),
  );
  for (let source = 0; source < directedEdges.length; source += 1) {
    const [u, v] = directedEdges[source];
    for (let destination = 0; destination < directedEdges.length; destination += 1) {
      const [nextSource, w] = directedEdges[destination];
      if (v === nextSource && w !== u) {
        matrix[destination][source] = 1;
      }
    }
  }
  return { directedEdges, matrix };
}

export function identityMatrix(dimension) {
  requireSafeInteger(dimension, "dimension", 0);
  return Array.from({ length: dimension }, (_, row) =>
    Array.from({ length: dimension }, (_, column) => (row === column ? 1 : 0)),
  );
}

export function multiplyMatrices(left, right) {
  const leftShape = matrixShape(left, "left matrix", { allowEmpty: true });
  const rightShape = matrixShape(right, "right matrix", { allowEmpty: true });
  if (leftShape.rows === 0 && rightShape.rows === 0) {
    return [];
  }
  if (leftShape.columns !== rightShape.rows) {
    throw new RangeError(
      `incompatible matrix dimensions ${leftShape.rows}x${leftShape.columns} and ` +
        `${rightShape.rows}x${rightShape.columns}`,
    );
  }
  const output = Array.from(
    { length: leftShape.rows },
    () => Array(rightShape.columns).fill(0),
  );
  for (let row = 0; row < leftShape.rows; row += 1) {
    for (let shared = 0; shared < leftShape.columns; shared += 1) {
      const coefficient = left[row][shared];
      if (coefficient === 0) {
        continue;
      }
      for (let column = 0; column < rightShape.columns; column += 1) {
        output[row][column] += coefficient * right[shared][column];
      }
    }
  }
  return output;
}

export function matrixPower(matrix, exponent) {
  const dimension = assertSquareMatrix(matrix, "matrix", { allowEmpty: true });
  requireSafeInteger(exponent, "exponent", 0);
  let result = identityMatrix(dimension);
  let factor = matrix.map((row) => [...row]);
  let remaining = exponent;
  while (remaining > 0) {
    if (remaining % 2 === 1) {
      result = multiplyMatrices(result, factor);
    }
    remaining = Math.floor(remaining / 2);
    if (remaining > 0) {
      factor = multiplyMatrices(factor, factor);
    }
  }
  return result;
}

function assertSymmetric(matrix, tolerance = 1e-12) {
  for (let row = 0; row < matrix.length; row += 1) {
    for (let column = row + 1; column < matrix.length; column += 1) {
      const scale = Math.max(1, Math.abs(matrix[row][column]), Math.abs(matrix[column][row]));
      if (Math.abs(matrix[row][column] - matrix[column][row]) > tolerance * scale) {
        throw new RangeError("matrix must be symmetric");
      }
    }
  }
}

function maximumOffDiagonal(matrix) {
  let maximum = 0;
  for (let row = 0; row < matrix.length; row += 1) {
    for (let column = row + 1; column < matrix.length; column += 1) {
      maximum = Math.max(maximum, Math.abs(matrix[row][column]));
    }
  }
  return maximum;
}

function maximumDiagonalMagnitude(matrix) {
  let maximum = 0;
  for (let index = 0; index < matrix.length; index += 1) {
    maximum = Math.max(maximum, Math.abs(matrix[index][index]));
  }
  return maximum;
}

/** Deterministic cyclic Jacobi eigensolver for real symmetric matrices. */
export function jacobiEigenpairs(matrix, options = {}) {
  const dimension = assertSquareMatrix(matrix, "matrix");
  assertSymmetric(matrix);
  const resolved = resolveTolerances(options, DEFAULT_EIGENSOLVER, true);
  const diagonal = matrix.map((row) => [...row]);
  const vectors = identityMatrix(dimension);
  let sweeps = 0;
  let converged = dimension === 1;

  for (let sweep = 0; sweep < resolved.maxSweeps && !converged; sweep += 1) {
    const threshold =
      resolved.absoluteTolerance +
      resolved.relativeTolerance * Math.max(1, maximumDiagonalMagnitude(diagonal));
    if (maximumOffDiagonal(diagonal) <= threshold) {
      converged = true;
      break;
    }

    for (let p = 0; p < dimension - 1; p += 1) {
      for (let q = p + 1; q < dimension; q += 1) {
        const apq = diagonal[p][q];
        if (Math.abs(apq) <= threshold) {
          continue;
        }
        const app = diagonal[p][p];
        const aqq = diagonal[q][q];
        const tau = (aqq - app) / (2 * apq);
        const t =
          tau === 0
            ? 1
            : Math.sign(tau) / (Math.abs(tau) + Math.sqrt(1 + tau * tau));
        const cosine = 1 / Math.sqrt(1 + t * t);
        const sine = t * cosine;

        for (let index = 0; index < dimension; index += 1) {
          if (index === p || index === q) {
            continue;
          }
          const aip = diagonal[index][p];
          const aiq = diagonal[index][q];
          const rotatedP = cosine * aip - sine * aiq;
          const rotatedQ = sine * aip + cosine * aiq;
          diagonal[index][p] = rotatedP;
          diagonal[p][index] = rotatedP;
          diagonal[index][q] = rotatedQ;
          diagonal[q][index] = rotatedQ;
        }
        diagonal[p][p] = app - t * apq;
        diagonal[q][q] = aqq + t * apq;
        diagonal[p][q] = 0;
        diagonal[q][p] = 0;

        for (let row = 0; row < dimension; row += 1) {
          const vip = vectors[row][p];
          const viq = vectors[row][q];
          vectors[row][p] = cosine * vip - sine * viq;
          vectors[row][q] = sine * vip + cosine * viq;
        }
      }
    }
    sweeps = sweep + 1;
  }

  if (!converged) {
    const threshold =
      resolved.absoluteTolerance +
      resolved.relativeTolerance * Math.max(1, maximumDiagonalMagnitude(diagonal));
    converged = maximumOffDiagonal(diagonal) <= threshold;
  }
  if (!converged) {
    throw new Error(`cyclic Jacobi eigensolver did not converge in ${resolved.maxSweeps} sweeps`);
  }

  const order = Array.from({ length: dimension }, (_, index) => index).sort(
    (left, right) => diagonal[left][left] - diagonal[right][right] || left - right,
  );
  return {
    values: order.map((index) => diagonal[index][index]),
    vectors: vectors.map((row) => order.map((index) => row[index])),
    sweeps,
  };
}

function assertOrthonormalColumns(basis, tolerance) {
  const shape = matrixShape(basis, "basis");
  for (let left = 0; left < shape.columns; left += 1) {
    for (let right = left; right < shape.columns; right += 1) {
      let innerProduct = 0;
      for (let row = 0; row < shape.rows; row += 1) {
        innerProduct += basis[row][left] * basis[row][right];
      }
      const expected = left === right ? 1 : 0;
      if (Math.abs(innerProduct - expected) > tolerance) {
        throw new RangeError("basis columns must be orthonormal");
      }
    }
  }
  return shape;
}

export function projectorFromOrthonormalBasis(
  basis,
  { orthonormalTolerance = DEFAULT_GROUPING.orthonormalTolerance } = {},
) {
  const tolerance = requireNonnegativeTolerance(
    orthonormalTolerance,
    "orthonormalTolerance",
  );
  const shape = assertOrthonormalColumns(basis, tolerance);
  const projector = Array.from({ length: shape.rows }, () => Array(shape.rows).fill(0));
  for (let row = 0; row < shape.rows; row += 1) {
    for (let column = 0; column < shape.rows; column += 1) {
      let value = 0;
      for (let basisColumn = 0; basisColumn < shape.columns; basisColumn += 1) {
        value += basis[row][basisColumn] * basis[column][basisColumn];
      }
      projector[row][column] = value;
    }
  }
  return projector;
}

/** Group adjacent eigenvalues and construct basis-invariant projectors. */
export function clusterEigenpairs(values, vectors, options = {}) {
  if (!Array.isArray(values) || values.length === 0 || values.some((value) => !Number.isFinite(value))) {
    throw new TypeError("eigenvalues must be a non-empty finite array");
  }
  const grouping = resolveGrouping(options);
  const shape = assertOrthonormalColumns(vectors, grouping.orthonormalTolerance);
  if (shape.columns !== values.length) {
    throw new RangeError("eigenvector column count must equal eigenvalue count");
  }
  const suppliedIndices = options.sourceIndices ?? values.map((_, index) => index);
  if (!Array.isArray(suppliedIndices) || suppliedIndices.length !== values.length) {
    throw new RangeError("sourceIndices must match the eigenvalue count");
  }

  const order = values.map((value, index) => ({
    value,
    column: index,
    sourceIndex: suppliedIndices[index],
  })).sort((left, right) => left.value - right.value || left.column - right.column);

  const connectedGroups = [];
  for (const item of order) {
    const current = connectedGroups.at(-1);
    if (current === undefined) {
      connectedGroups.push([item]);
      continue;
    }
    const previous = current.at(-1).value;
    const tolerance =
      grouping.absoluteTolerance +
      grouping.relativeTolerance * Math.max(Math.abs(previous), Math.abs(item.value));
    if (Math.abs(item.value - previous) <= tolerance) {
      current.push(item);
    } else {
      connectedGroups.push([item]);
    }
  }

  return connectedGroups.map((items) => {
    const basis = vectors.map((row) => items.map((item) => row[item.column]));
    const eigenvalues = items.map((item) => item.value);
    return {
      eigenvalue: eigenvalues.reduce((sum, value) => sum + value, 0) / eigenvalues.length,
      eigenvalues,
      multiplicity: items.length,
      sourceIndices: items.map((item) => item.sourceIndex),
      basis,
      projector: projectorFromOrthonormalBasis(basis, grouping),
    };
  });
}

/** Classify Laplacian zero modes before positive-mode clustering. */
export function positiveLaplacianModes(values, options = {}) {
  if (!Array.isArray(values) || values.length === 0 || values.some((value) => !Number.isFinite(value))) {
    throw new TypeError("eigenvalues must be a non-empty finite array");
  }
  const resolved = resolveTolerances(options, DEFAULT_ZERO_CLASSIFICATION);
  const scale = Math.max(1, ...values.map((value) => Math.abs(value)));
  const zeroThreshold = resolved.absoluteTolerance + resolved.relativeTolerance * scale;
  const zeroIndices = [];
  const positiveIndices = [];
  const positiveValues = [];
  for (let index = 0; index < values.length; index += 1) {
    const value = values[index];
    if (value < -zeroThreshold) {
      throw new RangeError(`Laplacian has a materially negative eigenvalue ${value}`);
    }
    if (value <= zeroThreshold) {
      zeroIndices.push(index);
    } else {
      positiveIndices.push(index);
      positiveValues.push(value);
    }
  }
  return {
    zeroThreshold,
    zeroIndices,
    positiveIndices,
    positiveValues,
    rawRatios: positiveValues.map((value) => Math.sqrt(value)),
  };
}

function gcdBigInt(left, right) {
  let a = left < 0n ? -left : left;
  let b = right < 0n ? -right : right;
  while (b !== 0n) {
    [a, b] = [b, a % b];
  }
  return a;
}

/** Choose a deterministic nominal audio-frame-bin anchor. */
export function chooseClockBinCalibration({
  sampleRateHz,
  calibrationFrameCount,
  playbackBandHz,
  ratios,
  nyquistGuard = 0.95,
}) {
  requireSafeInteger(sampleRateHz, "sampleRateHz", 1);
  requireSafeInteger(calibrationFrameCount, "calibrationFrameCount", 1);
  if (!Array.isArray(playbackBandHz) || playbackBandHz.length !== 2) {
    throw new TypeError("playbackBandHz must be [minimum, maximum]");
  }
  const minimumHz = requireFinite(playbackBandHz[0], "playbackBandHz[0]");
  const maximumHz = requireFinite(playbackBandHz[1], "playbackBandHz[1]");
  if (minimumHz <= 0 || maximumHz <= minimumHz) {
    throw new RangeError("playbackBandHz must be positive and increasing");
  }
  if (!Number.isFinite(nyquistGuard) || nyquistGuard <= 0 || nyquistGuard > 1) {
    throw new RangeError("nyquistGuard must lie in (0, 1]");
  }
  const guardedNyquistHz = (sampleRateHz / 2) * nyquistGuard;
  if (maximumHz > guardedNyquistHz) {
    throw new RangeError("playback band exceeds the guarded Nyquist frequency");
  }
  if (!Array.isArray(ratios) || ratios.length === 0) {
    throw new TypeError("ratios must be a non-empty array");
  }
  const copiedRatios = ratios.map((ratio, index) => {
    if (!Number.isFinite(ratio) || ratio <= 0) {
      throw new RangeError(`ratios[${index}] must be finite and positive`);
    }
    return ratio;
  });
  const minimumRatio = Math.min(...copiedRatios);
  const maximumRatio = Math.max(...copiedRatios);
  const binWidthHz = sampleRateHz / calibrationFrameCount;
  const minimumBin = Math.max(
    1,
    Math.ceil(minimumHz / (binWidthHz * minimumRatio)),
  );
  const maximumBandBin = Math.floor(maximumHz / (binWidthHz * maximumRatio));
  const maximumAnchorBin = Math.floor((nyquistGuard * calibrationFrameCount) / 2);
  const maximumBin = Math.min(maximumBandBin, maximumAnchorBin);
  if (minimumBin > maximumBin) {
    throw new RangeError("no frame bin places the complete mode spectrum in the playback band");
  }

  const continuousTarget =
    Math.sqrt((minimumHz * maximumHz) / (minimumRatio * maximumRatio)) /
    binWidthHz;
  const candidates = new Set([
    minimumBin,
    maximumBin,
    Math.max(minimumBin, Math.min(maximumBin, Math.floor(continuousTarget))),
    Math.max(minimumBin, Math.min(maximumBin, Math.ceil(continuousTarget))),
  ]);
  let selectedBin;
  let selectedScore = -Infinity;
  for (const bin of [...candidates].sort((left, right) => left - right)) {
    const anchorHz = bin * binWidthHz;
    const lowerMargin = (anchorHz * minimumRatio) / minimumHz;
    const upperMargin = maximumHz / (anchorHz * maximumRatio);
    const score = Math.min(lowerMargin, upperMargin);
    if (score > selectedScore) {
      selectedBin = bin;
      selectedScore = score;
    }
  }

  const numeratorUnreduced = BigInt(selectedBin) * BigInt(sampleRateHz);
  const denominatorUnreduced = BigInt(calibrationFrameCount);
  const divisor = gcdBigInt(numeratorUnreduced, denominatorUnreduced);
  const numerator = numeratorUnreduced / divisor;
  const denominator = denominatorUnreduced / divisor;
  const anchorHz = selectedBin * binWidthHz;
  return {
    policyId: CLOCK_BIN_POLICY_ID,
    nominalClockOnly: true,
    sampleRateHz,
    calibrationFrameCount,
    playbackBandHz: [minimumHz, maximumHz],
    nyquistGuard,
    guardedNyquistHz,
    binWidthHz,
    feasibleBinRange: [minimumBin, maximumBin],
    continuousTargetBin: continuousTarget,
    binIndex: selectedBin,
    anchorRationalHz: {
      numerator: numerator.toString(),
      denominator: denominator.toString(),
    },
    anchorHz,
    ratios: copiedRatios,
    frequenciesHz: copiedRatios.map((ratio) => ratio * anchorHz),
  };
}

/** Full Laplacian-to-ratio-to-clock-bin derivation with numerical receipt. */
export function deriveLaplacianClockTuning({
  laplacian,
  sampleRateHz,
  calibrationFrameCount,
  playbackBandHz,
  nyquistGuard = 0.95,
  eigensolver = {},
  grouping = {},
  zeroModeClassification = {},
}) {
  const resolvedEigensolver = resolveTolerances(
    eigensolver,
    DEFAULT_EIGENSOLVER,
    true,
  );
  const resolvedGrouping = resolveGrouping(grouping);
  const resolvedZeroMode = resolveTolerances(
    zeroModeClassification,
    DEFAULT_ZERO_CLASSIFICATION,
  );
  const eigenpairs = jacobiEigenpairs(laplacian, resolvedEigensolver);
  const modes = positiveLaplacianModes(eigenpairs.values, resolvedZeroMode);
  if (modes.positiveValues.length === 0) {
    throw new RangeError("Laplacian has no positive modes to tune");
  }
  const positiveVectors = eigenpairs.vectors.map((row) =>
    modes.positiveIndices.map((index) => row[index]),
  );
  const positiveEigenspaceGroups = clusterEigenpairs(
    modes.positiveValues,
    positiveVectors,
    { ...resolvedGrouping, sourceIndices: modes.positiveIndices },
  );
  const invariantPositiveEigenspaces = positiveEigenspaceGroups.map((group) => ({
    eigenvalue: group.eigenvalue,
    eigenvalues: [...group.eigenvalues],
    ratio: Math.sqrt(group.eigenvalue),
    multiplicity: group.multiplicity,
    projector: group.projector.map((row) => [...row]),
  }));
  const calibration = chooseClockBinCalibration({
    sampleRateHz,
    calibrationFrameCount,
    playbackBandHz,
    ratios: modes.rawRatios,
    nyquistGuard,
  });
  return {
    profileId: TUNING_PROFILE_ID,
    eigenpairs,
    modes,
    // Retained as a compatibility alias for the supplied v1 test contract.
    eigenspaceGroups: positiveEigenspaceGroups,
    positiveEigenspaceGroups,
    invariantPositiveEigenspaces,
    calibration,
    numerics: {
      abi: NUMERIC_ABI,
      eigensolver: resolvedEigensolver,
      eigenspaceGrouping: resolvedGrouping,
      zeroModeClassification: resolvedZeroMode,
    },
  };
}
