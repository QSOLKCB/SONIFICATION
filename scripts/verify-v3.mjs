// SPDX-License-Identifier: MPL-2.0
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

import {
  BASE_RELEASE,
  EVENT_COUNT,
  buildEventDocument,
  exactInvariantSummary,
} from "../src/etq-v3-core.mjs";
import {
  CONTRACT_PATH,
  HASH_DOMAINS,
  buildCanonicalContract,
  buildContractSchema,
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
assert.equal(
  canonicalSerialize(schema),
  readFileSync("spec/etq-303.v3.schema.json", "utf8"),
);

const payload = structuredClone(contract);
delete payload.$schema;
delete payload.determinism.contractPayloadSha256;
assert.equal(
  contract.determinism.contractPayloadSha256,
  canonicalObjectSha256(HASH_DOMAINS.contract, payload),
);
assert.equal(
  contract.determinism.preservedV2BasisFixtureSha256,
  BASE_RELEASE.basisSha256,
);
assert.equal(
  contract.determinism.preservedV2AdjacencyFixtureSha256,
  BASE_RELEASE.adjacencySha256,
);
assert.equal(
  contract.determinism.preservedV2DegreePotentialNumeratorsFixtureSha256,
  BASE_RELEASE.degreePotentialNumeratorsSha256,
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
assert.equal(bundle.receiverArtifacts.length, 6);
assert.equal(bundle.receipt.receivers.length, 6);
assert.equal(bundle.manifest.artifacts.length, 9);
assert.equal(
  bundle.receipt.eventCommitment.canonicalEventDocumentSha256,
  contract.determinism.eventDocumentSha256,
);

console.log(
  JSON.stringify(
    {
      status: "PASS",
      validation:
        "ETQ-303 v3 exact tensor state space, 303-cycle monomial support, Cartesian graph lift, event protocol, receiver projections, schema, and acyclic receipts",
      invariants,
      determinism: contract.determinism,
      receiptCoreSha256: bundle.receipt.receiptCoreSha256,
      manifestCoreSha256: bundle.manifest.manifestCoreSha256,
    },
    null,
    2,
  ),
);
