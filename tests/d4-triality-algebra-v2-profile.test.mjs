// SPDX-License-Identifier: MPL-2.0

import assert from "node:assert/strict";
import {
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  rmSync,
  symlinkSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";
import test from "node:test";

import {
  EVENT_COUNT,
  MIDI_DIVISION,
  PROFILE_ID,
  PROFILE_VERSION,
  PROBE_COEFFICIENTS,
  ROBERTS_ANCHOR,
  buildCanonicalProfileContractV2,
  buildEvaluatedOrbitEvents,
  buildEvaluatedOrbitMatrix,
  buildEventDocumentV2,
  buildInvariantProjectionSummary,
  evaluatePolynomialExact,
} from "../src/d4-triality-algebra-v2-profile.mjs";
import {
  ALLOWED_ROOT_ARTIFACT_EXTENSIONS_V2,
  IMPLEMENTATION_SOURCE_PATHS_V2,
  buildArtifactBundleV2,
  buildCsvReceiverV2,
  buildImplementationIdentityV2,
  buildMidiReceiverV2,
} from "../src/d4-triality-algebra-v2-artifacts.mjs";
import { buildSourceBinaryForms } from "../src/d4-triality-covariant-engine.mjs";

const PROJECT_ROOT = resolve(new URL("..", import.meta.url).pathname);
const contractFixture = JSON.parse(
  readFileSync(
    resolve(PROJECT_ROOT, "examples/d4-tia-15.v2.canonical.json"),
    "utf8",
  ),
);
const contractSchema = JSON.parse(
  readFileSync(
    resolve(PROJECT_ROOT, "spec/d4-tia-15.v2.schema.json"),
    "utf8",
  ),
);
const fixtureReceipt = JSON.parse(
  readFileSync(
    resolve(PROJECT_ROOT, "examples/d4-tia-15.v2.receipt.json"),
    "utf8",
  ),
);

test("D4-TIA-15 v2 keeps an exact explicit probe and Roberts anchor", () => {
  assert.equal(PROFILE_ID, "D4-TIA-15");
  assert.equal(PROFILE_VERSION, "2.0.0");
  assert.deepEqual(PROBE_COEFFICIENTS, {
    a0: 1,
    a1: 2,
    a2: 3,
    b0: 4,
    b1: 5,
    b2: 6,
    b3: 7,
  });
  assert.deepEqual(ROBERTS_ANCHOR, { u: 1, v: 0 });

  const { f, g } = buildSourceBinaryForms();
  assert.deepEqual(evaluatePolynomialExact(f), {
    numerator: 1n,
    denominator: 1n,
  });
  assert.deepEqual(evaluatePolynomialExact(g), {
    numerator: 4n,
    denominator: 1n,
  });
});

test("the evaluated covariant matrix is exactly 15 generators by six orbit positions", () => {
  const evaluation = buildEvaluatedOrbitMatrix();
  assert.equal(evaluation.generatorCount, 15);
  assert.equal(evaluation.representativeCount, 6);
  assert.deepEqual(evaluation.orbitOrder, ["e", "S", "T", "ST", "TS", "STS"]);
  assert.equal(evaluation.generators.length, 15);
  assert.ok(
    evaluation.generators.every(
      (generator) =>
        generator.orbitValues.length === 6 &&
        generator.orbitValues.every((value) => value.equivarianceVerified),
    ),
  );
});

test("order-zero invariant projections remain exact and receiver-invariant across orbit", () => {
  const summary = buildInvariantProjectionSummary();
  assert.deepEqual(summary.invariantGeneratorIndices, [4, 10, 12, 13, 15]);
  assert.equal(summary.invariantGeneratorCount, 5);
  assert.equal(summary.exactValueInvariantAcrossOrbit, true);
  assert.equal(summary.audibleControlInvariantAcrossOrbit, true);
  assert.ok(summary.varyingNonInvariantGeneratorCount > 0);

  const document = buildEventDocumentV2();
  for (const generatorIndex of summary.invariantGeneratorIndices) {
    const events = document.events.filter(
      (event) => event.generatorIndex === generatorIndex,
    );
    assert.equal(new Set(events.map((event) => event.evaluation.exactValue)).size, 1);
    assert.equal(new Set(events.map((event) => event.receiverProjection.midiNote)).size, 1);
    assert.equal(new Set(events.map((event) => event.receiverProjection.midiChannel)).size, 1);
    assert.equal(new Set(events.map((event) => event.receiverProjection.velocity)).size, 1);
    assert.equal(new Set(events.map((event) => event.receiverProjection.durationTicks)).size, 1);
    assert.ok(events.every((event) => event.receiverProjection.pitchOffset === 0));
  }
});

test("within-generator exact value classes drive only the authored pitch contour", () => {
  const { evaluation, orbitStrideTicks, events } = buildEvaluatedOrbitEvents();
  assert.equal(orbitStrideTicks, 26);
  assert.equal(events.length, EVENT_COUNT);

  for (const generator of evaluation.generators) {
    const related = events.filter(
      (event) => event.generatorIndex === generator.generatorIndex,
    );
    const classToNote = new Map();
    for (const event of related) {
      const expectedNote =
        event.grading.modularWeight + event.receiverProjection.pitchOffset;
      assert.equal(event.receiverProjection.midiNote, expectedNote);
      assert.ok(event.receiverProjection.midiNote >= 0);
      assert.ok(event.receiverProjection.midiNote <= 127);
      const key = event.evaluation.valueClassIndex;
      if (classToNote.has(key)) {
        assert.equal(classToNote.get(key), event.receiverProjection.midiNote);
      } else {
        classToNote.set(key, event.receiverProjection.midiNote);
      }
    }
  }
});

test("v2 event layout is six derived orbit blocks with the v1 grading clock inside each block", () => {
  const document = buildEventDocumentV2();
  assert.equal(document.eventCount, 90);
  assert.equal(document.orbitStrideTicks, 26);

  for (const event of document.events) {
    assert.equal(
      event.receiverProjection.onsetTick,
      event.orbitIndex * 26 + event.grading.polynomialDegree,
    );
    assert.equal(
      event.receiverProjection.durationTicks,
      event.grading.covariantDegree,
    );
    assert.equal(
      event.receiverProjection.midiChannel,
      event.grading.covariantOrder,
    );
  }
});

test("v2 CSV and MIDI carry all 90 evaluated events without a tempo event", () => {
  const document = buildEventDocumentV2();
  const csv = buildCsvReceiverV2(document);
  assert.equal(csv.trimEnd().split("\n").length, 91);

  const midi = buildMidiReceiverV2(document);
  assert.equal(midi.subarray(0, 4).toString("ascii"), "MThd");
  assert.equal(midi.readUInt16BE(8), 1);
  assert.equal(midi.readUInt16BE(10), 16);
  assert.equal(midi.readUInt16BE(12), MIDI_DIVISION);

  let noteOnCount = 0;
  let hasTempoEvent = false;
  for (let index = 0; index < midi.length - 2; index += 1) {
    if ((midi[index] & 0xf0) === 0x90) noteOnCount += 1;
    if (midi[index] === 0xff && midi[index + 1] === 0x51) {
      hasTempoEvent = true;
    }
  }
  assert.equal(noteOnCount, 90);
  assert.equal(hasTempoEvent, false);
});

test("v2 contract states the authored mapping and exact invariant boundary", () => {
  const contract = buildCanonicalProfileContractV2();
  assert.equal(contract.profileVersion, "2.0.0");
  assert.equal(contract.receiverMapping.orbitStrideTicks.value, 26);
  assert.equal(
    contract.invariantProjection.audibleControlInvariantAcrossOrbit,
    true,
  );
  assert.equal(contract.determinism.noFloatingPointIdentity, true);
  assert.match(contract.claimBoundary, /authored sonification choices/);
  assert.match(contract.claimBoundary, /external synthesizer/);
});

test("v2 manifest binds evaluation, events, receiver artifacts, and implementation", () => {
  const bundle = buildArtifactBundleV2();
  assert.deepEqual(
    bundle.manifest.artifacts.map((artifact) => artifact.filename),
    [
      "contract.json",
      "evaluations.json",
      "events.csv",
      "events.json",
      "events.mid",
    ],
  );
  assert.match(bundle.manifest.evaluationDocumentSha256, /^[0-9a-f]{64}$/);
  assert.match(bundle.manifest.eventDocumentSha256, /^[0-9a-f]{64}$/);
  assert.match(bundle.manifest.mappingContractSha256, /^[0-9a-f]{64}$/);
  assert.equal(
    bundle.manifest.invariantProjection.audibleControlInvariantAcrossOrbit,
    true,
  );

  const identity = buildImplementationIdentityV2();
  assert.deepEqual(
    identity.sourceFiles.map((entry) => entry.path),
    IMPLEMENTATION_SOURCE_PATHS_V2,
  );
  assert.equal(
    identity.sourceNormalization,
    "UTF-8-text;CRLF-and-CR-normalized-to-LF",
  );
});

test("v2 root artifacts remain restricted to JSON, CSV, and MIDI", () => {
  assert.deepEqual(
    [...ALLOWED_ROOT_ARTIFACT_EXTENSIONS_V2].sort(),
    [".csv", ".json", ".mid"],
  );
  const bundle = buildArtifactBundleV2();
  assert.ok(
    bundle.manifest.artifacts.every((artifact) =>
      ALLOWED_ROOT_ARTIFACT_EXTENSIONS_V2.some((extension) =>
        artifact.filename.endsWith(extension),
      ),
    ),
  );
});

test("v2 build command fails closed and emits the exact allowlisted bundle", () => {
  mkdirSync(resolve(PROJECT_ROOT, "dist"), { recursive: true });
  const parent = mkdtempSync(resolve(PROJECT_ROOT, "dist", "d4-tia-v2-test-"));

  const audioOutput = resolve(parent, "audio-request");
  const audioRejected = spawnSync(
    process.execPath,
    ["scripts/build-d4-tia-v2-artifacts.mjs", "--output", audioOutput, "--wav"],
    { cwd: PROJECT_ROOT, encoding: "utf8" },
  );
  assert.notEqual(audioRejected.status, 0);
  assert.equal(existsSync(audioOutput), false);

  const nonempty = resolve(parent, "nonempty");
  mkdirSync(nonempty);
  const marker = resolve(nonempty, "keep.txt");
  writeFileSync(marker, "keep", "utf8");
  const rejected = spawnSync(
    process.execPath,
    ["scripts/build-d4-tia-v2-artifacts.mjs", "--output", nonempty],
    { cwd: PROJECT_ROOT, encoding: "utf8" },
  );
  assert.notEqual(rejected.status, 0);
  assert.equal(readFileSync(marker, "utf8"), "keep");

  const outside = mkdtempSync(resolve(tmpdir(), "d4-tia-v2-outside-"));
  const link = resolve(parent, "escape-link");
  let symlinkCreated = false;
  try {
    symlinkSync(outside, link, "dir");
    symlinkCreated = true;
  } catch (error) {
    if (!["EPERM", "EACCES"].includes(error?.code)) throw error;
  }
  if (symlinkCreated) {
    const escaped = resolve(link, "bundle");
    const symlinkRejected = spawnSync(
      process.execPath,
      ["scripts/build-d4-tia-v2-artifacts.mjs", "--output", escaped],
      { cwd: PROJECT_ROOT, encoding: "utf8" },
    );
    assert.notEqual(symlinkRejected.status, 0);
    assert.equal(existsSync(resolve(outside, "bundle")), false);
  }

  const output = resolve(parent, "bundle");
  const built = spawnSync(
    process.execPath,
    ["scripts/build-d4-tia-v2-artifacts.mjs", "--output", output],
    { cwd: PROJECT_ROOT, encoding: "utf8" },
  );
  assert.equal(built.status, 0, built.stderr || built.stdout);
  assert.deepEqual(readdirSync(output).sort(), [
    "contract.json",
    "evaluations.json",
    "events.csv",
    "events.json",
    "events.mid",
    "manifest.json",
  ]);

  rmSync(outside, { recursive: true, force: true });
  rmSync(parent, { recursive: true, force: true });
});

test("v2 canonical contract, schema, and deterministic document hashes are frozen", () => {
  const contract = buildCanonicalProfileContractV2();
  const bundle = buildArtifactBundleV2();
  assert.deepEqual(contract, contractFixture);
  assert.equal(contractSchema.$id, "qsol.d4-tia-15.profile/v2");
  assert.deepEqual(contractSchema.const, contractFixture);
  assert.equal(bundle.manifest.mappingContractSha256, fixtureReceipt.mappingContractSha256);
  assert.equal(bundle.manifest.evaluationDocumentSha256, fixtureReceipt.evaluationDocumentSha256);
  assert.equal(bundle.manifest.eventDocumentSha256, fixtureReceipt.eventDocumentSha256);
  assert.deepEqual(bundle.manifest.invariantProjection, fixtureReceipt.invariantProjection);
});
