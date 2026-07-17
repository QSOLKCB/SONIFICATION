// SPDX-License-Identifier: LicenseRef-QSOL-IMC-Core-Proprietary-1.0
// Copyright (c) 2026 Trent Slade. All Rights Reserved.

/**
 * ETQ-101 reference construction.
 *
 * The implementation uses doubled integer E8-root coordinates. If r is a
 * conventional root, this module stores 2r, so every norm squared is exactly
 * eight and the adjacency condition r_a . r_b = 1 is the integer test
 * (2r_a) . (2r_b) = 4.
 *
 * No external packages are required. The module is deterministic and is safe
 * to import in either a modern browser or Node.js.
 */

export const MODEL_ID = "ETQ-101";
export const MODEL_VERSION = "1.0.0";
export const OUROBOROS_DIMENSION = 101;
export const QUTRIT_DIMENSION = 3;
export const SELECTED_FIXED_ROOTS = 2;
export const SELECTED_TRIALITY_ORBITS = 33;
export const REFERENCE_FREQUENCY_HZ = 432;
export const REFERENCE_ANGULAR_FREQUENCY_RAD_S =
  2 * Math.PI * REFERENCE_FREQUENCY_HZ;
export const PHASE_THETA_RAD = Math.PI / 2;
export const GOLDEN_RATIO = (1 + Math.sqrt(5)) / 2;
export const QUTRIT_ROOT_OF_UNITY = Object.freeze({
  re: -0.5,
  im: Math.sqrt(3) / 2,
});
export const SCL_STENCIL = Object.freeze([1, -2, 1]);

// Twice the D4 triality matrix. Applying this matrix and dividing by two is
// exact on the doubled-coordinate E8 roots used by this module.
export const D4_TRIALITY_NUMERATOR = Object.freeze([
  Object.freeze([1, 1, 1, 1]),
  Object.freeze([1, 1, -1, -1]),
  Object.freeze([1, -1, 1, -1]),
  Object.freeze([-1, 1, 1, -1]),
]);

export function lexicographicCompare(left, right) {
  const length = Math.min(left.length, right.length);
  for (let index = 0; index < length; index += 1) {
    if (left[index] !== right[index]) {
      return left[index] - right[index];
    }
  }
  return left.length - right.length;
}

export function vectorKey(vector) {
  return vector.join(",");
}

export function dot(left, right) {
  let total = 0;
  for (let index = 0; index < left.length; index += 1) {
    total += left[index] * right[index];
  }
  return total;
}

function populationCount(integer) {
  let value = integer;
  let count = 0;
  while (value !== 0) {
    count += value & 1;
    value >>>= 1;
  }
  return count;
}

/** Generate the standard 240 E8 roots in doubled integer coordinates. */
export function generateE8Roots() {
  const roots = [];

  // 112 roots of the form (+/-2, +/-2, 0, ..., 0), representing
  // conventional roots (+/-1, +/-1, 0, ..., 0).
  for (let first = 0; first < 8; first += 1) {
    for (let second = first + 1; second < 8; second += 1) {
      for (const firstSign of [-2, 2]) {
        for (const secondSign of [-2, 2]) {
          const root = Array(8).fill(0);
          root[first] = firstSign;
          root[second] = secondSign;
          roots.push(root);
        }
      }
    }
  }

  // 128 roots (+/-1, ..., +/-1), representing half-integer roots, with an
  // even number of negative entries.
  for (let mask = 0; mask < 256; mask += 1) {
    if (populationCount(mask) % 2 !== 0) {
      continue;
    }
    const root = [];
    for (let coordinate = 0; coordinate < 8; coordinate += 1) {
      root.push((mask & (1 << coordinate)) === 0 ? 1 : -1);
    }
    roots.push(root);
  }

  roots.sort(lexicographicCompare);
  return roots;
}

function applyTrialityBlock(block) {
  return D4_TRIALITY_NUMERATOR.map((row) => {
    const numerator = dot(row, block);
    if (numerator % 2 !== 0) {
      throw new Error("Triality left the doubled-coordinate E8 lattice");
    }
    return numerator / 2;
  });
}

