// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this file,
// You can obtain one at https://mozilla.org/MPL/2.0/.
// SPDX-License-Identifier: MPL-2.0

import assert from "node:assert/strict";
import test from "node:test";

import {
  BASE_RELEASE,
  BASE_SITE_COUNT,
  EVENT_COUNT,
  FIBRE_DIMENSION,
  FIBRE_PHASE_GAUSSIAN_EXPONENTS,
  buildCanonicalEvents,
  buildEventDocument,
  buildLiftedGraph,
  buildSiteRegistry,
  eventAddress,
  eventIndexFromAddress,
  exactMonomialPower,
  exactMonomialStep,
  gcd,
  tensorAddress,
  tensorIndex,
} from "../src/etq-v3-core.mjs";
import {
  EVENT_CSV_COLUMNS,
  HASH_DOMAINS,
  buildCanonicalContract,
  buildCsvReceiver,
  buildGraphmlReceiver,
  buildMidiReceiver,
  buildNdjsonReceiver,
  buildReceiptAndManifest,
  buildSvgReceiver,
  canonicalObjectSha256,
  canonicalSerialize,
  sha256Bytes,
  utf8,
} from "../src/etq-v3-artifacts.mjs";
import {
  buildRootAdjacency,
  graphDegreePotential,
  selectEtq101Basis,
} from "../src/etq-model.mjs";

function countOccurrences(text, pattern) {
  return text.split(pattern).length - 1;
}

test("the preserved ETQ-101 v2 fixtures are unchanged", () => {
  const basis = selectEtq101Basis();
  const adjacency = buildRootAdjacency(basis);
  const potential = graphDegreePotential(adjacency);
  assert.equal(sha256Bytes(utf8(JSON.stringify(basis))), BASE_RELEASE.basisSha256);
  assert.equal(
    sha256Bytes(utf8(JSON.stringify(adjacency))),
    BASE_RELEASE.adjacencySha256,
  );
  assert.equal(
    sha256Bytes(utf8(JSON.stringify(potential.numerators))),
    BASE_RELEASE.degreePotentialNumeratorsSha256,
  );
});

test("tensor indexing is a bijection on 101 times 3", () => {
  const indices = new Set();
  for (let siteIndex = 0; siteIndex < BASE_SITE_COUNT; siteIndex += 1) {
    for (let fibreLabel = 0; fibreLabel < FIBRE_DIMENSION; fibreLabel += 1) {
      const index = tensorIndex(siteIndex, fibreLabel);
      indices.add(index);
      assert.deepEqual(tensorAddress(index), { siteIndex, fibreLabel });
    }
  }
  assert.equal(indices.size, EVENT_COUNT);
  assert.deepEqual([...indices].sort((a, b) => a - b),
    Array.from({ length: EVENT_COUNT }, (_, index) => index));
});

test("the CRT event traversal visits all 303 addresses exactly once", () => {
  assert.equal(gcd(BASE_SITE_COUNT, FIBRE_DIMENSION), 1);
  const indices = new Set();
  for (let sequenceIndex = 0; sequenceIndex < EVENT_COUNT; sequenceIndex += 1) {
    const address = eventAddress(sequenceIndex);
    indices.add(address.tensorIndex);
    assert.equal(
      eventIndexFromAddress(address.siteIndex, address.fibreLabel),
      sequenceIndex,
    );
  }
  assert.equal(indices.size, EVENT_COUNT);
});

test("the exact monomial step has order 303 and no smaller positive order", () => {
  assert.deepEqual(FIBRE_PHASE_GAUSSIAN_EXPONENTS, [3, 2, 3]);
  for (let power = 1; power < EVENT_COUNT; power += 1) {
    const result = exactMonomialPower(0, 0, power);
    assert.notEqual(result.tensorIndex, 0);
  }
  for (let siteIndex = 0; siteIndex < BASE_SITE_COUNT; siteIndex += 1) {
    for (let fibreLabel = 0; fibreLabel < FIBRE_DIMENSION; fibreLabel += 1) {
      const result = exactMonomialPower(siteIndex, fibreLabel, EVENT_COUNT);
      assert.deepEqual(result, {
        siteIndex,
        fibreLabel,
        tensorIndex: tensorIndex(siteIndex, fibreLabel),
        accumulatedPhaseGaussianExponent: 0,
        accumulatedPhaseSymbol: "1",
      });
    }
  }
});

test("event transitions are exactly the monomial support cycle", () => {
  const events = buildCanonicalEvents();
  assert.equal(events.length, EVENT_COUNT);
  for (const event of events) {
    const transition = exactMonomialStep(event.siteIndex, event.fibreLabel);
    assert.equal(event.tensorIndex, transition.sourceTensorIndex);
    assert.equal(event.nextTensorIndex, transition.targetTensorIndex);
    assert.equal(
      event.transitionPhaseGaussianExponent,
      transition.phaseGaussianExponent,
    );
    assert.equal(
      events[event.nextSequenceIndex].tensorIndex,
      event.nextTensorIndex,
    );
  }
});

