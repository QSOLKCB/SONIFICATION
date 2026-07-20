// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this file,
// You can obtain one at https://mozilla.org/MPL/2.0/.
// SPDX-License-Identifier: MPL-2.0
// Copyright (c) 2026 Trent Slade / QSOL-IMC.

import {
  BASE_RELEASE,
  BASE_SITE_COUNT,
  EVENT_COUNT,
  EVENT_SCHEMA_ID,
  FIBRE_DIMENSION,
  FIBRE_PHASE_GAUSSIAN_EXPONENTS,
  GAUSSIAN_UNIT_SYMBOLS,
  LIFTED_GRAPH_SCHEMA_ID,
  MODEL_ID,
  MODEL_VERSION,
  PROFILE_ID,
  SITE_REGISTRY_SCHEMA_ID,
  buildCanonicalEvents,
  buildEventDocument,
  buildLiftedGraph,
  buildSiteRegistry,
  exactInvariantSummary,
} from "./etq-v3-core.mjs";
import {
  buildRootAdjacency,
  graphDegreePotential,
  selectEtq101Basis,
} from "./etq-model.mjs";
import {
  canonicalObjectSha256,
  canonicalSerialize,
  domainSeparatedSha256,
  sha256Bytes,
  utf8,
} from "./etq-v3-canonical.mjs";
import {
  EVENT_DOCUMENT_FILENAME,
  buildReceiverArtifacts,
} from "./etq-v3-receivers.mjs";

export {
  canonicalObjectSha256,
  canonicalSerialize,
  domainSeparatedSha256,
  sha256Bytes,
  utf8,
} from "./etq-v3-canonical.mjs";
export {
  EVENT_CSV_COLUMNS,
  EVENT_DOCUMENT_FILENAME,
  buildCsvReceiver,
  buildGraphmlReceiver,
  buildMidiReceiver,
  buildNdjsonReceiver,
  buildReceiverArtifacts,
  buildSvgReceiver,
} from "./etq-v3-receivers.mjs";

export const CONTRACT_SCHEMA_PATH = "../spec/etq-303.v3.schema.json";
export const CONTRACT_PATH = "examples/etq-303.v3.canonical.json";
export const RECEIPT_SCHEMA_ID = "qsol.etq-303.observation-receipt/v1";
export const MANIFEST_SCHEMA_ID = "qsol.etq-303.manifest/v1";

export const HASH_DOMAINS = Object.freeze({
  basis: "ETQ/V3/BASE-BASIS/v1",
  adjacency: "ETQ/V3/BASE-ADJACENCY/v1",
  degreePotential: "ETQ/V3/BASE-DEGREE-POTENTIAL/v1",
  siteRegistry: "ETQ/V3/SITE-REGISTRY/v1",
  liftedEdges: "ETQ/V3/LIFTED-EDGES/v1",
  events: "ETQ/V3/EVENTS/v1",
  eventDocument: "ETQ/V3/EVENT-DOCUMENT/v1",
  contract: "ETQ/V3/CONTRACT/v1",
  receipt: "ETQ/V3/RECEIPT/v1",
  manifest: "ETQ/V3/MANIFEST/v1",
  receiverPrefix: "ETQ/V3/RECEIVER/",
});

function contractPayload(value) {
  const payload = structuredClone(value);
  delete payload.$schema;
  delete payload.determinism.contractPayloadSha256;
  return payload;
}

