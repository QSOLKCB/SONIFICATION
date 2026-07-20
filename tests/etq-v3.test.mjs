// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this file,
// You can obtain one at https://mozilla.org/MPL/2.0/.
// SPDX-License-Identifier: MPL-2.0

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import {
  existsSync,
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
  BASE_RELEASE,
  BASE_SITE_COUNT,
  EVENT_COUNT,
  FIBRE_DIMENSION,
  FIBRE_PHASE_GAUSSIAN_EXPONENTS,
  FIBRE_PHASE_GAUSSIAN_SYMBOLS,
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
  ALLOWED_ROOT_ARTIFACT_EXTENSIONS,
  BUNDLE_CONTRACT_SCHEMA_PATH,
  EVENT_CSV_COLUMNS,
  HASH_DOMAINS,
  IMPLEMENTATION_SOURCE_PATHS,
  buildCanonicalContract,
  buildCsvReceiver,
  buildEventAtlasJsonReceiver,
  buildGraphJsonReceiver,
  buildImplementationIdentity,
  buildMidiReceiver,
  buildReceiptAndManifest,
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

const PROJECT_ROOT = resolve(new URL("..", import.meta.url).pathname);

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
  assert.deepEqual(
    [...indices].sort((a, b) => a - b),
    Array.from({ length: EVENT_COUNT }, (_, index) => index),
  );
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

test("the exact monomial step has order 303 and aligned phase labels", () => {
  assert.deepEqual(FIBRE_PHASE_GAUSSIAN_EXPONENTS, [3, 2, 3]);
  assert.deepEqual(FIBRE_PHASE_GAUSSIAN_SYMBOLS, ["-i", "-1", "-i"]);
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
  const contract = buildCanonicalContract();
  assert.deepEqual(
    contract.exactMathematics.monomialStep.gaussianPhaseSymbols,
    ["-i", "-1", "-i"],
  );
  assert.deepEqual(
    contract.exactMathematics.monomialStep.gaussianUnitSymbolLookup,
    ["1", "i", "-1", "-i"],
  );
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
  assert.deepEqual(document.exactStep.gaussianPhaseSymbols, ["-i", "-1", "-i"]);
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

test("all reference receivers are deterministic allowlisted projections", () => {
  const document = buildEventDocument();
  const csv = buildCsvReceiver(document);
  assert.equal(csv.trimEnd().split("\n").length, EVENT_COUNT + 1);
  assert.deepEqual(csv.split("\n", 1)[0].split(","), EVENT_CSV_COLUMNS);

  const graph = JSON.parse(buildGraphJsonReceiver(document, buildLiftedGraph()));
  assert.equal(graph.nodes.length, EVENT_COUNT);
  assert.equal(graph.edges.length, 5364);
  assert.equal(graph.connected, true);

  const atlas = JSON.parse(buildEventAtlasJsonReceiver(document));
  assert.equal(atlas.entries.length, EVENT_COUNT);
  assert.equal(atlas.columns, 101);
  assert.equal(atlas.rows, 3);

  const midi = buildMidiReceiver(document);
  assert.equal(midi.subarray(0, 4).toString("ascii"), "MThd");
  assert.equal(midi.subarray(14, 18).toString("ascii"), "MTrk");
  assert.equal(midi.readUInt16BE(12), 1);
  const statusBytes = [...midi].filter((byte) => (byte & 0xf0) === 0x90 || (byte & 0xf0) === 0x80);
  assert.equal(statusBytes.length, EVENT_COUNT * 2);

  const bundle = buildReceiptAndManifest();
  const allowed = new Set(ALLOWED_ROOT_ARTIFACT_EXTENSIONS);
  assert.deepEqual(
    bundle.receiverArtifacts.map((artifact) => artifact.filename),
    ["events.json", "events.csv", "graph.json", "event-atlas.json", "events.mid"],
  );
  for (const artifact of bundle.receiverArtifacts) {
    assert.ok(allowed.has(extname(artifact.filename)));
  }
});

test("implementation identity binds the v3 source bundle", () => {
  const identity = buildImplementationIdentity();
  assert.deepEqual(
    identity.sourceFiles.map((entry) => entry.path),
    IMPLEMENTATION_SOURCE_PATHS,
  );
  assert.equal(identity.sourceFiles.length, 5);
  assert.match(identity.sourceBundleSha256, /^[0-9a-f]{64}$/);
  const contract = buildCanonicalContract();
  assert.deepEqual(contract.lineage.implementation, identity);
  assert.equal(
    contract.determinism.implementationSourceBundleSha256,
    identity.sourceBundleSha256,
  );
});

test("contract, receipt, manifest, and bundled schema form an acyclic identity chain", () => {
  const contract = buildCanonicalContract();
  const payload = structuredClone(contract);
  delete payload.$schema;
  delete payload.determinism.contractPayloadSha256;
  assert.equal(
    contract.determinism.contractPayloadSha256,
    canonicalObjectSha256(HASH_DOMAINS.contract, payload),
  );
  const bundle = buildReceiptAndManifest();
  assert.equal(bundle.receipt.receivers.length, 5);
  assert.equal(bundle.manifest.artifacts.length, 8);
  assert.equal(bundle.contract.$schema, BUNDLE_CONTRACT_SCHEMA_PATH);
  assert.equal(bundle.contractSchema.$id, BUNDLE_CONTRACT_SCHEMA_PATH);
  assert.equal(
    bundle.contractSchema.properties.$schema.const,
    BUNDLE_CONTRACT_SCHEMA_PATH,
  );
  assert.equal(
    bundle.contract.determinism.contractPayloadSha256,
    contract.determinism.contractPayloadSha256,
  );
  assert.deepEqual(bundle.receipt.implementation, contract.lineage.implementation);
  assert.deepEqual(
    bundle.manifest.lineage.implementation,
    contract.lineage.implementation,
  );
  assert.ok(!bundle.manifest.artifacts.some((artifact) => artifact.filename === "manifest.json"));
  assert.equal(
    bundle.receipt.eventCommitment.canonicalEventDocumentSha256,
    contract.determinism.eventDocumentSha256,
  );
});

test("the build command rejects unsafe or nonempty output paths without deleting them", () => {
  const packagePath = resolve(PROJECT_ROOT, "package.json");
  const packageBefore = existsSync(packagePath) ? readFileSync(packagePath) : null;
  const rootAttempt = spawnSync(
    process.execPath,
    ["scripts/build-v3-artifacts.mjs", "--output", "."],
    { cwd: PROJECT_ROOT, encoding: "utf8" },
  );
  assert.notEqual(rootAttempt.status, 0);
  if (packageBefore !== null) assert.deepEqual(readFileSync(packagePath), packageBefore);

  mkdirSync(resolve(PROJECT_ROOT, "dist"), { recursive: true });
  const nonempty = mkdtempSync(resolve(PROJECT_ROOT, "dist", "unsafe-"));
  const sentinel = resolve(nonempty, "sentinel.txt");
  writeFileSync(sentinel, "keep", "utf8");
  const nonemptyAttempt = spawnSync(
    process.execPath,
    ["scripts/build-v3-artifacts.mjs", "--output", nonempty],
    { cwd: PROJECT_ROOT, encoding: "utf8" },
  );
  assert.notEqual(nonemptyAttempt.status, 0);
  assert.equal(readFileSync(sentinel, "utf8"), "keep");
  rmSync(nonempty, { recursive: true, force: true });
});

test("the build command writes only allowed root artifact types", () => {
  mkdirSync(resolve(PROJECT_ROOT, "dist"), { recursive: true });
  const parent = mkdtempSync(resolve(PROJECT_ROOT, "dist", "build-parent-"));
  const output = resolve(parent, "bundle");
  const result = spawnSync(
    process.execPath,
    ["scripts/build-v3-artifacts.mjs", "--output", output],
    { cwd: PROJECT_ROOT, encoding: "utf8" },
  );
  assert.equal(result.status, 0, result.stderr || result.stdout);
  const filenames = readdirSync(output).sort();
  assert.deepEqual(filenames, [
    "contract.json",
    "contract.schema.json",
    "event-atlas.json",
    "events.csv",
    "events.json",
    "events.mid",
    "graph.json",
    "manifest.json",
    "observation-receipt.json",
  ]);
  const allowed = new Set(ALLOWED_ROOT_ARTIFACT_EXTENSIONS);
  assert.ok(filenames.every((filename) => allowed.has(extname(filename))));
  rmSync(parent, { recursive: true, force: true });
});