/** Apply the embedded D4 x D4 order-three triality to an E8 root. */
export function applyTriality(root) {
  if (!Array.isArray(root) || root.length !== 8) {
    throw new TypeError("An E8 root must contain exactly eight coordinates");
  }
  return [
    ...applyTrialityBlock(root.slice(0, 4)),
    ...applyTrialityBlock(root.slice(4, 8)),
  ];
}

export function trialityOrbit(root) {
  const first = [...root];
  const second = applyTriality(first);
  const third = applyTriality(second);
  const closure = applyTriality(third);
  if (vectorKey(closure) !== vectorKey(first)) {
    throw new Error("Embedded triality did not close after three applications");
  }
  return vectorKey(first) === vectorKey(second)
    ? [first]
    : [first, second, third];
}

/**
 * Partition the 240 roots into the 12 fixed roots and 76 three-cycles of the
 * embedded triality. Three-cycle representatives are lexicographically least.
 */
export function classifyTrialityOrbits(roots = generateE8Roots()) {
  const rootKeys = new Set(roots.map(vectorKey));
  const seen = new Set();
  const fixed = [];
  const triples = [];

  for (const root of [...roots].sort(lexicographicCompare)) {
    if (seen.has(vectorKey(root))) {
      continue;
    }
    const rawOrbit = trialityOrbit(root);
    for (const member of rawOrbit) {
      const key = vectorKey(member);
      if (!rootKeys.has(key)) {
        throw new Error("Embedded triality did not preserve the E8 root set");
      }
      seen.add(key);
    }

    if (rawOrbit.length === 1) {
      fixed.push(rawOrbit[0]);
      continue;
    }

    const representative = [...rawOrbit].sort(lexicographicCompare)[0];
    triples.push([
      representative,
      applyTriality(representative),
      applyTriality(applyTriality(representative)),
    ]);
  }

  fixed.sort(lexicographicCompare);
  triples.sort((left, right) => lexicographicCompare(left[0], right[0]));
  return { fixed, triples };
}

/**
 * Canonical ETQ-101 ordered root labels: two fixed roots followed by 33
 * complete triality orbits, each ordered (r, tau r, tau^2 r). The returned
 * roots label an orthonormal basis of ell^2(S_101); they are not a vector
 * basis of R^8.
 */
export function selectEtq101Basis(roots = generateE8Roots()) {
  const { fixed, triples } = classifyTrialityOrbits(roots);
  if (fixed.length !== 12 || triples.length !== 76) {
    throw new Error(
      `Unexpected triality decomposition ${fixed.length} + 3*${triples.length}`,
    );
  }

  const basis = fixed.slice(0, SELECTED_FIXED_ROOTS).map((root) => [...root]);
  for (const orbit of triples.slice(0, SELECTED_TRIALITY_ORBITS)) {
    for (const root of orbit) {
      basis.push([...root]);
    }
  }

  if (basis.length !== OUROBOROS_DIMENSION) {
    throw new Error(`Canonical selector produced ${basis.length} basis states`);
  }
  return basis;
}

/** Return p such that U_tau |j> = |p[j]>. */
export function trialityPermutation() {
  const permutation = Array.from(
    { length: OUROBOROS_DIMENSION },
    (_, index) => index,
  );
  for (let orbit = 0; orbit < SELECTED_TRIALITY_ORBITS; orbit += 1) {
    const offset = SELECTED_FIXED_ROOTS + QUTRIT_DIMENSION * orbit;
    permutation[offset] = offset + 1;
    permutation[offset + 1] = offset + 2;
    permutation[offset + 2] = offset;
  }
  return permutation;
}

export function applyPermutationIndex(permutation, index, power = 1) {
  const normalizedPower = ((power % 3) + 3) % 3;
  let result = index;
  for (let step = 0; step < normalizedPower; step += 1) {
    result = permutation[result];
  }
  return result;
}

/** E8 root-polytope adjacency restricted to the canonical 101 roots. */
export function buildRootAdjacency(basis = selectEtq101Basis()) {
  const adjacency = Array.from(
    { length: basis.length },
    () => Array(basis.length).fill(0),
  );
  for (let left = 0; left < basis.length; left += 1) {
    for (let right = left + 1; right < basis.length; right += 1) {
      if (dot(basis[left], basis[right]) === 4) {
        adjacency[left][right] = 1;
        adjacency[right][left] = 1;
      }
    }
  }
  return adjacency;
}