export function buildCanonicalContract() {
  const basis = selectEtq101Basis();
  const adjacency = buildRootAdjacency(basis);
  const degreePotential = graphDegreePotential(adjacency);
  const siteRegistry = buildSiteRegistry();
  const liftedGraph = buildLiftedGraph();
  const events = buildCanonicalEvents();
  const eventDocument = buildEventDocument();
  const invariants = exactInvariantSummary();

  const contract = {
    $schema: CONTRACT_SCHEMA_PATH,
    modelId: MODEL_ID,
    modelVersion: MODEL_VERSION,
    profile: PROFILE_ID,
    releaseDate: "2026-07-20",
    lineage: {
      baseRelease: { ...BASE_RELEASE },
      provenanceMethodReferences: [
        {
          role: "foundational-receipt-bound-observation-protocol",
          doi: "10.5281/zenodo.21292906",
          version: "1.0",
        },
        {
          role: "forward-receipt-bound-observation-protocol",
          doi: "10.5281/zenodo.21293821",
          version: "1.2",
        },
      ],
      mathematicalDependencyOfMethodReferences: false,
    },
    exactMathematics: {
      ambientE8RootCount: 240,
      stateSpace: {
        expression: "H_303=H_101 tensor C^3",
        baseDimension: BASE_SITE_COUNT,
        fibreDimension: FIBRE_DIMENSION,
        totalDimension: EVENT_COUNT,
        distinctE8RootsClaimed: 101,
        distinctE8RootsNotClaimed: 303,
      },
      monomialStep: {
        expression: "F_303=R_101 tensor (X_3 exp(-i*pi*D_3/2))",
        supportAction: "(j,a)->(j+1 mod 101,a+1 mod 3)",
        sclStencil: [1, -2, 1],
        gaussianPhaseExponents: [...FIBRE_PHASE_GAUSSIAN_EXPONENTS],
        gaussianPhaseSymbols: [...GAUSSIAN_UNIT_SYMBOLS],
        gcd101And3: invariants.arithmetic.gcd101And3,
        supportCycleLength: EVENT_COUNT,
        exactOperatorOrder: EVENT_COUNT,
      },
      graphLift: {
        construction: "G_303=G_101 square C_3",
        vertices: liftedGraph.vertexCount,
        edges: liftedGraph.edgeCount,
        horizontalEdges: 3 * 1687,
        verticalEdges: 101 * 3,
        minimumDegree: invariants.graph.minimumDegree,
        maximumDegree: invariants.graph.maximumDegree,
        connected: invariants.graph.connected,
        eventTraversalIsGraphWalk: false,
      },
    },
    eventProtocol: {
      eventSchema: EVENT_SCHEMA_ID,
      siteRegistrySchema: SITE_REGISTRY_SCHEMA_ID,
      graphSchema: LIFTED_GRAPH_SCHEMA_ID,
      eventCount: EVENT_COUNT,
      sequenceIndexDomain: [0, EVENT_COUNT - 1],
      tensorIndexDomain: [0, EVENT_COUNT - 1],
      addressRule: "siteIndex=n mod 101; fibreLabel=n mod 3",
      inverseAddressRule:
        "n=siteIndex+101*((2*(fibreLabel-(siteIndex mod 3))) mod 3)",
      tensorIndexRule: "tensorIndex=3*siteIndex+fibreLabel",
      eventIdentityPrecedesReceivers: true,
    },
    receiverProfiles: {
      canonicalJson: "canonical-json-v1",
      csv: "csv-table-v1",
      ndjson: "ndjson-stream-v1",
      graphml: "cartesian-graphml-v1",
      svg: "svg-event-atlas-v1",
      midi: {
        id: "symbolic-midi-channel-v1",
        note: "preserved-ETQ-101-v2-symbolic-note",
        channel: "external-fibre-label-zero-based",
        eventDeltaTicks: 1,
        ticksPerQuarterNote: 1,
        noteVelocity: 64,
        tempoMetaEvent: null,
        absoluteFrequencyHz: null,
      },
      receiverMappingsAreMathematicalNecessities: false,
    },
    exclusions: [
      "303-distinct-e8-roots",
      "absolute-frequency",
      "waveform",
      "pcm-or-wav-rendering",
      "wall-clock-time",
      "ring-laplacian-substitution-for-selected-root-graph",
      "sorted-degree-multiset-as-vertex-labelled-potential",
      "eigensolver-output-as-canonical-identity",
      "event-traversal-as-selected-graph-walk",
      "physical-validation",
      "statistical-validation",
      "perceptual-validation",
    ],
    fixtures: {
      invariants,
      baseDegreeSum: degreePotential.degreeSum,
      baseDegreePotentialDenominator: degreePotential.normalizationDenominator,
      siteRegistryEntries: siteRegistry.sites.length,
      liftedGraphEdges: liftedGraph.edges.length,
      eventEntries: events.length,
    },
    determinism: {
      canonicalJson:
        "recursive-lexicographic-object-keys; arrays-preserve-order; safe-integers-only; UTF-8; no-BOM; no-trailing-newline",
      domainSeparatorEncoding: "UTF-8(domain)+NUL+payload-bytes",
      hashDomains: { ...HASH_DOMAINS },
      preservedV2BasisFixtureSha256: sha256Bytes(utf8(JSON.stringify(basis))),
      preservedV2AdjacencyFixtureSha256: sha256Bytes(
        utf8(JSON.stringify(adjacency)),
      ),
      preservedV2DegreePotentialNumeratorsFixtureSha256: sha256Bytes(
        utf8(JSON.stringify(degreePotential.numerators)),
      ),
      baseBasisDomainSha256: canonicalObjectSha256(HASH_DOMAINS.basis, basis),
      baseAdjacencyDomainSha256: canonicalObjectSha256(
        HASH_DOMAINS.adjacency,
        adjacency,
      ),
      baseDegreePotentialDomainSha256: canonicalObjectSha256(
        HASH_DOMAINS.degreePotential,
        degreePotential.numerators,
      ),
      siteRegistrySha256: canonicalObjectSha256(
        HASH_DOMAINS.siteRegistry,
        siteRegistry,
      ),
      liftedEdgesSha256: canonicalObjectSha256(
        HASH_DOMAINS.liftedEdges,
        liftedGraph.edges,
      ),
      eventsSha256: canonicalObjectSha256(HASH_DOMAINS.events, events),
      eventDocumentSha256: canonicalObjectSha256(
        HASH_DOMAINS.eventDocument,
        eventDocument,
      ),
      contractPayloadSha256: null,
    },
    claimBoundary:
      "ETQ-303 v3.0.0 is an exact finite 303-state tensor extension of the preserved ETQ-101 v2 selected-root basis, with a single 303-step support traversal, exact Gaussian-unit phase labels, and an exact Cartesian graph lift. It does not define 303 distinct E8 roots, sound, hertz, physical dynamics, empirical validation, or a privileged receiver.",
  };
  contract.determinism.contractPayloadSha256 = canonicalObjectSha256(
    HASH_DOMAINS.contract,
    contractPayload(contract),
  );
  return contract;
}

