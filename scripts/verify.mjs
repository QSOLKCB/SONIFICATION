// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this file,
// You can obtain one at https://mozilla.org/MPL/2.0/.
// SPDX-License-Identifier: MPL-2.0
// Copyright (c) 2026 Trent Slade / QSOL-IMC.

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";

import {
  CANONICAL_GENERATOR_WEIGHTS,
  DIMENSIONLESS_STEP_DELTA,
  MODEL_ID,
  MODEL_VERSION,
  PHASE_THETA_RAD,
  basisIndexFromMidiNote,
  buildRootAdjacency,
  buildTernaryMidiCodebook,
  canonicalGeneratorMatrix,
  canonicalModelSummary,
  graphDegreePotential,
  selectEtq101Basis,
  trialityPermutation,
} from "../src/etq-model.mjs";

const contractUrl = new URL(
  "../examples/etq-101.v2.canonical.json",
  import.meta.url,
);
const schemaUrl = new URL("../spec/etq-101.v2.schema.json", import.meta.url);
const contract = JSON.parse(readFileSync(contractUrl, "utf8"));
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

function collectPropertyNames(value, names = new Set()) {
  if (Array.isArray(value)) {
    for (const item of value) collectPropertyNames(item, names);
  } else if (value !== null && typeof value === "object") {
    for (const [key, child] of Object.entries(value)) {
      names.add(key);
      collectPropertyNames(child, names);
    }
  }
  return names;
}

assert.deepEqual(Object.keys(contract).sort(), [
  "$schema",
  "claimBoundary",
  "constants",
  "determinism",
  "dimensions",
  "dynamics",
  "fixtures",
  "legacyProfile",
  "modelId",
  "modelVersion",
  "parameterOrigins",
  "profile",
  "selection",
  "sonification",
  "stateSpace",
]);
assert.equal(contract.$schema, "../spec/etq-101.v2.schema.json");
assert.equal(contract.modelId, MODEL_ID);
assert.equal(contract.modelVersion, MODEL_VERSION);
assert.equal(contract.profile, "compact-101-ternary-midi");

const basis = selectEtq101Basis();
const adjacency = buildRootAdjacency(basis);
const degreePotential = graphDegreePotential(adjacency);
const midiCodebook = buildTernaryMidiCodebook();
const generator = canonicalGeneratorMatrix(adjacency);
const observed = canonicalModelSummary();

assert.deepEqual(contract.dimensions, observed.dimensions);
assert.deepEqual(contract.constants, observed.constants);
assert.equal(contract.constants.phaseThetaRad, PHASE_THETA_RAD);
assert.deepEqual(contract.dynamics.weights, CANONICAL_GENERATOR_WEIGHTS);
assert.deepEqual(contract.dynamics.weights, observed.dynamics.weights);
assert.equal(
  contract.dynamics.dimensionlessStepDelta,
  DIMENSIONLESS_STEP_DELTA,
);
assert.equal(
  contract.dynamics.dimensionlessStepDelta,
  observed.dynamics.dimensionlessStepDelta,
);
assert.equal(contract.fixtures.e8RootCount, observed.e8.rootCount);
assert.equal(contract.fixtures.trialityFixedRoots, observed.e8.trialityFixedRoots);
assert.equal(contract.fixtures.trialityThreeCycles, observed.e8.trialityThreeCycles);
assert.deepEqual(contract.fixtures.selectedGraph, observed.selectedGraph);
assert.deepEqual(
  {
    degreeSum: contract.fixtures.degreePotential.degreeSum,
    meanDegree: contract.fixtures.degreePotential.meanDegree,
    normalizationDenominator:
      contract.fixtures.degreePotential.normalizationDenominator,
    traceNumerator: contract.fixtures.degreePotential.traceNumerator,
    maximumAbsoluteNumerator:
      contract.fixtures.degreePotential.maximumAbsoluteNumerator,
  },
  observed.degreePotential,
);
assert.deepEqual(
  contract.sonification.occupiedNoteRange,
  observed.midiCodebook.occupiedNoteRange,
);
assert.deepEqual(
  contract.sonification.fixedSingletNotes,
  observed.midiCodebook.fixedSingletNotes,
);

assert.equal(
  contract.determinism.basisSha256,
  fixtureSha256(basis),
);
assert.equal(
  contract.determinism.adjacencySha256,
  fixtureSha256(adjacency),
);
assert.equal(
  contract.determinism.degreePotentialNumeratorsSha256,
  fixtureSha256(degreePotential.numerators),
);
assert.equal(
  contract.determinism.midiCodebookSha256,
  fixtureSha256(midiCodebook),
);
assert.equal(
  contract.determinism.contractPayloadSha256,
  contractPayloadSha256(contract),
);

