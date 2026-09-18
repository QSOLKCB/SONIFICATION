// SPDX-License-Identifier: MPL-2.0

import assert from "node:assert/strict";

import {
  EVENT_COUNT,
  PROFILE_ID,
  PROFILE_VERSION,
  buildCanonicalProfileContractV2,
  buildEventDocumentV2,
  buildInvariantProjectionSummary,
} from "../src/d4-triality-algebra-v2-profile.mjs";
import {
  buildArtifactBundleV2,
  buildMidiReceiverV2,
} from "../src/d4-triality-algebra-v2-artifacts.mjs";

const contract = buildCanonicalProfileContractV2();
const document = buildEventDocumentV2();
const invariant = buildInvariantProjectionSummary();
const bundle = buildArtifactBundleV2();

assert.equal(PROFILE_ID, "D4-TIA-15");
assert.equal(PROFILE_VERSION, "2.0.0");
assert.equal(document.eventCount, EVENT_COUNT);
assert.equal(document.eventCount, 90);
assert.equal(document.orbitSize, 6);
assert.equal(document.generatorCount, 15);
assert.equal(document.orbitStrideTicks, 26);
assert.deepEqual(invariant.invariantGeneratorIndices, [4, 10, 12, 13, 15]);
assert.equal(invariant.invariantGeneratorCount, 5);
assert.equal(invariant.exactValueInvariantAcrossOrbit, true);
assert.equal(invariant.audibleControlInvariantAcrossOrbit, true);
assert.ok(invariant.varyingNonInvariantGeneratorCount > 0);
assert.equal(
  contract.invariantProjection.audibleControlInvariantAcrossOrbit,
  true,
);
assert.match(bundle.manifest.evaluationDocumentSha256, /^[0-9a-f]{64}$/);
assert.match(bundle.manifest.eventDocumentSha256, /^[0-9a-f]{64}$/);
assert.match(bundle.manifest.mappingContractSha256, /^[0-9a-f]{64}$/);
assert.match(bundle.manifest.manifestCoreSha256, /^[0-9a-f]{64}$/);

const midi = buildMidiReceiverV2(document);
assert.equal(midi.readUInt16BE(8), 1);
assert.equal(midi.readUInt16BE(10), 16);
assert.equal(midi.readUInt16BE(12), 1);
for (let index = 0; index < midi.length - 1; index += 1) {
  assert.notEqual(
    midi[index] === 0xff && midi[index + 1] === 0x51,
    true,
    "D4-TIA-15 v2 MIDI must not contain a tempo event",
  );
}

console.log(
  JSON.stringify(
    {
      status: "PASS",
      profile: `${PROFILE_ID}@${PROFILE_VERSION}`,
      eventCount: document.eventCount,
      orbitStrideTicks: document.orbitStrideTicks,
      invariantProjection: invariant,
      mappingContractSha256: bundle.manifest.mappingContractSha256,
      evaluationDocumentSha256: bundle.manifest.evaluationDocumentSha256,
      eventDocumentSha256: bundle.manifest.eventDocumentSha256,
      manifestCoreSha256: bundle.manifest.manifestCoreSha256,
      contract,
    },
    null,
    2,
  ),
);