test("the site registry preserves root identity and exact labelled degrees", () => {
  const registry = buildSiteRegistry();
  assert.equal(registry.sites.length, BASE_SITE_COUNT);
  assert.equal(new Set(registry.sites.map((site) => site.rootDoubled.join(","))).size, 101);
  assert.equal(
    registry.sites.reduce((sum, site) => sum + site.baseDegree, 0),
    3374,
  );
  assert.equal(
    registry.sites.reduce((sum, site) => sum + site.degreePotentialNumerator, 0),
    0,
  );
  assert.ok(registry.sites.every((site) => site.liftedDegree === site.baseDegree + 2));
  assert.equal(registry.sites.filter((site) => site.fixedIndex !== null).length, 2);
  assert.equal(registry.sites.filter((site) => site.orbitIndex !== null).length, 99);
});

test("G_303 is the exact Cartesian product G_101 square C_3", () => {
  const graph = buildLiftedGraph();
  assert.equal(graph.vertexCount, 303);
  assert.equal(graph.baseEdgesPerLayer, 1687);
  assert.equal(graph.fibreEdgesPerSite, 3);
  assert.equal(graph.edgeCount, 3 * 1687 + 101 * 3);
  assert.equal(graph.minimumDegree, 24);
  assert.equal(graph.maximumDegree, 57);
  assert.equal(graph.connected, true);
  assert.equal(new Set(graph.edges.map((edge) => `${edge.source},${edge.target}`)).size, graph.edges.length);
  assert.ok(graph.edges.every((edge) => edge.source < edge.target));
  assert.equal(graph.edges.filter((edge) => edge.kind === "base-e8-edge").length, 3 * 1687);
  assert.equal(graph.edges.filter((edge) => edge.kind === "fibre-c3-edge").length, 101 * 3);

  const registry = buildSiteRegistry().sites;
  for (let siteIndex = 0; siteIndex < 101; siteIndex += 1) {
    for (let fibreLabel = 0; fibreLabel < 3; fibreLabel += 1) {
      assert.equal(
        graph.degrees[tensorIndex(siteIndex, fibreLabel)],
        registry[siteIndex].liftedDegree,
      );
    }
  }
});

test("the canonical event document separates internal triality from the external fibre", () => {
  const document = buildEventDocument();
  assert.equal(document.events.length, 303);
  assert.equal(document.siteRegistry.length, 101);
  assert.equal(document.graphContext.eventTraversalIsGraphWalk, false);
  const internalLabels = new Set(
    document.siteRegistry
      .map((site) => site.internalTrialityLabel)
      .filter((value) => value !== null),
  );
  const externalLabels = new Set(document.events.map((event) => event.fibreLabel));
  assert.deepEqual(internalLabels, new Set([0, 1, 2]));
  assert.deepEqual(externalLabels, new Set([0, 1, 2]));
  assert.equal(
    document.events.filter((event) => event.siteIndex === 0).length,
    3,
  );
});

test("canonical serialization rejects floating identity values", () => {
  assert.equal(canonicalSerialize({ b: 2, a: 1 }), '{"a":1,"b":2}');
  assert.throws(() => canonicalSerialize({ value: Math.PI }), /safe integers only/);
  assert.throws(() => canonicalSerialize({ value: Number.NaN }), /safe integers only/);
});

test("all reference receivers are deterministic projections of the same event document", () => {
  const document = buildEventDocument();
  const csv = buildCsvReceiver(document);
  assert.equal(csv.trimEnd().split("\n").length, EVENT_COUNT + 1);
  assert.deepEqual(csv.split("\n", 1)[0].split(","), EVENT_CSV_COLUMNS);

  const ndjson = buildNdjsonReceiver(document);
  assert.equal(ndjson.trimEnd().split("\n").length, EVENT_COUNT);

  const graphml = buildGraphmlReceiver(document, buildLiftedGraph());
  assert.equal(countOccurrences(graphml, "<node "), EVENT_COUNT);
  assert.equal(countOccurrences(graphml, "<edge "), 5364);

  const svg = buildSvgReceiver(document);
  assert.equal(countOccurrences(svg, '<rect class="node"'), EVENT_COUNT);

  const midi = buildMidiReceiver(document);
  assert.equal(midi.subarray(0, 4).toString("ascii"), "MThd");
  assert.equal(midi.subarray(14, 18).toString("ascii"), "MTrk");
  assert.equal(midi.readUInt16BE(12), 1);
  const statusBytes = [...midi].filter((byte) => (byte & 0xf0) === 0x90 || (byte & 0xf0) === 0x80);
  assert.equal(statusBytes.length, EVENT_COUNT * 2);
});

test("contract, receipt, and manifest form an acyclic deterministic identity chain", () => {
  const contract = buildCanonicalContract();
  const payload = structuredClone(contract);
  delete payload.$schema;
  delete payload.determinism.contractPayloadSha256;
  assert.equal(
    contract.determinism.contractPayloadSha256,
    canonicalObjectSha256(HASH_DOMAINS.contract, payload),
  );
  const bundle = buildReceiptAndManifest();
  assert.equal(bundle.receipt.receivers.length, 6);
  assert.equal(bundle.manifest.artifacts.length, 9);
  assert.ok(!bundle.manifest.artifacts.some((artifact) => artifact.filename === "manifest.json"));
  assert.equal(
    bundle.receipt.eventCommitment.canonicalEventDocumentSha256,
    contract.determinism.eventDocumentSha256,
  );
});
