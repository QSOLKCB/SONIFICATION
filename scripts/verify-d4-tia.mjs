// SPDX-License-Identifier: MPL-2.0

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import {
  GENERATOR_COUNT,
  PROFILE_ID,
  PROFILE_VERSION,
  buildCanonicalProfileContract,
  buildEventDocument,
} from "../src/d4-triality-algebra-profile.mjs";
import {
  ALLOWED_ROOT_ARTIFACT_EXTENSIONS,
  buildArtifactBundle,
} from "../src/d4-triality-algebra-artifacts.mjs";

const PROJECT_ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const fixture = JSON.parse(
  readFileSync(
    resolve(PROJECT_ROOT, "examples/d4-tia-15.v1.canonical.json"),
    "utf8",
  ),
);
const schema = JSON.parse(
  readFileSync(resolve(PROJECT_ROOT, "spec/d4-tia-15.v1.schema.json"), "utf8"),
);

const contract = buildCanonicalProfileContract();
assert.deepEqual(contract, fixture);
assert.equal(contract.schema, "qsol.d4-tia-15.profile/v1");
assert.equal(contract.profileId, PROFILE_ID);
assert.equal(contract.profileVersion, PROFILE_VERSION);
assert.equal(schema.properties.profileId.const, PROFILE_ID);
assert.equal(schema.properties.profileVersion.const, PROFILE_VERSION);
for (const key of [
  "source",
  "publishedStructure",
  "mapping",
  "determinism",
  "lineage",
  "claimBoundary",
]) {
  assert.deepEqual(
    schema.properties[key].const,
    contract[key],
    `schema must bind canonical contract section: ${key}`,
  );
}

const document = buildEventDocument();
assert.equal(document.events.length, GENERATOR_COUNT);
for (const event of document.events) {
  const g = event.grading;
  const r = event.receiverProjection;
  assert.equal(g.modularWeight, 4 * g.quadraticDegree + 6 * g.cubicDegree + g.polynomialDegree);
  assert.equal(g.covariantOrder, 2 * g.quadraticDegree + 3 * g.cubicDegree - g.polynomialDegree);
  assert.equal(g.covariantOrder, (g.modularWeight - 3 * g.polynomialDegree) / 2);
  assert.equal(r.onsetTick, g.polynomialDegree);
  assert.equal(r.durationTicks, g.covariantDegree);
  assert.equal(r.midiNote, g.modularWeight);
  assert.equal(r.midiChannel, g.covariantOrder);
}

const bundle = buildArtifactBundle();
assert.deepEqual(
  bundle.manifest.artifacts.map((artifact) => artifact.filename),
  ["contract.json", "events.csv", "events.json", "events.mid"],
);
assert.deepEqual(ALLOWED_ROOT_ARTIFACT_EXTENSIONS, [".json", ".csv", ".mid"]);
assert.ok(bundle.manifest.implementation.sourceFiles.length >= 5);
assert.equal(
  bundle.manifest.implementation.sourceNormalization,
  "UTF-8-text;CRLF-and-CR-normalized-to-LF",
);
assert.match(bundle.manifest.manifestCoreSha256, /^[0-9a-f]{64}$/);

console.log(
  JSON.stringify(
    {
      status: "PASS",
      profile: `${PROFILE_ID}@${PROFILE_VERSION}`,
      generatorCount: document.events.length,
      eventDocumentSha256: bundle.manifest.eventDocumentSha256,
      mappingContractSha256: bundle.manifest.mappingContractSha256,
      implementationSourceBundleSha256:
        bundle.manifest.implementation.sourceBundleSha256,
    },
    null,
    2,
  ),
);