export function buildGraphLaplacian(adjacency) {
  const dimension = adjacency.length;
  return adjacency.map((row, rowIndex) => {
    const degree = row.reduce((sum, value) => sum + value, 0);
    return row.map((value, columnIndex) =>
      rowIndex === columnIndex ? degree : -value,
    );
  });
}

export function graphSummary(adjacency) {
  const degrees = adjacency.map((row) =>
    row.reduce((sum, value) => sum + value, 0),
  );
  const edgeCount = degrees.reduce((sum, degree) => sum + degree, 0) / 2;

  const visited = new Set([0]);
  const queue = [0];
  while (queue.length > 0) {
    const current = queue.shift();
    for (let neighbour = 0; neighbour < adjacency.length; neighbour += 1) {
      if (adjacency[current][neighbour] === 1 && !visited.has(neighbour)) {
        visited.add(neighbour);
        queue.push(neighbour);
      }
    }
  }

  return {
    vertices: adjacency.length,
    edges: edgeCount,
    minimumDegree: Math.min(...degrees),
    maximumDegree: Math.max(...degrees),
    connected: visited.size === adjacency.length,
  };
}

/** diag(0,0, 1,-2,1, ..., 1,-2,1). */
export function curvatureDiagonal() {
  const diagonal = [0, 0];
  for (let orbit = 0; orbit < SELECTED_TRIALITY_ORBITS; orbit += 1) {
    diagonal.push(...SCL_STENCIL);
  }
  return diagonal;
}

/** diag(0,0, 0,1,2, ..., 0,1,2). */
export function qutritNumberDiagonal() {
  const diagonal = [0, 0];
  for (let orbit = 0; orbit < SELECTED_TRIALITY_ORBITS; orbit += 1) {
    diagonal.push(0, 1, 2);
  }
  return diagonal;
}

/** diag(0,0, -1,0,1, ..., -1,0,1). */
export function centeredQutritNumberDiagonal() {
  const diagonal = [0, 0];
  for (let orbit = 0; orbit < SELECTED_TRIALITY_ORBITS; orbit += 1) {
    diagonal.push(-1, 0, 1);
  }
  return diagonal;
}

/** Diagonal of U_tau^power D U_tau^-power. */
export function permuteDiagonal(
  diagonal,
  permutation = trialityPermutation(),
  power = 1,
) {
  const result = Array(diagonal.length).fill(0);
  for (let index = 0; index < diagonal.length; index += 1) {
    result[applyPermutationIndex(permutation, index, power)] = diagonal[index];
  }
  return result;
}

export function phaseKickDiagonal(theta = PHASE_THETA_RAD) {
  return curvatureDiagonal().map((value) => {
    const phase = -theta * value;
    return { re: Math.cos(phase), im: Math.sin(phase) };
  });
}

/**
 * Pure, normalized ETQ-101 golden-phase Ouroboros state. "Ouroboros" is a
 * declared model name, not a standard state class.
 */
export function ouroborosState({
  theta = PHASE_THETA_RAD,
  goldenRatio = GOLDEN_RATIO,
} = {}) {
  const curvature = curvatureDiagonal();
  const normalization = 1 / Math.sqrt(OUROBOROS_DIMENSION);
  return curvature.map((value, index) => {
    const phase = (2 * Math.PI * index) / goldenRatio - theta * value;
    return {
      re: normalization * Math.cos(phase),
      im: normalization * Math.sin(phase),
    };
  });
}

export function complex(re = 0, im = 0) {
  return { re, im };
}

export function complexAdd(left, right) {
  return complex(left.re + right.re, left.im + right.im);
}

export function complexMultiply(left, right) {
  return complex(
    left.re * right.re - left.im * right.im,
    left.re * right.im + left.im * right.re,
  );
}

export function complexScale(value, scalar) {
  return complex(value.re * scalar, value.im * scalar);
}

