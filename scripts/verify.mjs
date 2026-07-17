// SPDX-License-Identifier: LicenseRef-QSOL-IMC-Core-Proprietary-1.0
// Copyright (c) 2026 Trent Slade. All Rights Reserved.

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";

import {
  buildRootAdjacency,
  canonicalModelSummary,
  selectEtq101Basis,
} from "../src/etq-model.mjs";

const exampleUrl = new URL("../examples/etq-101.canonical.json", import.meta.url);
const schemaUrl = new URL("../spec/etq-101.schema.json", import.meta.url);
const contract = JSON.parse(readFileSync(exampleUrl, "utf8"));
const schema = JSON.parse(readFileSync(schemaUrl, "utf8"));

function sha256Utf8(value) {
  return createHash("sha256").update(value, "utf8").digest("hex");
}

function fixtureSha256(value) {
  return sha256Utf8(JSON.stringify(value));
}

function stableSerialize(value) {
  if (Array.isArray(value)) {
    return `[${value.map(stableSerialize).join(",")}]`;
  }
  if (value !== null && typeof value === "object") {
    const members = Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${stableSerialize(value[key])}`);
    return `{${members.join(",")}}`;
  }
  return JSON.stringify(value);
}

function contractPayloadSha256(value) {
  const payload = structuredClone(value);
  delete payload.$schema;
  delete payload.determinism.contractPayloadSha256;
  return sha256Utf8(stableSerialize(payload));
}

const expected = {
  stateSpace: {
    type: "root-indexed-graph-hilbert-space",
    basisInnerProduct: "<r|s>=kronecker-delta",
    decomposition: "C^2 direct-sum (C^33 tensor C^3)",
    qutritBlockSemantics: "33-mutually-exclusive-direct-sum-blocks",
  },
  dimensions: {
    total: 101,
    fixedSinglets: 2,
    qutritOrbits: 33,
    qutritSubspace: 99,
  },
  constants: {
    phaseThetaRad: Math.PI / 2,
    goldenRatio: (1 + Math.sqrt(5)) / 2,
    referenceFrequencyHz: 432,
    referenceAngularFrequencyRadPerSecond: 2 * Math.PI * 432,
  },
  selection: {
    coordinateEncoding: "doubled-integer-e8-roots",
    algorithm: "lexicographic-triality-closed-v1",
    hilbertSpaceConstruction: "ell2-of-selected-root-labels",
    fixedRoots: 2,
    completeTrialityOrbits: 33,
  },
  dynamics: {
    form: "floquet",
    continuousGenerator: "K=0.55*L_E_bar+0.25*L_Q_bar+0.20*V_phi",
    floquetOperator: "U_F=exp(-i*tau*K)*F_Q",
    graphNormalization: "two-times-maximum-degree",
    dimensionlessStepTau: (2 * Math.PI) / 303,
    dimensionlessStepTauExpression: "2*pi/303",
    timeStepSeconds: 1 / (303 * 432),
    timeStepSecondsExpression: "1/(303*432)",
    initialStateRecipe: "ouroboros-golden-scl-v1",
    weights: {
      e8RootGraph: 0.55,
      qutritHopping: 0.25,
      goldenOrbitPotential: 0.2,
      sclStatic: 0,
      qutritNumber: 0,
      ouroborosRing: 0,
    },
    phaseDrive: {
      operator: "diag(1,-2,1)",
      thetaRad: Math.PI / 2,
      stepOrder: [
        "scl-phase-kick",
        "triality-shift",
        "continuous-generator",
      ],
      trialityCovariantOrbit: [0, 1, 2],
    },
  },
  sonification: {
    mappingId: "generator-spectrum-v1",
    renderStatus: "specified-not-implemented",
    spectralSource: "dimensionless-generator-K",
    trajectoryUsed: false,
    initialStateRecipe: "ouroboros-golden-scl-v1",
    referenceFrequencyHz: 432,
    pitchMapId: "golden-band-v1",
    pitchMap: "f_l=f0*2^(goldenRatio*xi_l)",
    normalizedSpectralDomain: [-1, 1],
    amplitudeMapId: "spectral-projector-sqrt-v1",
    amplitudeMap: "a_l=sqrt(Tr(rho0*P_l))",
    oscillatorPhaseMapId: "zero-v1",
    stereoMapId: "triality-equal-power-v1",
    epsilonMu: 1e-12,
    eigenvalueAbsoluteTolerance: 1e-10,
    eigenvalueRelativeTolerance: 1e-10,
    durationSeconds: 20,
    sampleRateHz: 48000,
    channels: 2,
    windowId: "raised-cosine-edge-v1",
    edgeFadeSeconds: 0.02,
    peakCeiling: 0.98,
    silencePolicy: "emit-zero-pcm",
    pcmFormat: "s16le",
    quantizer: "nearest-ties-away-from-zero-v1",
    dither: "none",
    numericRuntimeId: null,
    eigensolverId: null,
    renderManifestPayloadSha256: null,
    pcmSha256: null,
  },
  fixtures: {
    e8RootCount: 240,
    trialityFixedRoots: 12,
    trialityThreeCycles: 76,
    selectedGraph: {
      vertices: 101,
      edges: 1687,
      minimumDegree: 22,
      maximumDegree: 55,
      connected: true,
    },
  },
  determinism: {
    fixtureSerialization:
      "UTF-8(JSON.stringify(value)); compact; no BOM; no trailing newline",
    contractCanonicalization: "recursive-lexicographic-object-keys-json-v1",
    contractPayloadRule:
      "remove $schema and determinism.contractPayloadSha256 before canonicalization",
    basisSha256:
      "97cfd1f087745422fd66d3640c7b86c3209593c4b53741018c08a5e9cdb15f6f",
    adjacencySha256:
      "29ae0af5b1090c9de30f1efc25789060fb1791eb175d2afcd6888847f7fe6324",
    contractPayloadSha256:
      "9c6d8c5bc5b630d0ad276e9d0970a8d2da2d11455eb9877ee01d23cf1f17835c",
  },
  claimBoundary:
    "A deterministic 101-dimensional root-indexed Hilbert space built from an E8 root-graph truncation closed under an embedded D4 triality. It is not a 101-dimensional representation of E8, and 432 Hz is a declared sonification scale.",
};

assert.deepEqual(Object.keys(contract).sort(), [
  "$schema",
  "claimBoundary",
  "constants",
  "determinism",
  "dimensions",
  "dynamics",
  "fixtures",
  "modelId",
  "modelVersion",
  "profile",
  "selection",
  "sonification",
  "stateSpace",
]);
assert.equal(contract.$schema, "../spec/etq-101.schema.json");
assert.equal(contract.modelId, "ETQ-101");
assert.equal(contract.modelVersion, "1.0.0");
assert.equal(contract.profile, "compact-101");
for (const key of [
  "stateSpace",
  "dimensions",
  "constants",
  "selection",
  "dynamics",
  "sonification",
  "fixtures",
  "determinism",
]) {
  assert.deepEqual(contract[key], expected[key], `Canonical ${key} mismatch`);
}
assert.equal(contract.claimBoundary, expected.claimBoundary);

const basis = selectEtq101Basis();
const adjacency = buildRootAdjacency(basis);
const observed = canonicalModelSummary();
const observedHashes = {
  basisSha256: fixtureSha256(basis),
  adjacencySha256: fixtureSha256(adjacency),
};

assert.equal(contract.modelId, observed.modelId);
assert.equal(contract.modelVersion, observed.modelVersion);
assert.deepEqual(contract.dimensions, observed.dimensions);
assert.deepEqual(contract.constants, observed.constants);
assert.equal(contract.fixtures.e8RootCount, observed.e8.rootCount);
assert.equal(contract.fixtures.trialityFixedRoots, observed.e8.trialityFixedRoots);
assert.equal(contract.fixtures.trialityThreeCycles, observed.e8.trialityThreeCycles);
assert.deepEqual(contract.fixtures.selectedGraph, observed.selectedGraph);
assert.equal(contract.determinism.basisSha256, observedHashes.basisSha256);
assert.equal(contract.determinism.adjacencySha256, observedHashes.adjacencySha256);
assert.equal(
  contract.determinism.contractPayloadSha256,
  contractPayloadSha256(contract),
);

assert.equal(
  contract.dimensions.total,
  contract.dimensions.fixedSinglets + 3 * contract.dimensions.qutritOrbits,
);
assert.equal(
  contract.dimensions.qutritSubspace,
  3 * contract.dimensions.qutritOrbits,
);
assert.equal(contract.constants.phaseThetaRad, Math.PI / 2);
assert.equal(contract.constants.goldenRatio, (1 + Math.sqrt(5)) / 2);
assert.equal(
  contract.constants.referenceAngularFrequencyRadPerSecond,
  2 * Math.PI * contract.constants.referenceFrequencyHz,
);
assert.equal(contract.dynamics.phaseDrive.thetaRad, contract.constants.phaseThetaRad);
assert.equal(
  contract.sonification.referenceFrequencyHz,
  contract.constants.referenceFrequencyHz,
);
assert.equal(contract.dynamics.dimensionlessStepTau, (2 * Math.PI) / 303);
assert.equal(
  contract.dynamics.timeStepSeconds,
  contract.dynamics.dimensionlessStepTau /
    contract.constants.referenceAngularFrequencyRadPerSecond,
);
assert.equal(
  Object.values(contract.dynamics.weights).reduce((sum, value) => sum + value, 0),
  1,
);

assert.equal(schema.$schema, "https://json-schema.org/draft/2020-12/schema");
assert.equal(
  schema.$id,
  "https://raw.githubusercontent.com/QSOLKCB/SONIFICATION/main/spec/etq-101.schema.json",
);
assert.equal(
  schema.properties.determinism.properties.contractPayloadSha256.const,
  contract.determinism.contractPayloadSha256,
);

console.log(
  JSON.stringify(
    {
      status: "PASS",
      validation:
        "Exact canonical instance, cross-field relations, schema parse, and deterministic fixtures",
      summary: observed,
      determinism: contract.determinism,
    },
    null,
    2,
  ),
);
