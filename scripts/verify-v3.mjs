// SPDX-License-Identifier: MPL-2.0
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { extname } from "node:path";

import {
  BASE_RELEASE,
  EVENT_COUNT,
  FIBRE_PHASE_GAUSSIAN_SYMBOLS,
  buildEventDocument,
  exactInvariantSummary,
} from "../src/etq-v3-core.mjs";
import {
  ALLOWED_ROOT_ARTIFACT_EXTENSIONS,
  BUNDLE_CONTRACT_SCHEMA_PATH,
  CONTRACT_PATH,
  HASH_DOMAINS,
  buildCanonicalContract,
  buildContractSchema,
  buildImplementationIdentity,
  buildReceiptAndManifest,
  canonicalObjectSha256,
  canonicalSerialize,
} from "../src/etq-v3-artifacts.mjs";

const contract = JSON.parse(readFileSync(CONTRACT_PATH, "utf8"));
const schema = JSON.parse(readFileSync("spec/etq-303.v3.schema.json", "utf8"));
const observedContract = buildCanonicalContract();
const observedSchema = buildContractSchema(observedContract);
assert.deepEqual(contract, observedContract);
assert.deepEqual(schema, observedSchema);
assert.equal(canonicalSerialize(contract), readFileSync(CONTRACT_PATH, "utf8"));
assert.equal(canonicalSerialize(schema), readFileSync("spec/etq-303.v3.schema.json", "utf8"));

const payload = structuredClone(contract);
delete payload.$schema;
delete payload.determinism.contractPayloadSha256;
assert.equal(
  contract.determinism.contractPayloadSha256,
  canonicalObjectSha256(HASH_DOMAINS.contract, payload),
);
assert.equal(contract.determinism.preservedV2BasisFixtureSha256, BASE_RELEASE.basisSha256);
assert.equal(contract.determinism.preservedV2AdjacencyFixtureSha256, BASE_RELEASE.adjacencySha256);
assert.equal(
  contract.determinism.preservedV2DegreePotentialNumeratorsFixtureSha256,
  BASE_RELEASE.degreePotentialNumeratorsSha256,
);
assert.deepEqual(
  contract.exactMathematics.monomialStep.gaussianPhaseSymbols,
  FIBRE_PHASE_GAUSSIAN_SYMBOLS,
);
assert.deepEqual(contract.lineage.implementation, buildImplementationIdentity());
assert.equal(
  contract.determinism.implementationSourceBundleSha256,
  contract.lineage.implementation.sourceBundleSha256,
);

const invariants = exactInvariantSummary();
assert.equal(invariants.dimensions.total, EVENT_COUNT);
assert.equal(invariants.eventTraversal.uniqueTensorIndices, EVENT_COUNT);
assert.equal(invariants.eventTraversal.uniqueAddresses, EVENT_COUNT);
assert.equal(invariants.monomialStep.after303.tensorIndex, 0);
assert.equal(invariants.monomialStep.after303.accumulatedPhaseGaussianExponent, 0);
assert.equal(invariants.graph.vertices, EVENT_COUNT);
assert.equal(invariants.graph.edges, 5364);

const eventDocument = buildEventDocument();
assert.equal(
  contract.determinism.eventDocumentSha256,
  canonicalObjectSha256(HASH_DOMAINS.eventDocument, eventDocument),
);

const bundle = buildReceiptAndManifest();
assert.equal(bundle.receiverArtifacts.length, 5);
assert.equal(bundle.receipt.receivers.length, 5);
assert.equal(bundle.manifest.artifacts.length, 8);
assert.equal(bundle.contract.$schema, BUNDLE_CONTRACT_SCHEMA_PATH);
assert.equal(bundle.contractSchema.$id, BUNDLE_CONTRACT_SCHEMA_PATH);
assert.equal(bundle.contractSchema.properties.$schema.const, BUNDLE_CONTRACT_SCHEMA_PATH);
assert.equal(
  bundle.contract.determinism.contractPayloadSha256,
  contract.determinism.contractPayloadSha256,
);
assert.deepEqual(bundle.receipt.implementation, contract.lineage.implementation);
assert.deepEqual(bundle.manifest.lineage.implementation, contract.lineage.implementation);
const allowedExtensions = new Set(ALLOWED_ROOT_ARTIFACT_EXTENSIONS);
for (const artifact of bundle.manifest.artifacts) {
  assert.ok(
    allowedExtensions.has(extname(artifact.filename)),
    `disallowed root artifact extension: ${artifact.filename}`,
  );
}
assert.equal(
  bundle.receipt.eventCommitment.canonicalEventDocumentSha256,
  contract.determinism.eventDocumentSha256,
);

console.log(
  JSON.stringify(
    {
      status: "PASS",
      validation:
        "ETQ-303 v3 exact tensor state space, 303-cycle monomial support, Cartesian graph lift, event protocol, allowlisted receiver projections, implementation identity, bundle-local schema, and acyclic receipts",
      invariants,
      determinism: contract.determinism,
      implementation: contract.lineage.implementation,
      receiptCoreSha256: bundle.receipt.receiptCoreSha256,
      manifestCoreSha256: bundle.manifest.manifestCoreSha256,
    },
    null,
    2,
  ),
);