assert.equal(degreePotential.degreeSum, 2 * contract.fixtures.selectedGraph.edges);
assert.equal(
  degreePotential.numerators.reduce((sum, value) => sum + value, 0),
  0,
);
assert.equal(
  Math.max(...degreePotential.numerators.map((value) => Math.abs(value))),
  degreePotential.normalizationDenominator,
);
assert.equal(
  Object.values(contract.dynamics.weights).reduce((sum, value) => sum + value, 0),
  1,
);
assert.equal(contract.dynamics.dimensionlessStepDelta, (2 * Math.PI) / 303);
assert.equal(contract.dynamics.physicalTimeScale, null);
assert.equal(contract.sonification.absoluteFrequencyHz, null);
assert.deepEqual(contract.sonification.allowedArtifactExtensions, [
  ".mid",
  ".csv",
  ".json",
]);
assert.equal(contract.sonification.renderedAudioStatus, "permanently-disabled");

const permutation = trialityPermutation();
for (let row = 0; row < generator.length; row += 1) {
  for (let column = 0; column < generator.length; column += 1) {
    assert.ok(Number.isFinite(generator[row][column]));
    assert.ok(Math.abs(generator[row][column] - generator[column][row]) <= 1e-15);
    assert.ok(
      Math.abs(
        generator[permutation[row]][permutation[column]] -
          generator[row][column],
      ) <= 1e-15,
    );
  }
}

assert.equal(midiCodebook.length, 101);
assert.equal(new Set(midiCodebook.map((entry) => entry.midiNote)).size, 101);
for (const entry of midiCodebook) {
  assert.equal(basisIndexFromMidiNote(entry.midiNote), entry.basisIndex);
}

const forbiddenForwardProperties = [
  "goldenRatio",
  "referenceFrequencyHz",
  "referenceAngularFrequencyRadPerSecond",
  "sampleRateHz",
  "pcmFormat",
  "pcmSha256",
  "wavSha256",
];
const forwardPayload = structuredClone(contract);
delete forwardPayload.legacyProfile;
const forwardPropertyNames = collectPropertyNames(forwardPayload);
for (const forbidden of forbiddenForwardProperties) {
  assert.equal(forwardPropertyNames.has(forbidden), false, `${forbidden} is forbidden`);
}

assert.equal(schema.$schema, "https://json-schema.org/draft/2020-12/schema");
assert.equal(
  schema.$id,
  "https://raw.githubusercontent.com/QSOLKCB/SONIFICATION/main/spec/etq-101.v2.schema.json",
);
assert.equal(schema.type, "object");
assert.equal(schema.additionalProperties, false);
assert.deepEqual([...schema.required].sort(), Object.keys(contract).sort());
assert.equal(schema.properties.modelId.const, contract.modelId);
assert.equal(schema.properties.modelVersion.const, contract.modelVersion);
assert.equal(schema.properties.profile.const, contract.profile);
assert.deepEqual(schema.properties.stateSpace.const, contract.stateSpace);
assert.deepEqual(schema.properties.dimensions.const, contract.dimensions);
assert.deepEqual(schema.properties.constants.const, contract.constants);
assert.deepEqual(schema.properties.selection.const, contract.selection);
assert.deepEqual(schema.properties.dynamics.const, contract.dynamics);
assert.deepEqual(schema.properties.fixtures.const, contract.fixtures);
assert.deepEqual(schema.properties.determinism.const, contract.determinism);
assert.deepEqual(schema.properties.legacyProfile.const, contract.legacyProfile);
assert.deepEqual(
  schema.properties.parameterOrigins.const,
  contract.parameterOrigins,
);
assert.equal(schema.properties.claimBoundary.const, contract.claimBoundary);

const sonificationSchema = schema.properties.sonification;
assert.equal(sonificationSchema.type, "object");
assert.equal(sonificationSchema.additionalProperties, false);
assert.deepEqual(
  [...sonificationSchema.required].sort(),
  Object.keys(contract.sonification).sort(),
);
for (const [key, value] of Object.entries(contract.sonification)) {
  const property = sonificationSchema.properties[key];
  assert.ok(property, `Missing sonification schema property ${key}`);
  if (Object.hasOwn(property, "const")) {
    assert.deepEqual(property.const, value, `Schema const mismatch for ${key}`);
  } else {
    assert.equal(property.type, "null", `Unhandled schema rule for ${key}`);
    assert.equal(value, null, `${key} must be null`);
  }
}

console.log(
  JSON.stringify(
    {
      status: "PASS",
      validation:
        "ETQ-101 v2 structural model, degree potential, ternary MIDI codebook, schema constants, and deterministic receipts",
      summary: observed,
      determinism: contract.determinism,
      legacyProfile: contract.legacyProfile,
    },
    null,
    2,
  ),
);
