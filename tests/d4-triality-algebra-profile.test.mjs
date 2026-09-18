// SPDX-License-Identifier: MPL-2.0

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import {
  mkdirSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { extname, resolve } from "node:path";
import test from "node:test";

import {
  GENERATOR_COUNT,
  MIDI_DIVISION,
  MIDI_VELOCITY,
  PROFILE_ID,
  PROFILE_VERSION,
  buildCanonicalProfileContract,
  buildEventDocument,
  buildGeneratorEvents,
} from "../src/d4-triality-algebra-profile.mjs";
import {
  ALLOWED_ROOT_ARTIFACT_EXTENSIONS,
  EVENT_CSV_COLUMNS,
  IMPLEMENTATION_SOURCE_PATHS,
  buildArtifactBundle,
  buildCsvReceiver,
  buildImplementationIdentity,
  buildMidiReceiver,
} from "../src/d4-triality-algebra-artifacts.mjs";
import { D4_TRIALITY_INVARIANT_GENERATORS } from "../src/d4-triality-reference.mjs";

const PROJECT_ROOT = resolve(new URL("..", import.meta.url).pathname);

test("D4-TIA-15 is separately versioned from ETQ", () => {
  assert.equal(PROFILE_ID, "D4-TIA-15");
  assert.equal(PROFILE_VERSION, "1.0.0");
  assert.equal(GENERATOR_COUNT, 15);
  const contract = buildCanonicalProfileContract();
  assert.equal(contract.status, "separate-noncanonical-research-profile");
  assert.match(contract.lineage.relationToEtq, /does not modify ETQ-101 v2 or ETQ-303 v3/);
});

test("all 15 published generators survive with their grading ledger intact", () => {
  const events = buildGeneratorEvents();
  assert.equal(events.length, D4_TRIALITY_INVARIANT_GENERATORS.length);
  for (let index = 0; index < events.length; index += 1) {
    const source = D4_TRIALITY_INVARIANT_GENERATORS[index];
    const event = events[index];
    assert.equal(event.sequenceIndex, index);
    assert.equal(event.generatorIndex, source.index);
    assert.equal(event.label, source.label);
    assert.equal(event.grading.quadraticDegree, source.quadraticDegree);
    assert.equal(event.grading.cubicDegree, source.cubicDegree);
    assert.equal(event.grading.polynomialDegree, source.polynomialDegree);
    assert.equal(event.grading.modularWeight, source.modularWeight);
    assert.equal(event.grading.covariantOrder, source.covariantOrder);
    assert.equal(
      event.grading.covariantDegree,
      source.quadraticDegree + source.cubicDegree,
    );
  }
});

test("v1 sonification uses identity transfers without rescaling published grades", () => {
  for (const event of buildGeneratorEvents()) {
    const g = event.grading;
    const r = event.receiverProjection;
    assert.equal(r.onsetTick, g.polynomialDegree);
    assert.equal(r.durationTicks, g.covariantDegree);
    assert.equal(r.midiNote, g.modularWeight);
    assert.equal(r.midiChannel, g.covariantOrder);
    assert.equal(r.velocity, MIDI_VELOCITY);
  }
  const contract = buildCanonicalProfileContract();
  assert.equal(contract.mapping.onsetTick.transfer, "identity");
  assert.equal(contract.mapping.durationTicks.transfer, "identity");
  assert.equal(contract.mapping.midiNote.transfer, "identity");
  assert.equal(contract.mapping.midiChannel.transfer, "identity");
  assert.equal(contract.mapping.tempoMicrosecondsPerQuarter, null);
  assert.equal(contract.mapping.absoluteFrequencyHz, null);
});

test("event document preserves all source grades and explicit authored boundaries", () => {
  const document = buildEventDocument();
  assert.equal(document.events.length, 15);
  assert.equal(new Set(document.events.map((event) => event.generatorIndex)).size, 15);
  assert.deepEqual(
    [...new Set(document.events.map((event) => event.family))].sort(),
    ["cubic", "joint", "quadratic"],
  );
  assert.match(document.claimBoundary, /authored identity-transfer receiver convention/);
});

test("CSV is a lossless auditable table of the 15 events", () => {
  const csv = buildCsvReceiver();
  const lines = csv.trimEnd().split("\n");
  assert.equal(lines.length, 16);
  assert.deepEqual(lines[0].split(","), EVENT_CSV_COLUMNS);
  assert.ok(lines.some((line) => line.includes("cubic-discriminant=(P,P)_2")));
});

test("MIDI is a 16-track symbolic projection with no tempo event", () => {
  const midi = buildMidiReceiver();
  assert.equal(midi.subarray(0, 4).toString("ascii"), "MThd");
  assert.equal(midi.readUInt32BE(4), 6);
  assert.equal(midi.readUInt16BE(8), 1);
  assert.equal(midi.readUInt16BE(10), 16);
  assert.equal(midi.readUInt16BE(12), MIDI_DIVISION);
  assert.equal(midi.includes(Buffer.from([0xff, 0x51])), false);
  const noteOns = [...midi].filter((byte) => (byte & 0xf0) === 0x90);
  assert.equal(noteOns.length, 15);
});

test("artifact manifest binds contract, events, receivers, and implementation", () => {
  const bundle = buildArtifactBundle();
  assert.deepEqual(
    bundle.manifest.artifacts.map((artifact) => artifact.filename),
    ["contract.json", "events.csv", "events.json", "events.mid"],
  );
  assert.equal(bundle.manifest.profileId, PROFILE_ID);
  assert.equal(bundle.manifest.profileVersion, PROFILE_VERSION);
  assert.match(bundle.manifest.mappingContractSha256, /^[0-9a-f]{64}$/);
  assert.match(bundle.manifest.eventDocumentSha256, /^[0-9a-f]{64}$/);
  assert.match(bundle.manifest.manifestCoreSha256, /^[0-9a-f]{64}$/);
  assert.deepEqual(
    buildImplementationIdentity().sourceFiles.map((entry) => entry.path),
    IMPLEMENTATION_SOURCE_PATHS,
  );
});

test("root artifacts remain restricted to JSON, CSV, and MIDI", () => {
  const allowed = new Set(ALLOWED_ROOT_ARTIFACT_EXTENSIONS);
  for (const artifact of buildArtifactBundle().manifest.artifacts) {
    assert.ok(allowed.has(extname(artifact.filename)));
  }
});

test("build command fails closed on nonempty output and emits the exact bundle", () => {
  mkdirSync(resolve(PROJECT_ROOT, "dist"), { recursive: true });
  const parent = mkdtempSync(resolve(PROJECT_ROOT, "dist", "d4-tia-test-"));
  const nonempty = resolve(parent, "nonempty");
  mkdirSync(nonempty);
  writeFileSync(resolve(nonempty, "sentinel.txt"), "keep", "utf8");

  const rejected = spawnSync(
    process.execPath,
    ["scripts/build-d4-tia-artifacts.mjs", "--output", nonempty],
    { cwd: PROJECT_ROOT, encoding: "utf8" },
  );
  assert.notEqual(rejected.status, 0);
  assert.equal(readFileSync(resolve(nonempty, "sentinel.txt"), "utf8"), "keep");

  const output = resolve(parent, "bundle");
  const built = spawnSync(
    process.execPath,
    ["scripts/build-d4-tia-artifacts.mjs", "--output", output],
    { cwd: PROJECT_ROOT, encoding: "utf8" },
  );
  assert.equal(built.status, 0, built.stderr || built.stdout);
  assert.deepEqual(readdirSync(output).sort(), [
    "contract.json",
    "events.csv",
    "events.json",
    "events.mid",
    "manifest.json",
  ]);
  rmSync(parent, { recursive: true, force: true });
});