export function buildContractSchema(contract = buildCanonicalContract()) {
  const required = Object.keys(contract);
  const properties = {};
  for (const [key, value] of Object.entries(contract)) {
    properties[key] = { const: value };
  }
  return {
    $schema: "https://json-schema.org/draft/2020-12/schema",
    $id:
      "https://raw.githubusercontent.com/QSOLKCB/SONIFICATION/main/spec/etq-303.v3.schema.json",
    title: "ETQ-303 v3.0.0 exact canonical contract",
    type: "object",
    additionalProperties: false,
    required,
    properties,
  };
}

export function buildReceiptAndManifest() {
  const eventDocument = buildEventDocument();
  const contract = buildCanonicalContract();
  const contractBytes = utf8(canonicalSerialize(contract));
  const contractSchema = buildContractSchema(contract);
  const contractSchemaBytes = utf8(canonicalSerialize(contractSchema));
  const receiverArtifacts = buildReceiverArtifacts(eventDocument).map((artifact) => {
    const sha256 = sha256Bytes(artifact.bytes);
    const semanticSha256 = domainSeparatedSha256(
      `${HASH_DOMAINS.receiverPrefix}${artifact.receiverId}/v1`,
      artifact.bytes,
    );
    return { ...artifact, sha256, semanticSha256, byteLength: artifact.bytes.length };
  });

  const eventArtifact = receiverArtifacts.find(
    (artifact) => artifact.filename === EVENT_DOCUMENT_FILENAME,
  );
  const receiptCore = {
    schema: RECEIPT_SCHEMA_ID,
    modelId: MODEL_ID,
    modelVersion: MODEL_VERSION,
    profile: PROFILE_ID,
    eventCommitment: {
      filename: eventArtifact.filename,
      fileSha256: eventArtifact.sha256,
      semanticSha256: eventArtifact.semanticSha256,
      canonicalEventDocumentSha256:
        contract.determinism.eventDocumentSha256,
    },
    contract: {
      path: CONTRACT_PATH,
      fileSha256: sha256Bytes(contractBytes),
      contractPayloadSha256:
        contract.determinism.contractPayloadSha256,
    },
    receivers: receiverArtifacts.map((artifact) => ({
      receiverId: artifact.receiverId,
      filename: artifact.filename,
      mediaType: artifact.mediaType,
      semantics: artifact.semantics,
      byteLength: artifact.byteLength,
      sha256: artifact.sha256,
      semanticSha256: artifact.semanticSha256,
    })),
    claimBoundary: contract.claimBoundary,
  };
  const receiptCoreSha256 = canonicalObjectSha256(HASH_DOMAINS.receipt, receiptCore);
  const receipt = { ...receiptCore, receiptCoreSha256 };
  const receiptBytes = utf8(canonicalSerialize(receipt));

  const manifestArtifacts = [
    {
      filename: "contract.json",
      mediaType: "application/json",
      byteLength: contractBytes.length,
      sha256: sha256Bytes(contractBytes),
    },
    {
      filename: "contract.schema.json",
      mediaType: "application/schema+json",
      byteLength: contractSchemaBytes.length,
      sha256: sha256Bytes(contractSchemaBytes),
    },
    ...receiverArtifacts.map((artifact) => ({
      filename: artifact.filename,
      mediaType: artifact.mediaType,
      byteLength: artifact.byteLength,
      sha256: artifact.sha256,
    })),
    {
      filename: "observation-receipt.json",
      mediaType: "application/json",
      byteLength: receiptBytes.length,
      sha256: sha256Bytes(receiptBytes),
    },
  ].sort((left, right) => left.filename.localeCompare(right.filename));

  const manifestCore = {
    schema: MANIFEST_SCHEMA_ID,
    modelId: MODEL_ID,
    modelVersion: MODEL_VERSION,
    profile: PROFILE_ID,
    lineage: { ...BASE_RELEASE },
    generationRule:
      "contract-and-event-document-first; receiver-bytes-second; receipt-third; manifest-last",
    artifacts: manifestArtifacts,
    receiptCoreSha256,
    claimBoundary: contract.claimBoundary,
  };
  const manifestCoreSha256 = canonicalObjectSha256(
    HASH_DOMAINS.manifest,
    manifestCore,
  );
  const manifest = { ...manifestCore, manifestCoreSha256 };

  return {
    contract,
    contractBytes,
    contractSchema,
    contractSchemaBytes,
    eventDocument,
    receiverArtifacts,
    receipt,
    receiptBytes,
    manifest,
    manifestBytes: utf8(canonicalSerialize(manifest)),
  };
}