export function complexMatrixMultiply(left, right) {
  const rows = left.length;
  const columns = right[0].length;
  const shared = right.length;
  const output = Array.from({ length: rows }, () =>
    Array.from({ length: columns }, () => complex()),
  );
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      let value = complex();
      for (let index = 0; index < shared; index += 1) {
        value = complexAdd(
          value,
          complexMultiply(left[row][index], right[index][column]),
        );
      }
      output[row][column] = value;
    }
  }
  return output;
}

export function complexIdentity(dimension) {
  return Array.from({ length: dimension }, (_, row) =>
    Array.from({ length: dimension }, (_, column) =>
      complex(row === column ? 1 : 0, 0),
    ),
  );
}

export function complexMatrixPower(matrix, exponent) {
  let result = complexIdentity(matrix.length);
  let factor = matrix;
  let remaining = exponent;
  while (remaining > 0) {
    if (remaining % 2 === 1) {
      result = complexMatrixMultiply(result, factor);
    }
    remaining = Math.floor(remaining / 2);
    if (remaining > 0) {
      factor = complexMatrixMultiply(factor, factor);
    }
  }
  return result;
}

export function qutritOperators() {
  const zero = () => complex(0, 0);
  const X = Array.from({ length: 3 }, () => Array.from({ length: 3 }, zero));
  const Z = Array.from({ length: 3 }, () => Array.from({ length: 3 }, zero));

  for (let source = 0; source < 3; source += 1) {
    X[(source + 1) % 3][source] = complex(1, 0);
    const phase = (2 * Math.PI * source) / 3;
    Z[source][source] = complex(Math.cos(phase), Math.sin(phase));
  }

  const N = [
    [complex(0), complex(0), complex(0)],
    [complex(0), complex(1), complex(0)],
    [complex(0), complex(0), complex(2)],
  ];
  const D = [
    [complex(1), complex(0), complex(0)],
    [complex(0), complex(-2), complex(0)],
    [complex(0), complex(0), complex(1)],
  ];
  return { X, Z, N, D };
}

/** Local F_3 = X exp(-i theta D), which has exact order three. */
export function twistedQutritStep(theta = PHASE_THETA_RAD) {
  const { X } = qutritOperators();
  const localCurvature = [1, -2, 1];
  const phase = Array.from({ length: 3 }, (_, row) =>
    Array.from({ length: 3 }, (_, column) => {
      if (row !== column) {
        return complex();
      }
      const angle = -theta * localCurvature[row];
      return complex(Math.cos(angle), Math.sin(angle));
    }),
  );
  return complexMatrixMultiply(X, phase);
}

export function maxComplexMatrixDifference(left, right) {
  let maximum = 0;
  for (let row = 0; row < left.length; row += 1) {
    for (let column = 0; column < left[row].length; column += 1) {
      maximum = Math.max(
        maximum,
        Math.hypot(
          left[row][column].re - right[row][column].re,
          left[row][column].im - right[row][column].im,
        ),
      );
    }
  }
  return maximum;
}

export function canonicalModelSummary() {
  const roots = generateE8Roots();
  const { fixed, triples } = classifyTrialityOrbits(roots);
  const basis = selectEtq101Basis(roots);
  const adjacency = buildRootAdjacency(basis);
  return {
    modelId: MODEL_ID,
    modelVersion: MODEL_VERSION,
    dimensions: {
      total: OUROBOROS_DIMENSION,
      fixedSinglets: SELECTED_FIXED_ROOTS,
      qutritOrbits: SELECTED_TRIALITY_ORBITS,
      qutritSubspace: SELECTED_TRIALITY_ORBITS * QUTRIT_DIMENSION,
    },
    constants: {
      phaseThetaRad: PHASE_THETA_RAD,
      goldenRatio: GOLDEN_RATIO,
      referenceFrequencyHz: REFERENCE_FREQUENCY_HZ,
      referenceAngularFrequencyRadPerSecond:
        REFERENCE_ANGULAR_FREQUENCY_RAD_S,
    },
    e8: {
      rootCount: roots.length,
      doubledRootNormSquared: dot(roots[0], roots[0]),
      trialityFixedRoots: fixed.length,
      trialityThreeCycles: triples.length,
    },
    selectedGraph: graphSummary(adjacency),
  };
}
